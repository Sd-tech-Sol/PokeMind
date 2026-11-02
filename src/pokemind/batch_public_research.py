"""Bounded PUBLIC-only refresh. No log, player, private deck or statistics input."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
import uuid
import os
from html import unescape
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser

from pokemind import competitive, learning_loop
from pokemind.public_deck_preflight import SCOPED_PUBLIC_CACHES

MAX_GETS = 150
MAX_BYTES = 32 * 1024 * 1024
MAX_RESPONSE = 2 * 1024 * 1024
AGENT = "PokeMind/1.0 (owner-authorized bounded public research)"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("PUBLIC_REDIRECT_REFUSED")


def allowed_url(url):
    p = urlsplit(url)
    if p.scheme != "https" or p.query or p.fragment or p.username or p.password or p.port not in (None, 443):
        raise ValueError("PUBLIC_URL_REFUSED")
    if p.netloc == "api.tcgdex.net" and re.fullmatch(r"/v2/(?:en|fr)/cards/[A-Za-z0-9.-]{1,80}", p.path):
        return p.netloc
    if p.netloc == "www.limitlesstcg.com" and re.fullmatch(r"/(?:robots\.txt|decks(?:/[0-9]+(?:/[a-z0-9-]+)?)?|decks/list/[0-9]+)", p.path):
        return p.netloc
    if p.netloc == "www.pokemon.com" and (p.path == "/robots.txt" or p.path in {
        "/us/play-pokemon/about/tournaments-rules-and-resources",
        "/us/pokemon-news/2026-pokemon-tcg-standard-format-rotation-announcement"}):
        return p.netloc
    raise ValueError("PUBLIC_URL_REFUSED")


def public_endpoints(root, as_of):
    """Only already PUBLIC catalog/list metadata and fixed official resources."""
    from pokemind.battle_batch import safe_path
    urls = ["https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources",
            "https://www.pokemon.com/us/pokemon-news/2026-pokemon-tcg-standard-format-rotation-announcement",
            "https://www.limitlesstcg.com/decks"]
    pair = [Path(root) / p for p in SCOPED_PUBLIC_CACHES]
    # Public names cover a fixed broad set, never a private-game-derived query.
    core = ("dragapult", "drakloak", "dreepy", "dusknoir", "dusclops", "duskull", "munkidori",
            "kangaskhan", "absol", "audino", "slowking", "alakazam", "gholdengo", "charizard",
            "hydrapple", "dudunsparce", "lucario", "psyduck", "team rocket's watchtower")
    try:
        from pokemind.public_campaign import require_public_database
        for p in pair:
            safe_path(root, p)
            require_public_database(root, p)
        with closing(sqlite3.connect(pair[1].as_uri() + "?mode=ro&immutable=1", uri=True)) as con:
            rows = con.execute("SELECT DISTINCT t.printing_id,t.name,t.source_url FROM catalog_translations t "
                "JOIN catalog_printings p ON p.tcgdex_id=t.printing_id LEFT JOIN catalog_sets s ON s.tcgdex_id=p.set_id "
                "WHERE t.language='en' AND t.status='present' AND (p.regulation_mark IN ('H','I','J') OR p.regulation_mark IS NULL) "
                "AND (s.release_date IS NULL OR s.release_date<=?) ORDER BY s.release_date DESC,t.printing_id", (as_of,)).fetchall()
        cards = []
        for pid, name, url in rows:
            if any(word in (name or "").casefold() for word in core):
                # Use a modern API endpoint only for IDs already in the PUBLIC catalog.
                for language in ("en", "fr"):
                    candidate = f"https://api.tcgdex.net/v2/{language}/cards/{pid}"
                    try:
                        allowed_url(candidate)
                        cards.append(candidate)
                    except ValueError:
                        pass
        # Recent public printings first. Keep both languages for each selected ID.
        urls.extend(cards[:72])
        with closing(sqlite3.connect(pair[0].as_uri() + "?mode=ro&immutable=1", uri=True)) as con:
            urls.extend(r[0] for r in con.execute("SELECT DISTINCT list_url FROM meta_competitive_lists ORDER BY placement LIMIT 4"))
    except (OSError, ValueError, sqlite3.Error):
        pass
    return list(dict.fromkeys(urls))


def refresh_public(root, *, as_of, opener=None, campaign=None, endpoints=None, cancelled=None,
                   max_gets=None, max_bytes=None, official_policy=None):
    """Separate explicit network action; no private input is accepted by this API."""
    from pokemind.battle_batch import safe_path, _new_file
    competitive._advisor_context(as_of)
    root = Path(root).absolute()
    if campaign is not None and not re.fullmatch('[0-9a-f]{32}', campaign):
        raise ValueError('PUBLIC_CAMPAIGN_ID_INVALID')
    # Keep paths below legacy Windows MAX_PATH even inside a synthetic root.
    suffix = campaign[:16] if campaign else as_of.replace('-', '')
    target = safe_path(root, root / f"data/local/public-campaigns/lot-i-battle-intelligence-{suffix}", exists=False)
    manifest = target / "research.json"
    if manifest.exists():
        safe_path(root, manifest)
        value = json.loads(manifest.read_text(encoding="utf-8"))
        if value.get("scope") != "PUBLIC_ONLY" or value.get("as_of") != as_of:
            raise ValueError("PUBLIC_CAMPAIGN_CONFLICT")
        return {**value, "reused_offline": True}  # never reopen a closed envelope
    if target.exists():
        # A crash/reservation is not permission to retry or to create another budget.
        raise ValueError("PUBLIC_CAMPAIGN_INCOMPLETE_NO_RETRY")
    target.mkdir(parents=True, exist_ok=False)
    _new_file(target / "PUBLIC_ONLY.json", b'{"kind":"public_research_only","schema_version":1}\n')
    (target / "pages").mkdir()
    report = {"scope": "PUBLIC_ONLY", "as_of": as_of, "gets": 0, "bytes": 0,
              "max_gets": min(MAX_GETS, max_gets or MAX_GETS), "max_bytes": min(MAX_BYTES, max_bytes or MAX_BYTES),
              "requests": [], "facts": [], "closed_hosts": {}}
    opener = opener or build_opener(NoRedirect())
    robots, attempted, last_host_call = {}, set(), {}
    def fetch(url, *, robot=False):
        if cancelled and cancelled():
            report['stopped'] = 'CANCELLED'
            return None
        host = allowed_url(url)
        if host in report["closed_hosts"] or url in attempted:
            return None
        if report["gets"] >= report['max_gets'] or report["bytes"] >= report['max_bytes']:
            report["stopped"] = "BUDGET_EXHAUSTED"
            return None
        attempted.add(url)
        report["gets"] += 1
        record = {"url": url, "state": "reserved", "retrieved_at": datetime.now(timezone.utc).isoformat()}
        report["requests"].append(record)
        # Durable reservations use new files; a process crash cannot silently reset
        # the quota or cause automatic retries on the next launch.
        _new_file(target / f"reservation-{report['gets']:03d}.json", json.dumps(record).encode())
        try:
            if host in last_host_call:
                time.sleep(max(0, 1 - (time.monotonic() - last_host_call[host])))
            last_host_call[host] = time.monotonic()
            with opener.open(Request(url, headers={"User-Agent": AGENT, "Accept": "application/json,text/html,text/plain"}), timeout=25) as response:
                if response.status != 200 or response.geturl() != url:
                    raise ValueError("HTTP_OR_REDIRECT_REFUSED")
                allowance = min(MAX_RESPONSE, report['max_bytes'] - report["bytes"])
                body = response.read(allowance)
                report["bytes"] += len(body)
                if len(body) >= allowance:
                    raise ValueError("RESPONSE_SIZE_CAP")
            lower = body[:65536].lower()
            if any(term in lower for term in (b"cf-chl-", b"captcha", b"verify you are human", b"access denied", b"just a moment...")):
                raise ValueError("PROTECTION_PAGE_NO_BYPASS")
            sha = hashlib.sha256(body).hexdigest()
            # Only the TCGdex data licence permits retention established here.
            # HTML bodies from sources with unestablished rights stay ephemeral.
            if host == 'api.tcgdex.net':
                _new_file(target / "pages" / (sha + ".body"), body)
            record.update(state="complete", bytes=len(body), sha256=sha, http_status=200)
            headers = getattr(response, 'headers', {})
            record.update(etag=headers.get('ETag'), last_modified=headers.get('Last-Modified'))
            return body
        except (HTTPError, URLError, OSError, ValueError) as exc:
            category = "HTTP_" + str(exc.code) if isinstance(exc, HTTPError) else type(exc).__name__
            record.update(state="stopped_no_retry", reason=category)
            report["closed_hosts"][host] = category
            return None
    queue = [(url, None) for url in (endpoints if endpoints is not None else public_endpoints(root, as_of))]
    for url, family in queue:
        if report.get('stopped') == 'CANCELLED':
            break
        try:
            host = allowed_url(url)
        except ValueError:
            continue
        if host != "api.tcgdex.net" and host not in robots:
            body = fetch(f"https://{host}/robots.txt", robot=True)
            if body is None:
                robots[host] = False
            else:
                parser = RobotFileParser()
                parser.parse(body.decode("utf-8", errors="replace").splitlines())
                robots[host] = parser
        policy = robots.get(host)
        if host != "api.tcgdex.net" and (policy is False or not policy.can_fetch(AGENT, url)):
            continue
        body = fetch(url)
        if body is None:
            continue
        record = report["requests"][-1]
        fact = {"source_url": url, "retrieved_at": record["retrieved_at"], "sha256": record["sha256"],
                "status": "provider_observation_not_normative_certification",
                'publisher': host, 'published_at': None, 'effective_from': None,
                'format': 'unknown', 'license': 'MIT data; images excluded' if host == 'api.tcgdex.net' else 'retention_of_raw_content_not_established',
                'etag': record.get('etag'), 'last_modified': record.get('last_modified'),
                'validation': 'schema_validated_observation' if host == 'api.tcgdex.net' else 'unverified'}
        if host == "api.tcgdex.net":
            try:
                payload = json.loads(body)
                if payload.get("id") != url.rsplit("/", 1)[1] or not isinstance(payload.get("name"), str):
                    raise ValueError
                fact.update(kind="card", language=url.split("/")[-3],
                    card={k: payload.get(k) for k in ("id", "name", "category", "stage", "hp", "regulationMark",
                        "effect", "abilities", "attacks", "retreat", "energyType")})
            except (ValueError, TypeError, AttributeError):
                report["closed_hosts"][host] = "UNSUPPORTED_PAYLOAD_NO_RETRY"
                continue
        elif host == "www.limitlesstcg.com" and "/decks/list/" not in url:
            html = body.decode("utf-8", errors="replace")
            if url.rstrip("/").endswith("/decks"):
                entries = []
                for href, label in re.findall(r'<a\b[^>]*href=["\'](/decks/[0-9]+(?:/[a-z0-9-]+)?)["\'][^>]*>(.*?)</a>', html, re.I | re.S):
                    label = " ".join(unescape(re.sub(r"<[^>]+>", " ", label)).split())
                    if not label:
                        label = href.rsplit("/", 1)[-1].replace("-", " ").title()
                    if label and len(label) <= 100 and href not in {e["path"] for e in entries}:
                        entries.append({"path": href, "archetype": label})
                fact.update(kind="public_archetype_directory", entries=entries)
                focus = ("kangaskhan", "dragapult", "absol", "gardevoir", "starmie", "froslass", "lucario", "slowking")
                selected = [e for e in entries if any(w in e["path"].casefold() + e["archetype"].casefold() for w in focus)][:8]
                if not selected:
                    selected = entries[:6]
                queue.extend(("https://www.limitlesstcg.com" + e["path"], e["archetype"]) for e in selected)
            else:
                links = list(dict.fromkeys(re.findall(r'["\'](/decks/list/[0-9]+)["\']', html)))[:2]
                queue.extend(("https://www.limitlesstcg.com" + link, family) for link in links)
                fact.update(kind="public_archetype_page", archetype=family, list_links=links)
        elif host == "www.limitlesstcg.com":
            try:
                export = competitive.parse_list(body)
                parsed = competitive.parse_deck_export(export)
                if parsed.total_cards != 60:
                    raise ValueError
                fact.update(kind="deck60", export=export, total_cards=60, legality="unknown", live="unknown",
                            archetype=family, publication_date="unknown", author="unknown")
            except ValueError:
                report["closed_hosts"][host] = "UNVERIFIED_DECK_BODY_NO_RETRY"
                continue
        else:
            fact.update(kind="official_document", review_status="unverified", legality="unknown")
            from pokemind.public_source_fields import extract_official_fields
            fact['rule_evidence'] = extract_official_fields(body, source_url=url,
                policy=(official_policy or {}).get(url))
            fact['published_at'] = fact['rule_evidence']['published_at']
        report["facts"].append(fact)
    report.setdefault("stopped", "COMPLETED_NO_RESTART")
    journal = []
    for i, fact in enumerate(report["facts"]):
        journal = learning_loop.append_record(journal, record_id=f"public-{i:03d}", kind="source_fact", recorded_at=as_of,
            payload={"provenance": fact["source_url"], **fact}, refs=["source:" + fact["source_url"]])
    _new_file(target / "research.learning.json", (json.dumps(journal, ensure_ascii=False, indent=2) + "\n").encode())
    _new_file(manifest, (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode())
    index = safe_path(root, root / "data/local/public-campaigns/battle-intelligence-index.jsonl", exists=False)
    if index.exists():
        if index.stat().st_nlink != 1 or index.stat().st_size > 1024 * 1024:
            raise ValueError("PUBLIC_INDEX_UNSAFE")
        for line in index.read_text(encoding="utf-8").splitlines():
            if json.loads(line).get("scope") != "PUBLIC_ONLY":
                raise ValueError("PUBLIC_INDEX_CONFLICT")
    with index.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"scope": "PUBLIC_ONLY", "as_of": as_of, "manifest": str(manifest.relative_to(root))}) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return report


def knowledge_view(root, *, as_of, topic=None):
    """Read existing immutable research snapshots, retaining revisions by source.

    No additional factual store: this is a projection over the existing index
    and source_fact Learning Loop journals. Never scans for unindexed files.
    """
    from pokemind.battle_batch import safe_path, digest
    root = Path(root).absolute()
    index = safe_path(root, root / 'data/local/public-campaigns/battle-intelligence-index.jsonl', exists=False)
    if not index.exists():
        return {'facts': [], 'history': [], 'as_of': as_of, 'source': 'existing_public_research_snapshots'}
    if index.stat().st_nlink != 1 or index.stat().st_size > 1024 * 1024:
        raise ValueError('PUBLIC_INDEX_UNSAFE')
    history, seen, current = [], set(), {}
    for line in index.read_text(encoding='utf-8').splitlines():
        entry = json.loads(line)
        if entry.get('scope') != 'PUBLIC_ONLY' or entry.get('as_of', '') > as_of:
            continue
        path = root / entry['manifest']
        if path.parent.parent != root / 'data/local/public-campaigns' or not path.parent.name.startswith('lot-i-battle-intelligence-') or path.name != 'research.json':
            raise ValueError('PUBLIC_INDEX_CONFLICT')
        safe_path(root, path)
        if path.stat().st_size > 16 * 1024 * 1024:
            raise ValueError('PUBLIC_MANIFEST_SIZE_CAP')
        value = json.loads(path.read_text(encoding='utf-8'))
        if value.get('scope') != 'PUBLIC_ONLY':
            raise ValueError('PUBLIC_MANIFEST_SCOPE')
        for fact in value['facts']:
            key = (fact['source_url'], fact['kind'])
            allowed_url(fact['source_url'])
            relevant = (topic is None or
                topic == 'card' and fact['kind'] == 'card' or
                topic == 'rules' and fact['kind'] == 'official_document' or
                topic == 'meta' and fact['kind'].startswith(('deck60', 'public_archetype')))
            if not relevant:
                continue
            identity = digest({k: v for k, v in fact.items() if k not in {'retrieved_at', 'etag', 'last_modified'}})
            if identity not in seen:
                if key in current:
                    current[key]['revision_status'] = 'superseded'
                row = dict(fact, version=identity, revision_status='current')
                history.append(row)
                seen.add(identity)
            else:
                row = next(r for r in history if r['version'] == identity)
                if key in current and current[key] is not row:
                    current[key]['revision_status'] = 'superseded'
                row['revision_status'] = 'current'
                row['retrieved_at'] = fact['retrieved_at']
            current[key] = row
    return {'facts': list(current.values()), 'history': history, 'as_of': as_of,
            'source': 'existing_public_research_snapshots', 'public_only': True}


def research(root, *, as_of, topic='meta', identity=None, opener=None, offline=False, cancelled=None,
             official_policy=None):
    """Cache first; a new requested envelope never reopens a historical one."""
    if topic not in {'meta', 'rules', 'card'}:
        raise ValueError('PUBLIC_TOPIC_INVALID')
    competitive._advisor_context(as_of)
    if topic == 'card' and (not isinstance(identity, str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9.-]{0,89}', identity) or '..' in identity):
        raise ValueError('PUBLIC_CARD_ID_REQUIRED')
    before = knowledge_view(root, as_of=as_of, topic=topic)
    selected = [f for f in before['facts'] if topic != 'card' or f.get('card', {}).get('id') == identity]
    ttl = 30 if topic == 'card' else 1
    today = datetime.fromisoformat(as_of).date()
    from pokemind.toronto_tz import toronto_zone
    def retrieved_date(fact):
        stamp = datetime.fromisoformat(fact['retrieved_at'].replace('Z', '+00:00'))
        return stamp.astimezone(toronto_zone()).date() if stamp.tzinfo else stamp.date()
    for fact in selected:
        fact['fresh'] = 0 <= (today - retrieved_date(fact)).days < ttl
    fresh = bool(selected) and (any(f['fresh'] and f['kind'] == 'public_archetype_directory' for f in selected)
        if topic == 'meta' else all(f['fresh'] for f in selected))
    from pokemind import battle_batch, battle_coach
    control = Path(root).absolute() / 'data/local/public-campaigns/research-control.json'
    remembered, control_stamp = battle_coach._control(Path(root).absolute(), control)
    key = topic + ':' + (identity or '')
    remembered = remembered or {}
    cooldown = remembered.get(key, {}).get('blocked_on') == as_of
    if fresh or offline or cooldown:
        return {'as_of':as_of,
            **({'meta_evidence':public_meta_evidence(root, as_of=as_of)} if topic=='meta' else {}),
            'status': 'SOURCE_COOLDOWN' if cooldown else 'CACHE_FRESH' if fresh else 'OFFLINE_STALE_OR_EMPTY', 'persisted': True,
            'added': 0, 'updated': 0, 'already_known': len(selected), 'unverified': sum(f.get('validation') != 'schema_validated_observation' for f in selected),
            'gets': 0, 'facts': selected, 'sources': list(dict.fromkeys(f['source_url'] for f in selected)), 'fresh': fresh}
    if topic == 'card':
        endpoints = [f'https://api.tcgdex.net/v2/{lang}/cards/{identity}' for lang in ('en', 'fr')]
    elif topic == 'rules':
        endpoints = ['https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources',
            'https://www.pokemon.com/us/pokemon-news/2026-pokemon-tcg-standard-format-rotation-announcement']
    else:
        endpoints = ['https://www.limitlesstcg.com/decks']
    result = refresh_public(root, as_of=as_of, opener=opener, campaign=uuid.uuid4().hex,
                            endpoints=endpoints, cancelled=cancelled,
                            official_policy=official_policy,
                            max_gets=142 if topic == 'meta' else None,
                            max_bytes=16*1024*1024 if topic == 'meta' else None)
    remembered[key] = {'last_attempt':as_of, 'blocked_on':as_of if result['closed_hosts'] else None}
    battle_coach._atomic_control(Path(root).absolute(), control, remembered, control_stamp)
    after = knowledge_view(root, as_of=as_of, topic=topic)
    prior_keys = {(f['source_url'], f['kind']): f['version'] for f in before['facts']}
    added = updated = known = 0
    for fact in result['facts']:
        key = (fact['source_url'], fact['kind'])
        row = next(f for f in after['facts'] if (f['source_url'], f['kind']) == key)
        if key not in prior_keys:
            added += 1
        elif prior_keys[key] != row['version']:
            updated += 1
        else:
            known += 1
    return {'as_of':as_of,
        **({'meta_evidence':public_meta_evidence(root, as_of=as_of)} if topic=='meta' else {}),
        'status': 'PARTIAL' if result['closed_hosts'] or result['stopped'] != 'COMPLETED_NO_RESTART' else 'SAVED',
        'persisted': True, 'added': added, 'updated': updated, 'already_known': known,
        'unverified': sum(f.get('validation') != 'schema_validated_observation' for f in result['facts']),
        'gets': result['gets'], 'bytes': result['bytes'], 'facts': after['facts'],
        'sources': [r['url'] for r in result['requests'] if r['state'] == 'complete'],
        'closed_hosts': result['closed_hosts'], 'fresh': False}


def research_matchups(root, *, as_of, cancelled=None):
    """Use the existing PUBLIC campaign and meta engines, with a daily cache.

    Eight capped API calls complement the HTML envelope (142 calls /16 MiB).
    Previous source databases stay immutable; the control retains last good data.
    """
    from pokemind import battle_batch, battle_coach, public_campaign
    root = Path(root).absolute()
    folder = battle_batch.safe_path(root, root / 'data/local/public-campaigns', exists=False)
    folder.mkdir(parents=True, exist_ok=True)
    pointer = folder / 'chat-matchups.json'
    previous, stamp = battle_coach._control(root, pointer)
    if previous and previous.get('as_of') == as_of:
        return previous | {'cache_hit':True, 'gets':0}
    name = 'chat-' + uuid.uuid4().hex[:16]
    report = public_campaign.run_campaign(root, name, create=True, execute=True,
        tcgdex_budget=0, official_budget=0, meta_budget=8,
        response_limit=2*1024*1024, cancelled=cancelled)
    db = root / 'data/local/public-campaigns' / ('lot-i-' + name) / 'public.sqlite3'
    public_campaign.require_public_database(root, db)
    with closing(sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1', uri=True)) as con:
        matches = con.execute('SELECT COUNT(*) FROM meta_matches WHERE eligible=1').fetchone()[0]
    receipt = {'as_of':as_of, 'attempt_campaign':name, 'valid_campaign': name if matches else (previous or {}).get('valid_campaign'),
        'status': 'SOURCE_SNAPSHOT_SAVED' if matches else 'INSUFFICIENT_OR_BLOCKED_PUBLIC_DATA',
        'eligible_matches':matches, 'gets':report['get_attempts'], 'bytes':report.get('response_bytes_received', 0),
        'scope':'PUBLIC_ONLY', 'source_url':'https://docs.limitlesstcg.com/developer/tournaments',
        'winrate':None, 'persisted':True, 'cache_hit':False}
    battle_coach._atomic_control(root, pointer, receipt, stamp)
    return receipt


def matchup_database(root):
    from pokemind import battle_batch, battle_coach, public_campaign
    root = Path(root).absolute()
    pointer = battle_batch.safe_path(root, root / 'data/local/public-campaigns/chat-matchups.json', exists=False)
    value, _ = battle_coach._control(root, pointer)
    name = (value or {}).get('valid_campaign')
    if not isinstance(name, str) or not re.fullmatch('chat-[0-9a-f]{16}', name):
        return None
    path = root / 'data/local/public-campaigns' / ('lot-i-' + name) / 'public.sqlite3'
    public_campaign.require_public_database(root, path)
    return path


def public_meta_evidence(root, *, as_of):
    """Read-only projection of the existing marked matchup cache, no GET."""
    from datetime import date, timedelta
    from pokemind.meta import meta_window_comparison
    db = matchup_database(root)
    if db is None:
        return None
    end = date.fromisoformat(as_of)
    return meta_window_comparison(db, since=(end-timedelta(days=27)).isoformat(),
        split=(end-timedelta(days=13)).isoformat(), until=as_of, as_of=as_of)


def load_public_research(root, as_of):
    from pokemind.battle_batch import safe_path
    path = Path(root) / f"data/local/public-campaigns/lot-i-battle-intelligence-{as_of.replace('-', '')}/research.json"
    try:
        index = Path(root) / "data/local/public-campaigns/battle-intelligence-index.jsonl"
        if index.exists():
            safe_path(root, index)
            if index.stat().st_size <= 1024 * 1024 and index.stat().st_nlink == 1:
                entries = [json.loads(line) for line in index.read_text(encoding="utf-8").splitlines()]
                candidates = [row for row in entries if row.get("scope") == "PUBLIC_ONLY" and row.get("as_of", "") <= as_of]
                if candidates:
                    selected = max(candidates, key=lambda row: row["as_of"])
                    path = Path(root) / selected["manifest"]
                    if path.parent.parent != Path(root) / "data/local/public-campaigns" or not path.parent.name.startswith("lot-i-battle-intelligence-"):
                        return None
        safe_path(root, path)
        result = json.loads(path.read_text(encoding="utf-8"))
        return result if result.get("scope") == "PUBLIC_ONLY" and result.get("as_of", "") <= as_of else None
    except (ValueError, OSError):
        return None
