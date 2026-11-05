"""Small public tournament pages; isolated SQLite cache, never an owner deck.

Network use is explicit and bounded. Downloaded pages and complete lists must
remain in the ignored PUBLIC workspace, not in fixtures or Git reports.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pokemind.database import utc_now
from pokemind.database import SCHEMA_VERSION, connect_readonly, connect_writable, initialize_schema
from pokemind.deck_exports import serialize_deck
from pokemind.decks import DeckCard, parse_deck_export
from pokemind.candidates import _identity as candidate_card_identity
from pokemind.public_campaign import campaign_plan, require_public_database
from pokemind.recovery import _ProcessLock, _atomic_bytes, _canonical, _redirected


USER_AGENT = "PokeMind/0.9 (manual bounded public tournament research)"
MAX_GETS = 100
MAX_BYTES = 64 * 1024 * 1024
MAX_RESPONSE = 2 * 1024 * 1024
INDEX_URL = "https://www.limitlesstcg.com/tournaments?format=standard&time=3months&type=all&zone=all"


def page_url(url: str) -> str:
    parsed = urlsplit(url)
    if url == INDEX_URL:
        return url
    if (parsed.scheme != "https" or parsed.netloc != "www.limitlesstcg.com"
            or parsed.query or parsed.fragment or not re.fullmatch(
                r"/(?:robots\.txt|about(?:/[a-z-]+)?|terms(?:-of-service)?|privacy|legal"
                r"|tournaments/[1-9][0-9]*(?:/(?:decklists|statistics|cards))?"
                r"|decks/list/[1-9][0-9]*|cards/[A-Z0-9]{1,12}/[A-Za-z0-9]{1,12})", parsed.path)):
        raise ValueError("COMPETITIVE_URL_NOT_ALLOWED")
    return url


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        fp.close()
        raise ValueError("COMPETITIVE_REDIRECT_STOP")


def create_workspace(root: Path, campaign: str) -> Path:
    campaign_plan(root, campaign, tcgdex_budget=1, meta_budget=0, official_budget=0)
    target = root / "data/local/public-campaigns" / ("lot-i-" + campaign)
    target.mkdir(parents=True, exist_ok=False)
    _atomic_bytes(target / "PUBLIC_ONLY.json", _canonical({
        "kind": "pokemind_public_only_lot_i", "campaign": campaign, "schema_version": 1,
    }), overwrite=False)
    (target / "pages").mkdir()
    require_public_database(root, target / "public.sqlite3")
    return target


class BoundedPages:
    """One persistent envelope; reserve URL before I/O, no retry after a crash.

    An interrupted reservation closes the run. Completed bodies can be reread
    offline. A denied/oversized/ambiguous response closes this provider.
    """
    def __init__(self, target: Path, *, opener=None, clock=time.monotonic, sleep=time.sleep):
        self.target = target.absolute()
        target = self.target
        require_public_database(target.parents[3], target / "public.sqlite3")
        self.path = target / "requests.json"
        for path in (self.path, target / "pages"):
            if _redirected(path) or (path.is_file() and path.stat().st_nlink != 1):
                raise ValueError("COMPETITIVE_WORKSPACE_ALIAS_BLOCKED")
        self.opener = opener if opener is not None else build_opener(NoRedirect())
        self.clock, self.sleep = clock, sleep
        self.last_request = None
        self.report = (json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists()
                       else {"schema_version": 1, "gets": 0, "bytes": 0,
                             "stopped": None, "requests": []})
        if any(item["state"] == "reserved" for item in self.report["requests"]):
            self.report["stopped"] = "INTERRUPTED_REQUEST_REQUIRES_REVIEW"
            self._save()

    def _save(self):
        _atomic_bytes(self.path, _canonical(self.report))

    def get(self, url: str) -> bytes:
        with _ProcessLock(self.target / ".competitive-network.lock"):
            if self.path.exists():
                self.report = json.loads(self.path.read_text(encoding="utf-8"))
            if any(item["state"] == "reserved" for item in self.report["requests"]):
                self.report["stopped"] = "INTERRUPTED_REQUEST_REQUIRES_REVIEW"
                self._save()
            return self._get(url)

    def _get(self, url: str) -> bytes:
        page_url(url)
        if self.report["stopped"]:
            raise ValueError("COMPETITIVE_PROVIDER_CLOSED")
        if any(item["url"] == url for item in self.report["requests"]):
            raise ValueError("COMPETITIVE_URL_ALREADY_ATTEMPTED")
        allowance = min(MAX_RESPONSE, MAX_BYTES - self.report["bytes"])
        if self.report["gets"] >= MAX_GETS or allowance <= 0:
            raise ValueError("COMPETITIVE_BUDGET_EXHAUSTED")
        if self.last_request is not None:
            self.sleep(max(0, 1 - (self.clock() - self.last_request)))
        else:
            self.sleep(1)  # also across separate manual invocations
        entry = {"url": url, "state": "reserved", "fetched_at": utc_now(), "bytes": 0}
        self.report["requests"].append(entry)
        self.report["gets"] += 1
        self._save()
        self.last_request = self.clock()
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"})
        try:
            with self.opener.open(request, timeout=20) as response:
                status = response.status
                entry["http_status"] = status
                if status != 200:
                    raise ValueError("COMPETITIVE_HTTP_STOP")
                if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                    raise ValueError("COMPETITIVE_ENCODING_STOP")
                length = response.headers.get("Content-Length")
                if length and (not length.isdigit() or int(length) > allowance):
                    raise ValueError("COMPETITIVE_RESPONSE_CAP_STOP")
                body = response.read(allowance)
                entry["bytes"] = len(body)
                self.report["bytes"] += len(body)
                if len(body) >= allowance or (length and len(body) != int(length)):
                    raise ValueError("COMPETITIVE_RESPONSE_CAP_OR_INCOMPLETE_STOP")
                lowered = body.lower()
                if (response.headers.get("cf-mitigated") == "challenge" or any(token in lowered for token in (
                        b"/cdn-cgi/challenge-platform/", b"verify you are human", b"<title>access denied",
                        b"<title>just a moment", b"captcha", b"automated access is prohibited"))):
                    raise ValueError("COMPETITIVE_ACCESS_CHALLENGE_STOP")
                digest = hashlib.sha256(body).hexdigest()
                destination = self.target / "pages" / (digest + ".body")
                if _redirected(destination) or (destination.exists() and (
                        not destination.is_file() or destination.stat().st_nlink != 1)):
                    raise ValueError("COMPETITIVE_PAGE_ALIAS_BLOCKED")
                if destination.exists():
                    if destination.read_bytes() != body:
                        raise ValueError("COMPETITIVE_CACHE_DIGEST_MISMATCH")
                else:
                    _atomic_bytes(destination, body, overwrite=False)
                entry.update(state="complete", sha256=digest,
                             content_type=response.headers.get("Content-Type", "unknown"))
                self._save()
                return body
        except (ValueError, OSError, URLError) as exc:
            code = str(exc) if isinstance(exc, ValueError) else "COMPETITIVE_NETWORK_STOP"
            if isinstance(exc, HTTPError):
                entry["http_status"] = exc.code
                exc.close()
            entry["state"] = "stopped"
            self.report["stopped"] = code
            self._save()
            raise ValueError(code) from exc

    def close(self):
        with _ProcessLock(self.target / ".competitive-network.lock"):
            if self.path.exists():
                self.report = json.loads(self.path.read_text(encoding="utf-8"))
            if self.report["stopped"] is None:
                self.report["stopped"] = "COMPLETED_BATCH_NO_RESTART"
            self._save()

    def cached(self, url: str) -> bytes:
        matches = [r for r in self.report["requests"] if r["url"] == url and r["state"] == "complete"]
        if len(matches) != 1:
            raise ValueError("COMPETITIVE_PAGE_NOT_CACHED")
        return cached_page(self.target, matches[0])


def cached_page(target: Path, entry: dict) -> bytes:
    """Pure read shared with the advisor; no BoundedPages/client construction."""
    if not re.fullmatch(r"[0-9a-f]{64}", entry.get("sha256", "")):
        raise ValueError("COMPETITIVE_CACHE_DIGEST_INVALID")
    source = target / "pages" / (entry["sha256"] + ".body")
    if (any(_redirected(path) for path in (source, *source.absolute().parents))
            or not source.is_file() or source.stat().st_nlink != 1
            or source.stat().st_size > MAX_RESPONSE):
        raise ValueError("COMPETITIVE_CACHE_FILE_UNSAFE")
    body = source.read_bytes()
    if hashlib.sha256(body).hexdigest() != entry["sha256"]:
        raise ValueError("COMPETITIVE_CACHE_DIGEST_MISMATCH")
    return body


@dataclass
class Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)

    def text(self):
        return " ".join(" ".join(x.text() if isinstance(x, Node) else x
                                 for x in self.children).split())

    def find(self, *, tag=None, cls=None, attr=None):
        found = []
        for child in self.children:
            if isinstance(child, Node):
                if ((tag is None or child.tag == tag)
                        and (cls is None or cls in child.attrs.get("class", "").split())
                        and (attr is None or attr in child.attrs)):
                    found.append(child)
                found.extend(child.find(tag=tag, cls=cls, attr=attr))
        return found


class PageTree(HTMLParser):
    def __init__(self, body: bytes):
        super().__init__(convert_charrefs=True)
        if len(body) > MAX_RESPONSE:
            raise ValueError("COMPETITIVE_PARSE_BODY_CAP")
        self.root = Node("root")
        self.stack = [self.root]
        self.nodes = 0
        self.feed(body.decode("utf-8"))
        self.close()

    def handle_starttag(self, tag, attrs):
        self.nodes += 1
        if self.nodes > 100_000 or len(self.stack) > 100:
            raise ValueError("COMPETITIVE_PARSE_STRUCTURE_CAP")
        child = Node(tag, dict(attrs))
        self.stack[-1].children.append(child)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(child)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def one(nodes):
    if len(nodes) != 1:
        raise ValueError("COMPETITIVE_PAGE_STRUCTURE_CHANGED")
    return nodes[0]


def parse_event(body: bytes, url: str, *, as_of: str) -> dict:
    page_url(url)
    if not re.fullmatch(r"https://www.limitlesstcg.com/tournaments/[1-9][0-9]*", url):
        raise ValueError("COMPETITIVE_EVENT_URL_REQUIRED")
    tree = PageTree(body).root
    name = one(tree.find(cls="infobox-heading")).text()
    line = one(tree.find(cls="infobox-line")).text()
    match = re.search(r"(\d{1,2})(?:st|nd|rd|th) (\w+) (\d{4})\s*•\s*(\d+) Players", line)
    if not match:
        raise ValueError("COMPETITIVE_EVENT_DATE_OR_SIZE_MISSING")
    day, month, year, players = match.groups()
    months = ("January February March April May June July August September October November December").split()
    when = date(int(year), months.index(month) + 1, int(day))
    if when > date.fromisoformat(as_of):
        raise ValueError("COMPETITIVE_FUTURE_EVENT")
    format_links = [a for a in tree.find(tag="a") if a.attrs.get("href", "").startswith("/decks/?time=all&format=")]
    format_range = one(format_links).text()
    placements = []
    seen = set()
    for row in tree.find(tag="tr", attr="data-rank"):
        rank = int(row.attrs["data-rank"])
        if rank < 1 or rank in seen or rank > int(players):
            raise ValueError("COMPETITIVE_PLACEMENT_CONFLICT")
        seen.add(rank)
        links = [a.attrs["href"] for a in row.find(tag="a")
                 if re.fullmatch(r"/decks/list/[1-9][0-9]*", a.attrs.get("href", ""))]
        if len(links) > 1:
            raise ValueError("COMPETITIVE_LIST_LINK_CONFLICT")
        if links:
            archetype = row.attrs.get("data-deck", "").strip()
            if not archetype or len(archetype) > 120:
                raise ValueError("COMPETITIVE_ARCHETYPE_MISSING")
            placements.append({"placement": rank, "archetype": archetype,
                               "list_url": page_url("https://www.limitlesstcg.com" + links[0])})
    if not placements:
        raise ValueError("COMPETITIVE_PUBLISHED_LISTS_MISSING")
    return {"event_id": url.rsplit("/", 1)[1], "name": name, "date": when.isoformat(),
            "participant_count": int(players), "source_url": url,
            "source_sha256": hashlib.sha256(body).hexdigest(),
            "format_range": format_range, "format": "unknown", "platform": "in_person",
            "match_mode": "unknown", "placements": sorted(placements, key=lambda r: r["placement"]),
            "published_list_placements": len(placements), "published_result_rows": len(seen)}


def qualify_standard(event: dict, index_body: bytes) -> dict:
    """Match the public index row, not an assumed legality from card names."""
    tree = PageTree(index_body).root
    rows = [row for row in tree.find(tag="tr") if any(
        a.attrs.get("href") == "/tournaments/" + event["event_id"] for a in row.find(tag="a"))]
    row = one(rows)
    cells = row.find(tag="td")
    if (not any(image.attrs.get("alt") == "standard" for image in row.find(tag="img"))
            or len(cells) != 6 or cells[2].text() != event["name"]
            or cells[4].text() != str(event["participant_count"])):
        raise ValueError("COMPETITIVE_STANDARD_INDEX_MISMATCH")
    expected = date.fromisoformat(event["date"]).strftime("%d %b %y")
    if cells[0].text() != expected:
        raise ValueError("COMPETITIVE_STANDARD_INDEX_DATE_MISMATCH")
    return {**event, "format": "standard", "format_source_url": INDEX_URL,
            "format_source_sha256": hashlib.sha256(index_body).hexdigest(),
            "legality": "source_declared_event_format_not_individual_live_verification"}


def parse_list(body: bytes) -> str:
    tree = PageTree(body).root
    text_list = one(tree.find(attr="data-text-decklist"))
    cards = []
    sections = {"Pokémon": "pokemon", "Trainer": "trainer", "Energy": "energy"}
    headings = []
    for column in text_list.find(cls="decklist-column"):
        heading = one(column.find(cls="decklist-column-heading")).text()
        match = re.fullmatch(r"(Pokémon|Trainer|Energy) \((\d+)\)", heading)
        if not match:
            raise ValueError("COMPETITIVE_SECTION_UNKNOWN")
        section, total = match.groups()
        if section in headings:
            raise ValueError("COMPETITIVE_SECTION_DUPLICATE")
        headings.append(section)
        subtotal = 0
        for node in column.find(cls="decklist-card"):
            quantity = int(one(node.find(cls="card-count")).text())
            name = one(node.find(cls="card-name")).text()
            if node.attrs.get("data-lang") != "en":
                raise ValueError("COMPETITIVE_LIST_LANGUAGE_UNKNOWN")
            set_code, number = node.attrs.get("data-set"), node.attrs.get("data-number")
            if not set_code or not number:
                raise ValueError("COMPETITIVE_PRINTING_MISSING")
            ordinal = len(cards) + 1
            cards.append(DeckCard(ordinal=ordinal, source_line=ordinal, card_type=sections[section],
                                  quantity=quantity, name=name, set_code=set_code,
                                  collector_number=number, normalized_line=f"{quantity} {name} {set_code} {number}"))
            subtotal += quantity
        if subtotal != int(total):
            raise ValueError("COMPETITIVE_SECTION_TOTAL_MISMATCH")
    if set(headings) != set(sections):
        raise ValueError("COMPETITIVE_SECTION_MISSING")
    return serialize_deck(cards)


def parse_statistics(body: bytes) -> dict:
    tree = PageTree(body).root
    rows = []
    for row in tree.find(tag="tr", attr="data-count"):
        count = int(row.attrs["data-count"])
        cells = row.find(tag="td")
        if len(cells) != 6 or not cells[2].text() or count < 1:
            raise ValueError("COMPETITIVE_STATISTICS_STRUCTURE_CHANGED")
        rows.append({"archetype_family": cells[2].text(), "count": count})
    if not rows:
        raise ValueError("COMPETITIVE_STATISTICS_MISSING")
    return {"rows": rows, "denominator": sum(row["count"] for row in rows),
            "scope": "published_result_subset_not_all_entrants", "match_winrates": None,
            "source_sha256": hashlib.sha256(body).hexdigest()}


def initialize_competitive(connection):
    # Additional PUBLIC meta tables; no change to the owner schema version.
    connection.execute("""CREATE TABLE IF NOT EXISTS meta_competitive_events (
        event_id TEXT PRIMARY KEY, metadata_json TEXT NOT NULL)""")
    connection.execute("""CREATE TABLE IF NOT EXISTS meta_competitive_lists (
        event_id TEXT NOT NULL REFERENCES meta_competitive_events(event_id),
        placement INTEGER NOT NULL, archetype TEXT NOT NULL, list_url TEXT NOT NULL,
        page_sha256 TEXT NOT NULL, fetched_at TEXT NOT NULL, deck_text TEXT NOT NULL,
        PRIMARY KEY(event_id, placement))""")


def store_event(root: Path, db: Path, event: dict, lists: list[dict]) -> dict:
    require_public_database(root, db)
    if event.get("format") != "standard" or event.get("platform") != "in_person":
        raise ValueError("COMPETITIVE_STANDARD_QUALIFICATION_REQUIRED")
    expected = {p["placement"]: p for p in event["placements"]}
    seen = set()
    for item in lists:
        rank = item["placement"]
        if (rank in seen or rank not in expected
                or any(item[k] != expected[rank][k] for k in ("archetype", "list_url"))):
            raise ValueError("COMPETITIVE_LIST_PLACEMENT_MISMATCH")
        seen.add(rank)
        page_url(item["list_url"])
        if not re.fullmatch(r"[0-9a-f]{64}", item["page_sha256"]):
            raise ValueError("COMPETITIVE_LIST_PROVENANCE_MISSING")
        if serialize_deck(parse_deck_export(item["deck_text"]).cards) != item["deck_text"]:
            raise ValueError("COMPETITIVE_LIST_NOT_CANONICAL")
    creating = not db.exists()
    connection = connect_writable(db)
    try:
        if creating:
            initialize_schema(connection)
        elif connection.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
            raise ValueError("COMPETITIVE_CACHE_SCHEMA_UNSUPPORTED_NO_MIGRATION")
        with connection:
            initialize_competitive(connection)
            metadata = {k: v for k, v in event.items() if k != "placements"}
            metadata["sampled_lists"] = len(lists)
            encoded = json.dumps(metadata, sort_keys=True)
            existing = connection.execute("SELECT metadata_json FROM meta_competitive_events WHERE event_id=?", (event["event_id"],)).fetchone()
            if existing and existing[0] != encoded:
                raise ValueError("COMPETITIVE_EXISTING_EVENT_CONFLICT")
            connection.execute("INSERT OR IGNORE INTO meta_competitive_events VALUES (?,?)", (event["event_id"], encoded))
            for item in lists:
                values = (event["event_id"], item["placement"], item["archetype"], item["list_url"],
                          item["page_sha256"], item["fetched_at"], item["deck_text"])
                previous = connection.execute("SELECT * FROM meta_competitive_lists WHERE event_id=? AND placement=?", values[:2]).fetchone()
                if previous and tuple(previous) != values:
                    raise ValueError("COMPETITIVE_EXISTING_LIST_CONFLICT")
                connection.execute("INSERT OR IGNORE INTO meta_competitive_lists VALUES (?,?,?,?,?,?,?)", values)
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign = len(connection.execute("PRAGMA foreign_key_check").fetchall())
        return {"event_id": event["event_id"], "lists": len(lists), "integrity": integrity, "foreign_key_errors": foreign}
    finally:
        connection.close()


def competitive_summary(root: Path, db: Path) -> dict:
    require_public_database(root, db)
    connection = connect_readonly(db)
    try:
        events = [json.loads(r[0]) for r in connection.execute("SELECT metadata_json FROM meta_competitive_events ORDER BY event_id")]
        counts = [dict(r) for r in connection.execute("SELECT archetype, COUNT(*) AS n FROM meta_competitive_lists GROUP BY archetype ORDER BY n DESC, archetype")]
        return {"events": events, "sampled_lists": sum(row["n"] for row in counts),
                "archetypes": counts, "scope": "selected_published_placements",
                "match_winrates": None, "live_legality": "unknown", "collection": "unknown",
                "network_used": False, "owner_database_opened": False}
    finally:
        connection.close()


def competitive_export(root: Path, db: Path, event_id: str, placement: int) -> str:
    require_public_database(root, db)
    connection = connect_readonly(db)
    try:
        row = connection.execute("SELECT deck_text FROM meta_competitive_lists WHERE event_id=? AND placement=?", (event_id, placement)).fetchone()
        if row is None:
            raise ValueError("COMPETITIVE_LIST_NOT_FOUND")
        return serialize_deck(parse_deck_export(row[0]).cards)
    finally:
        connection.close()


ADVISOR_UNKNOWNS = (
    "matchup", "winrate", "BO1/BO3", "TCG_Live_legality_and_availability",
    "collection", "credits", "printing_equivalence", "current_format_compatibility",
)


def _advisor_context(as_of: str) -> dict:
    if not isinstance(as_of, str) or date.fromisoformat(as_of).isoformat() != as_of:
        raise ValueError("COMPETITIVE_ADVISOR_DATE_REQUIRED")
    return {"as_of": as_of, "network_used": False, "owner_database_opened": False,
            "database_mutated": False, "scope": "offline_public_selected_placements",
            "selection_bias": "published_top_placements_not_random_players_or_matches",
            "unknowns": list(ADVISOR_UNKNOWNS), "strength_ranking": None}


def _card_map(text: str) -> dict:
    # Same exact-printing identity policy as owner-controlled candidates, but
    # this function receives public text only and never invokes candidate I/O.
    parsed = parse_deck_export(text)
    serialize_deck(parsed.cards)  # all sections, safe names, printing/duplicates
    result = {}
    for card in parsed.cards:
        if not card.set_code or not card.collector_number:
            raise ValueError("COMPETITIVE_ADVISOR_PRINTING_REQUIRED")
        identity = candidate_card_identity({"card_name": card.name, "set_code": card.set_code,
                                            "collector_number": card.collector_number})
        if identity in result:
            raise ValueError("COMPETITIVE_ADVISOR_AMBIGUOUS_CARD_IDENTITY")
        result[identity] = {"type": card.card_type, "name": card.name,
                            "set": card.set_code, "number": card.collector_number,
                            "quantity": card.quantity}
    return result


def _composition_id(cards: dict) -> str:
    payload = [[*key, cards[key]["type"], cards[key]["quantity"]] for key in sorted(cards)]
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _family(label: str) -> str:
    return "Dragapult" if label.casefold().startswith("dragapult") else label


# One battle analysis asked for the same verified sample about twenty times per counter-deck plan, re-reading
# and re-parsing every cached list page each time (owner diagnostic, 2026-11-03: about 13 s per plan).
_SNAPSHOTS: dict = {}
_SNAPSHOT_LOCK = threading.Lock()
SNAPSHOT_SECONDS = 900


def _snapshot_key(db: Path, as_of: str):
    """Every file the sample is verified from, by size and modification time; any change recomputes it.

    Only the database, the ledger and the pages the ledger names are looked at: no folder is listed.
    """
    try:
        db = Path(db).absolute()
        target = db.parent
        ledger = target / "requests.json"
        if any(_redirected(path) for path in (db, target, target / "pages", ledger)):
            return None
        stamps = [(path.name, path.stat().st_mtime_ns, path.stat().st_size) for path in (db, ledger)]
        if stamps[1][2] > MAX_RESPONSE:
            return None
        for record in json.loads(ledger.read_text(encoding="utf-8"))["requests"]:
            digest = record.get("sha256", "")
            page = target / "pages" / (digest + ".body")
            if re.fullmatch(r"[0-9a-f]{64}", digest) and page.is_file():
                stamps.append((digest, page.stat().st_mtime_ns, page.stat().st_size))
            else:
                stamps.append((str(digest), None, None))
        return os.path.normcase(str(db)), as_of, tuple(stamps)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None


def _advisor_snapshot(root: Path, db: Path, as_of: str):
    """The verified public sample; reused while none of its files changed (a private copy on every call)."""
    _advisor_context(as_of)
    require_public_database(root, db)  # lexical namespace before any owner fallback
    key = _snapshot_key(db, as_of)
    if key is not None:
        with _SNAPSHOT_LOCK:
            hit = _SNAPSHOTS.get(key)
        if hit and time.monotonic() - hit[0] < SNAPSHOT_SECONDS:
            return copy.deepcopy(hit[1])
    value = _advisor_snapshot_uncached(root, db, as_of)
    if key is not None and key == _snapshot_key(db, as_of):  # unchanged while it was read
        with _SNAPSHOT_LOCK:
            if len(_SNAPSHOTS) >= 4:
                _SNAPSHOTS.clear()
            _SNAPSHOTS[key] = (time.monotonic(), copy.deepcopy(value))
    return value


def _advisor_snapshot_uncached(root: Path, db: Path, as_of: str):
    _advisor_context(as_of)
    require_public_database(root, db)  # lexical namespace before any owner fallback
    if not db.is_file():
        raise ValueError("COMPETITIVE_ADVISOR_PUBLIC_CACHE_MISSING")
    target = db.parent
    ledger_path = target / "requests.json"
    if (not ledger_path.is_file() or _redirected(ledger_path)
            or ledger_path.stat().st_nlink != 1 or ledger_path.stat().st_size > MAX_RESPONSE):
        raise ValueError("COMPETITIVE_ADVISOR_SOURCE_CACHE_MISSING_OR_UNSAFE")
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        records = ledger["requests"]
        if not isinstance(records, list) or len(records) > MAX_GETS:
            raise ValueError
        by_url = {}
        for record in records:
            by_url.setdefault(page_url(record["url"]), []).append(record)
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError("COMPETITIVE_ADVISOR_SOURCE_LEDGER_INVALID") from exc
    bodies = {}

    def source(url):
        if url in bodies:
            return bodies[url]
        matches = by_url.get(url, [])
        if len(matches) != 1 or matches[0].get("state") != "complete" or matches[0].get("http_status") != 200:
            raise ValueError("COMPETITIVE_ADVISOR_SOURCE_MISSING_OR_AMBIGUOUS")
        bodies[url] = (cached_page(target, matches[0]), matches[0])
        return bodies[url]

    connection = connect_readonly(db)
    try:
        names = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"meta_competitive_events", "meta_competitive_lists"}.issubset(names):
            raise ValueError("COMPETITIVE_ADVISOR_TABLES_MISSING_NO_MIGRATION")
        expected_columns = {
            "meta_competitive_events": {"event_id", "metadata_json"},
            "meta_competitive_lists": {"event_id", "placement", "archetype", "list_url",
                                       "page_sha256", "fetched_at", "deck_text"},
        }
        for table, required in expected_columns.items():
            columns = {r[1] for r in connection.execute(f"PRAGMA table_info({table})")}
            if not required.issubset(columns):
                raise ValueError("COMPETITIVE_ADVISOR_SCHEMA_INCOMPLETE_NO_MIGRATION")
        raw_events = connection.execute("SELECT event_id,metadata_json FROM meta_competitive_events LIMIT 4").fetchall()
        rows = connection.execute("SELECT * FROM meta_competitive_lists ORDER BY event_id,placement LIMIT 501").fetchall()
        if len(raw_events) > 3 or len(rows) > 500:
            raise ValueError("COMPETITIVE_ADVISOR_SAMPLE_CAP")
    finally:
        connection.close()
    if not rows:
        raise ValueError("COMPETITIVE_ADVISOR_EMPTY_PUBLIC_SAMPLE")
    events, issues, groups, verified_events = {}, [], {}, {}
    for raw_event in raw_events:
        event_id = raw_event["event_id"]
        try:
            metadata = json.loads(raw_event["metadata_json"])
            url = "https://www.limitlesstcg.com/tournaments/" + event_id
            body, _ = source(url)
            index, _ = source(INDEX_URL)
            verified = qualify_standard(parse_event(body, url, as_of=as_of), index)
            fields = ("event_id", "name", "date", "participant_count", "format", "platform",
                      "format_range", "source_url", "source_sha256", "format_source_sha256")
            if any(metadata.get(k) != verified[k] for k in fields):
                raise ValueError("COMPETITIVE_ADVISOR_EVENT_SOURCE_CONFLICT")
            events[event_id] = {k: verified[k] for k in (
                "event_id", "name", "date", "participant_count", "format", "platform", "source_url")}
            events[event_id]["sample_scope"] = "published_selected_placements"
            verified_events[event_id] = verified
        except (OSError, ValueError, KeyError, TypeError, IndexError):
            issues.append({"event_id": event_id, "code": "EVENT_SOURCE_INVALID_OR_FUTURE"})
    for row in rows:
        selector = f"{row['event_id']}:{row['placement']}"
        try:
            event = verified_events[row["event_id"]]
            placement = next(p for p in event["placements"] if p["placement"] == row["placement"])
            if any(row[k] != placement[k] for k in ("list_url", "archetype")):
                raise ValueError("COMPETITIVE_ADVISOR_PLACEMENT_SOURCE_CONFLICT")
            body, record = source(row["list_url"])
            if row["page_sha256"] != record["sha256"] or row["fetched_at"] != record["fetched_at"]:
                raise ValueError("COMPETITIVE_ADVISOR_PAGE_PROVENANCE_CONFLICT")
            cards = _card_map(row["deck_text"])
            if _composition_id(cards) != _composition_id(_card_map(parse_list(body))):
                raise ValueError("COMPETITIVE_ADVISOR_LIST_SOURCE_CONFLICT")
            digest = _composition_id(cards)
            group = groups.setdefault(digest, {"composition_id": digest, "cards": cards,
                                                "occurrences": [], "card_source": source})
            group["occurrences"].append({"selector": selector, "event_id": row["event_id"],
                "placement": row["placement"], "date": event["date"], "archetype": row["archetype"],
                "list_url": row["list_url"], "fetched_at": row["fetched_at"]})
        except (OSError, ValueError, KeyError, TypeError, StopIteration):
            issues.append({"selector": selector, "code": "LIST_60_PRINTING_OR_SOURCE_INVALID"})
    # Different sourced names/types for one set+number are not silently merged.
    printings = {}
    for digest, group in groups.items():
        for key, card in group["cards"].items():
            printings.setdefault(key[1:], set()).add((key[0], card["type"]))
    for group in groups.values():
        group["quality"] = []
        if any(len(printings[key[1:]]) > 1 for key in group["cards"]):
            group["quality"].append("AMBIGUOUS_PRINTING_NAME_OR_TYPE")
        families = {_family(row["archetype"]) for row in group["occurrences"]}
        if len(families) > 1:
            group["quality"].append("ARCHETYPE_FAMILY_DISAGREEMENT")
        for code in group["quality"]:
            issues.append({"composition_id": group["composition_id"], "code": code})
    return groups, events, issues, len(rows)


def _build_facts(group: dict) -> dict:
    cards = list(group["cards"].values())
    counts = {kind: sum(card["quantity"] for card in cards if card["type"] == kind)
              for kind in ("pokemon", "trainer", "energy")}
    stages = []
    for card in cards:
        if card["type"] != "pokemon":
            continue
        url = f"https://www.limitlesstcg.com/cards/{card['set']}/{card['number']}"
        try:
            body, _ = group["card_source"](url)
            tree = PageTree(body).root
            if one(tree.find(cls="card-text-name")).text().casefold() != card["name"].casefold():
                continue
            text = one(tree.find(cls="card-text-type")).text()
            match = re.search(r"(?:^| - )(Basic|Stage [12])(?: - |$)", text)
            if match:
                stages.append({"name": card["name"], "stage": match[1], "source_url": url})
        except (OSError, ValueError, KeyError, TypeError):
            pass  # optional card text; never request missing sources
    return {"total_cards": sum(counts.values()), "section_copies": counts,
            "energy_cards": [{"name": card["name"], "quantity": card["quantity"]}
                             for card in cards if card["type"] == "energy"],
            "stages_from_cached_text": stages,
            "unverified_stages": "unknown;absence_of_cached_text_is_not_basic",
            "support_roles_and_prize_exchange": "conditional_not_measured"}


def _group_public(group: dict, *, detail=False) -> dict:
    rows = group["occurrences"]
    result = {"composition_id": group["composition_id"], "reference": rows[0]["selector"],
              "archetypes": sorted({row["archetype"] for row in rows}),
              "placements": len(rows), "placement_range": [min(r["placement"] for r in rows), max(r["placement"] for r in rows)],
              "events": sorted({r["event_id"] for r in rows}),
              "date_range": [min(r["date"] for r in rows), max(r["date"] for r in rows)],
              "source_urls": sorted({r["list_url"] for r in rows}),
              "quality": group["quality"] or ["cached_event_and_list_rechecked_60_printing_exact"]}
    if detail:
        result.update(occurrences=rows, build_facts=_build_facts(group))
    return result


def competitive_inventory(root: Path, db: Path, *, as_of: str) -> dict:
    groups, events, issues, total = _advisor_snapshot(root, db, as_of)
    compositions = [_group_public(group) for _, group in sorted(groups.items())]
    archetypes = sorted({label for group in compositions for label in group["archetypes"]})
    return {**_advisor_context(as_of), "status": "PARTIAL_WITH_EVIDENCE" if issues or any(g["quality"] for g in groups.values()) else "OK",
            "sampled_placements": total, "valid_placements": sum(g["placements"] for g in compositions),
            "distinct_compositions": len(groups), "archetype_labels": archetypes,
            "events": list(events.values()), "compositions": compositions, "issues": issues,
            "identity_policy": "normalized_name+set+number+type+quantity;no_reprint_equivalence_inferred"}


def _select_group(groups: dict, selector: str) -> dict:
    if not re.fullmatch(r"[1-9][0-9]*:[1-9][0-9]*", selector):
        raise ValueError("COMPETITIVE_ADVISOR_SELECTOR_EVENT_COLON_PLACEMENT_REQUIRED")
    matches = [group for group in groups.values() if any(r["selector"] == selector for r in group["occurrences"])]
    if len(matches) != 1 or "AMBIGUOUS_PRINTING_NAME_OR_TYPE" in matches[0]["quality"]:
        raise ValueError("COMPETITIVE_ADVISOR_LIST_MISSING_INVALID_OR_AMBIGUOUS")
    return matches[0]


def _quantitative_diff(left: dict, right: dict, limit: int) -> dict:
    if type(limit) is not int or not 1 <= limit <= 60:
        raise ValueError("COMPETITIVE_ADVISOR_DIFF_LIMIT_1_TO_60")
    shared, removed, added = [], [], []
    for key in sorted(left["cards"].keys() | right["cards"].keys()):
        a, b = left["cards"].get(key), right["cards"].get(key)
        if a and b and a["type"] != b["type"]:
            raise ValueError("COMPETITIVE_ADVISOR_PRINTING_TYPE_CONFLICT")
        before, after = a["quantity"] if a else 0, b["quantity"] if b else 0
        identity = {k: (b or a)[k] for k in ("type", "name", "set", "number")}
        common = min(before, after)
        if common:
            shared.append({**identity, "quantity": common})
        if before > after:
            removed.append({**identity, "quantity": before - after})
        if after > before:
            added.append({**identity, "quantity": after - before})
    totals = {name: sum(card["quantity"] for card in values)
              for name, values in (("shared", shared), ("removed", removed), ("added", added))}
    assert totals["shared"] + totals["removed"] == totals["shared"] + totals["added"] == 60
    return {"counts": totals, "shared": shared[:limit], "removed": removed[:limit], "added": added[:limit],
            "omitted_identities": {name: max(0, len(values) - limit) for name, values in (
                ("shared", shared), ("removed", removed), ("added", added))},
            "identity_policy": "exact_printing_with_normalized_name;reprint_or_language_equivalence_unknown"}


def competitive_compare(root: Path, db: Path, left: str, right: str, *, as_of: str, limit=12) -> dict:
    groups, events, issues, _ = _advisor_snapshot(root, db, as_of)
    a, b = _select_group(groups, left), _select_group(groups, right)
    return {**_advisor_context(as_of), "status": "PARTIAL_WITH_EVIDENCE" if issues else "OK",
            "requested_selectors": {"left": left, "right": right},
            "left": _group_public(a, detail=True), "right": _group_public(b, detail=True),
            "same_composition": a["composition_id"] == b["composition_id"],
            "changes": _quantitative_diff(a, b, limit), "issues": issues,
            "interpretation": "construction_difference_only;card_overlap_is_not_matchup_strength"}


def competitive_shortlist(root: Path, db: Path, *, as_of: str, options=4, base=None) -> dict:
    if type(options) is not int or not 2 <= options <= 4:
        raise ValueError("COMPETITIVE_ADVISOR_OPTIONS_2_TO_4")
    groups, events, issues, _ = _advisor_snapshot(root, db, as_of)
    eligible = [g for g in groups.values() if not g["quality"]]

    def family(group):
        return _family(group["occurrences"][0]["archetype"])

    def representative(candidates):
        # A medoid on *distinct compositions*, not placement counts or strength.
        # Ties use the composition ID, never a tournament rank.
        def distance(group):
            return sum(_quantitative_diff(group, other, 1)["counts"]["removed"] for other in candidates)
        return min(candidates, key=lambda group: (distance(group), group["composition_id"]))

    dragapult = [g for g in eligible if family(g) == "Dragapult"]
    if base:
        reference = _select_group(groups, base)
        if reference not in eligible or family(reference) != "Dragapult":
            raise ValueError("COMPETITIVE_ADVISOR_VALID_DRAGAPULT_BASE_REQUIRED")
    elif dragapult:
        reference = representative(dragapult)
    else:
        raise ValueError("COMPETITIVE_ADVISOR_DRAGAPULT_BASE_MISSING")
    selected = [reference]
    families = ["Basic Box", "Hydrapple", "Dhelmise"]
    families += sorted({family(g) for g in eligible} - {"Dragapult", *families})
    for label in families:
        candidates = [g for g in eligible if family(g) == label and g not in selected]
        if candidates:
            selected.append(representative(candidates))
        if len(selected) == options:
            break
    if len(selected) < 2:
        raise ValueError("COMPETITIVE_ADVISOR_DISTINCT_ALTERNATIVE_MISSING")
    hypotheses = {
        "Dragapult": "Hypothèse : tester la mise en place des évolutions,les couleurs d'Énergie et la répartition des marqueurs;aucun avantage de matchup mesuré.",
        "Basic Box": "Hypothèse : tester la flexibilité d'attaquants de base,la gestion des couleurs et l'exposition des soutiens;échange des Récompenses à vérifier.",
        "Hydrapple": "Hypothèse : tester l'accélération Plante et l'installation des évolutions avant les gros K.O.;stabilité et échange des Récompenses inconnus.",
        "Dhelmise": "Hypothèse : tester la préparation de défausse et des attaquants moins coûteux en Récompenses;sous conditions des textes de cartes et du soutien disponible.",
    }
    result = []
    for group in selected:
        option = _group_public(group, detail=True)
        option["plan_hypothesis"] = hypotheses.get(family(group), "Hypothèse : examiner évolutions,Énergies,soutien et échange des Récompenses en entraînement;aucune supériorité démontrée.")
        option["difference_from_base"] = _quantitative_diff(reference, group, 1)["counts"]
        option["export_selector"] = option["reference"]
        result.append(option)
    return {**_advisor_context(as_of), "status": "PARTIAL_WITH_EVIDENCE" if issues or len(result) < options else "OK",
            "options": result, "requested_options": options, "issues": issues,
            "selection_method": "different_families;unweighted_distinct_composition_medoid;ties_by_composition_id;not_strength_or_placement_ranking"}
