"""Owner-selected folder analysis over the existing parser/observer/learning engines.

Raw inputs never leave the selected folder or enter a network request. An older
owner schema is observed read-only; derived snapshots use the existing local
Learning Loop JSON contract until a separately authorized migration is possible.
"""
from __future__ import annotations

import hashlib
import copy
import json
import os
import re
import sqlite3
import stat
import threading
import time
import unicodedata
from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import replace
from datetime import date
from pathlib import Path

from pokemind import battle_logs as logs, competitive, deck_library, learning_loop, opponent_observer
from pokemind import counter_deck, deck_knowledge, rules
from pokemind.database import SCHEMA_VERSION
from pokemind.public_deck_preflight import SCOPED_PUBLIC_CACHES

VERSION = "battle-batch-v4"
MAX_FILES = 20_000
MAX_TOTAL = 1024 ** 3


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def safe_path(root, path, *, expected=None, exists=True):
    root, path = Path(root).absolute(), Path(path).absolute()
    if (".." in path.parts or not path.is_relative_to(root)
            or any(":" in p for p in path.parts[1:]) or (expected is not None and path != root / expected)):
        raise ValueError("BATCH_PATH_OUT_OF_SCOPE")
    for ancestor in (*reversed(path.parents), path):
        try:
            info = ancestor.lstat()
        except FileNotFoundError:
            if not exists and ancestor.is_relative_to(root):
                continue
            raise ValueError("BATCH_PATH_MISSING") from None
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 1024:
            raise ValueError("BATCH_REDIRECTION_REFUSED")
    if exists and not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("BATCH_RESOLVED_SCOPE_REFUSED")
    return path


def files_in_folder(root, folder, *, max_files=MAX_FILES, max_total=MAX_TOTAL):
    """Only this explicitly selected tree; fail before content on cap violation."""
    folder = safe_path(root, folder, expected="data/local/battle_logs")
    if not folder.is_dir():
        raise ValueError("BATCH_FOLDER_REQUIRED")
    stack, paths, refused, total, entries, log_entries = [folder], [], Counter(), 0, 0, 0
    while stack:
        parent = safe_path(folder, stack.pop())
        with os.scandir(parent) as directory:
            for entry in directory:
                entries += 1
                if entries > max_files * 4:
                    raise ValueError("BATCH_DIRECTORY_ENTRY_CAP")
                try:
                    path = safe_path(folder, Path(entry.path))
                    info = path.lstat()
                except (ValueError, OSError):
                    refused["unsafe_path"] += 1
                    continue
                if stat.S_ISDIR(info.st_mode):
                    stack.append(path)
                elif path.suffix.lower() in {".txt", ".log"}:
                    log_entries += 1
                    if log_entries > max_files:
                        raise ValueError("BATCH_TOTAL_CAP_NO_CONTENT_READ")
                    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                        refused["unsafe_file"] += 1
                        continue
                    if info.st_size > logs.MAX_LOG_BYTES:
                        refused["file_size_cap"] += 1
                        continue
                    paths.append(path)
                    total += info.st_size
                    if len(paths) > max_files or total > max_total:
                        raise ValueError("BATCH_TOTAL_CAP_NO_CONTENT_READ")
    return sorted(paths), dict(refused), total


def read_selected(folder, path):
    path = safe_path(folder, path)
    before = path.stat()
    if before.st_size > logs.MAX_LOG_BYTES or before.st_nlink != 1:
        raise ValueError("BATCH_FILE_UNSAFE")
    keys = ("st_dev", "st_ino", "st_size", "st_mtime_ns")
    with path.open("rb") as source:
        opened = os.fstat(source.fileno())
        if any(getattr(before, k) != getattr(opened, k) for k in keys) or opened.st_nlink != 1:
            raise ValueError("BATCH_SOURCE_CHANGED")
        raw = source.read(logs.MAX_LOG_BYTES + 1)
        after = os.fstat(source.fileno())
    final = safe_path(folder, path).stat()
    if any(getattr(before, k) != getattr(other, k) for other in (after, final) for k in keys):
        raise ValueError("BATCH_SOURCE_CHANGED")
    text, encoding = logs.decode_log_bytes(raw)
    if "\x00" in text:
        raise ValueError("BATCH_BINARY_LOG")
    return text, encoding


def semantic_text(text):
    return "\n".join(line.rstrip() for line in unicodedata.normalize("NFKC", text).replace("\r", "").splitlines() if line.strip())


def equivalent_text_key(text):
    """Ignore indentation already ignored by the parser; preserve all content."""
    return digest(semantic_text('\n'.join(line.strip() for line in text.splitlines())))


def parse_selected(text, player):
    # More than one terminal victory or a reset of numbered turns is a
    # concatenation, not evidence for two blindly linked records.
    wins = sum(any(p.search(line) for p in logs.WIN_PATTERNS) for line in text.splitlines())
    turns = [m[0] for line in text.splitlines() if (m := logs._match_turn(line.strip()))]
    if wins > 1 or any(b < a for a, b in zip(turns, turns[1:])):
        raise ValueError("BATCH_CONCATENATED_GAMES_REFUSED")
    parsed = logs.parse_battle_log(text, reference_player=player)
    if not parsed.valid or parsed.opponent_name is None:
        raise ValueError("BATCH_PLAYER_OR_PARTICIPANTS_UNRESOLVED")
    return parsed


def segments(text):
    """Terminal-winner boundaries only; incomplete tails still need validation."""
    lines = text.splitlines()
    ends = [i + 1 for i, line in enumerate(lines) if any(p.search(line) for p in logs.WIN_PATTERNS)]
    if len(ends) < 2:
        return [text]
    result, start = [], 0
    for end in ends:
        result.append("\n".join(lines[start:end]))
        start = end
    if any(line.strip() for line in lines[start:]):
        result.append("\n".join(lines[start:]))
    return result


def database_preflight(root, db):
    try:
        db = safe_path(root, db, expected="data/local/pokemind.sqlite3")
        if not db.is_file() or db.stat().st_nlink != 1:
            return {"status": "BLOCKED_UNSAFE", "can_import": False}
        for suffix in ("-wal", "-shm", "-journal"):
            if db.with_name(db.name + suffix).exists():
                return {"status": "BLOCKED_SIDECAR", "can_import": False}
        with closing(sqlite3.connect(db.as_uri() + "?mode=ro&immutable=1", uri=True, timeout=1)) as con:
            version = con.execute("PRAGMA user_version").fetchone()[0]
            integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok" or con.execute("PRAGMA foreign_key_check").fetchone() is not None:
                return {"status": "BLOCKED_INTEGRITY", "can_import": False}
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        return {"status": "COMPATIBLE" if version == SCHEMA_VERSION else "BLOCKED_SCHEMA_NO_MIGRATION",
                "schema_version": version, "expected_schema": SCHEMA_VERSION, "integrity": "ok",
                "can_import": version == SCHEMA_VERSION and {"battle_logs", "battle_events", "observed_decks"} <= tables}
    except (ValueError, OSError, sqlite3.Error):
        return {"status": "BLOCKED_MISSING_OR_UNAVAILABLE", "can_import": False}


_CONTEXTS, _CONTEXTS_LOCK = {}, threading.Lock()
RESEARCH_INDEX = 'data/local/public-campaigns/battle-intelligence-index.jsonl'


def _public_context_key(root, paths, as_of):
    """Every file the public context is read from, by size and date; no folder is listed."""
    snapshot = competitive._snapshot_key(paths[0], as_of)
    if snapshot is None:
        return None
    try:
        index = Path(root) / RESEARCH_INDEX
        fallback = Path(root) / ('data/local/public-campaigns/lot-i-battle-intelligence-'
                                 + as_of.replace('-', '') + '/research.json')
        named = [paths[1], index, fallback]
        if index.is_file():
            if index.stat().st_size > 1024 * 1024:
                return None
            for line in index.read_text(encoding='utf-8').splitlines():
                manifest = json.loads(line).get('manifest') if line.strip() else None
                if isinstance(manifest, str):
                    named.append(Path(root) / manifest)
        stamps = []
        for path in named:
            info = path.stat() if path.exists() else None
            stamps.append((os.path.normcase(str(path)), info and info.st_mtime_ns, info and info.st_size))
        return os.path.normcase(str(Path(root).absolute())), as_of, snapshot, tuple(stamps)
    except (OSError, ValueError, TypeError, AttributeError):
        return None


def public_context(root, as_of):
    """Public families and signatures, reused while none of their files changed (a private copy each time).

    Rebuilt for every imported game, about 5 s each (owner's diagnostic, 2026-11-05).
    """
    paths = [Path(root) / p for p in SCOPED_PUBLIC_CACHES]
    key = _public_context_key(root, paths, as_of)
    if key is not None:
        with _CONTEXTS_LOCK:
            hit = _CONTEXTS.get(key)
        if hit is not None:
            try:
                for path in paths:
                    safe_path(root, path)
            except (ValueError, OSError):
                return None, paths, {"status": "BLOCKED_PUBLIC_REFERENCE", "references": 0}
            return copy.deepcopy(hit[0]), paths, dict(hit[1])
    index, paths, source = _public_context_uncached(root, as_of)
    if index is not None and key is not None and key == _public_context_key(root, paths, as_of):
        with _CONTEXTS_LOCK:
            if len(_CONTEXTS) >= 2:
                _CONTEXTS.clear()
            _CONTEXTS[key] = (copy.deepcopy(index), dict(source))
    return index, paths, source


def _public_context_uncached(root, as_of):
    paths = [Path(root) / p for p in SCOPED_PUBLIC_CACHES]
    try:
        for path in paths:
            safe_path(root, path)
        index = deck_library.reference_index(root, paths[0], as_of=as_of, reference_db=paths[1])
        # Classification needs Pokemon signatures, not a pile of common Trainers.
        # Translation aliases share an explicitly stored printing ID; no inferred
        # reprint equivalence or regulation claim is introduced here.
        with closing(sqlite3.connect(paths[1].as_uri() + "?mode=ro&immutable=1", uri=True)) as con:
            rows = con.execute("SELECT t.printing_id,t.language,t.name,p.category,t.payload_sha256 FROM catalog_translations t "
                "JOIN catalog_printings p ON p.tcgdex_id=t.printing_id WHERE t.status='present' "
                "AND t.retrieved_at IS NOT NULL AND substr(t.retrieved_at,1,10)<=?", (as_of,)).fetchall()
        aliases, english, by_name, hashes, french = defaultdict(set), {}, defaultdict(set), {}, {}
        for pid, lang, name, category, sha in rows:
            if rules._normalized_name(category or "") not in {"pokemon", "pokémon"}:
                continue
            norm = rules._normalized_name(name or "")
            aliases[pid].add(norm)
            by_name[norm].add(pid)
            if lang == "en":
                english[pid] = norm
                hashes[pid] = sha
            elif lang == "fr":
                french[pid] = name
        from pokemind.batch_public_research import load_public_research
        research = load_public_research(root, as_of)
        from pokemind.batch_public_research import knowledge_view
        remembered = knowledge_view(root, as_of=as_of)
        if remembered['facts']:
            research = remembered
        if research:
            refreshed_english = {f["card"]["id"]: rules._normalized_name(f["card"]["name"])
                for f in research["facts"] if f.get("kind") == "card" and f.get("language") == "en"}
            for fact in research["facts"]:
                card = fact.get("card", {})
                pid = card.get("id")
                if pid in aliases and card.get("name") and refreshed_english.get(pid) == english.get(pid):
                    aliases[pid].add(rules._normalized_name(card["name"]))
                    if fact.get("language") == "fr":
                        french[pid] = card["name"]
                if fact.get("kind") == "deck60" and fact.get("archetype"):
                    cards = competitive._card_map(fact["export"])
                    if sum(c["quantity"] for c in cards.values()) != 60:
                        continue
                    selector = "web-" + fact["source_url"].rsplit("/", 1)[-1] + ":1"
                    family = canonical_family(fact["archetype"], {r["archetype"] for r in index["references"]})
                    composition = {"composition_id": competitive._composition_id(cards),
                        "source_urls": [fact["source_url"]], "archetypes": [family],
                        "interpretation": "published_reference_not_attested_tournament_or_matchup_strength"}
                    index["references"].append({"archetype": family, "original_public_label": fact["archetype"],
                        "names": sorted({rules._normalized_name(c["name"]) for c in cards.values()}),
                        "composition": composition, "selector": selector, "total_cards": 60,
                        "cards": [dict(c, aliases=[rules._normalized_name(c['name'])]) for c in cards.values()],
                        "export": fact['export']})
        family_members = {ref["selector"]: {pid for name in ref["names"] for pid in by_name.get(name, ())}
                          for ref in index["references"]}
        member_families = defaultdict(set)
        for ref in index["references"]:
            for pid in family_members[ref["selector"]]:
                member_families[english.get(pid, pid)].add(ref["archetype"])
        minimums, weights, primary_names = {}, {}, defaultdict(set)
        for ref in index["references"]:
            members = family_members[ref["selector"]]
            words = [w for w in re.findall(r"[a-z]{3,}", ref["archetype"].casefold())
                     if w not in {"mega", "box", "lead", "team", "rocket"}]
            primary = {pid for pid in members if any(w in english.get(pid, "") for w in words[:1])}
            primary_names[ref["archetype"]].update(name for pid in primary for name in aliases[pid])
            parents = set()
            if primary:
                from pokemind.catalog_batch_store import verified_payload
                from pokemind.set_code_aliases import payload_source
                with closing(sqlite3.connect(paths[1].as_uri() + "?mode=ro&immutable=1", uri=True)) as con:
                    con.row_factory = sqlite3.Row
                    frontier = set(primary)
                    for _ in range(2):
                        next_frontier = set()
                        for pid in frontier:
                            payload = verified_payload(con, "cards", pid, "en", hashes.get(pid))
                            proof = payload_source(con, "cards", pid, "en") if payload else None
                            if proof and payload.get("evolveFrom"):
                                parent = rules._normalized_name(payload["evolveFrom"])
                                next_frontier.update(p for p in members if english.get(p) == parent)
                        parents.update(next_frontier)
                        frontier = next_frontier
            chosen = (primary | parents) if primary else {
                p for p in members if len(member_families[english.get(p, p)]) < 3}
            ref["names"] = sorted({name for pid in chosen for name in aliases[pid]})
            minimums[ref["archetype"]] = 1 if primary else 2
            weights[ref["archetype"]] = 100 if primary else 1
        index["minimum_matches_by_family"] = minimums
        index["signature_weights_by_family"] = weights
        index["primary_names_by_family"] = {k:sorted(v) for k,v in primary_names.items()}
        index["pokemon_names"] = {name: english[pid] for pid, names in aliases.items() if pid in english
                                  for name in names if len(member_families[english[pid]]) < 3}
        index["pokemon_display_names"] = {english[pid]: french.get(pid, english[pid]) for pid in english}
        return index, paths, {"status": "AVAILABLE_SOURCE_CHECKED", "references": len(index["references"])}
    except (ValueError, OSError, sqlite3.Error, KeyError, TypeError):
        return None, paths, {"status": "BLOCKED_PUBLIC_REFERENCE", "references": 0}


def canonical_family(label, known):
    """Merge provider spelling/attack-label aliases, not exact deck variants."""
    label = competitive._family(label)
    if label in known:
        return label
    def main(value):
        words = [w for w in re.findall(r"[a-z]{3,}", value.casefold()) if w not in {"mega", "team", "rocket"}]
        return words[0] if words else value.casefold()
    matches = [family for family in known if main(family) == main(label)]
    return sorted(matches, key=lambda v: (len(v), v))[0] if matches else label


def registered_decks(root, db, preflight, as_of, *, all_versions=False):
    """Read old, healthy schema too; never attest a played version by similarity."""
    if preflight.get("integrity") != "ok":
        return []
    try:
        safe_path(root, db, expected="data/local/pokemind.sqlite3")
        with closing(sqlite3.connect(Path(db).absolute().as_uri() + "?mode=ro&immutable=1", uri=True)) as con:
            con.row_factory = sqlite3.Row
            versions = con.execute("SELECT id,deck_id,version_number,total_cards FROM deck_versions "
                "WHERE exact_confirmed=1 AND total_cards=60 AND substr(imported_at,1,10)<=? "
                "ORDER BY deck_id,version_number DESC LIMIT 100", (as_of,)).fetchall()
            result, seen = [], set()
            for version in versions:
                if version["deck_id"] in seen and not all_versions:
                    continue
                rows = con.execute("SELECT * FROM deck_version_cards WHERE deck_version_id=? ORDER BY ordinal", (version["id"],)).fetchall()
                sections = []
                for kind, label in (("pokemon", "Pokémon"), ("trainer", "Trainer"), ("energy", "Energy")):
                    cards = [r for r in rows if r["card_type"] == kind]
                    sections.append(label + ": " + str(sum(r["quantity"] for r in cards)))
                    sections.extend(r["normalized_line"] for r in cards)
                    sections.append("")
                export = "\n".join(sections) + "\nTotal Cards: 60\n"
                if competitive.parse_deck_export(export).total_cards == 60:
                    result.append({"deck_id": version["deck_id"], "version": version["version_number"],
                        "scope": "registered_reference_not_attested_played_version", "export": export})
                    seen.add(version["deck_id"])
            return result
    except (OSError, ValueError, sqlite3.Error):
        return []


def printing_map(cards, connection, aliases):
    """Collapse a FR/EN name only when the existing resolver proves one printing."""
    resolved, unknown = {}, []
    for literal, card in cards.items():
        identity = rules._resolve_structure_identity(connection,
            {"card_name": card["name"], "set_code": card["set"], "collector_number": card["number"]},
            set_aliases=aliases)
        key = ("printing:" + identity["ids"][0],) if len(identity["ids"]) == 1 else ("literal", *literal)
        if len(identity["ids"]) != 1:
            unknown.append({k: card[k] for k in ("name", "set", "number")})
        if key in resolved:
            resolved[key]["quantity"] += card["quantity"]
        else:
            resolved[key] = dict(card)
    return resolved, unknown


def _redacted(value, parsed):
    for name, label in ((parsed.reference_player, "[joueur]"), (parsed.opponent_name, "[adversaire]")):
        if name:
            value = re.sub(re.escape(name), label, value, flags=re.I)
    return value


def analyze_record(parsed, index, *, as_of, match_id):
    opponent = opponent_observer.observe(parsed, index=index, as_of=as_of)
    own = opponent_observer.observe(replace(parsed, reference_player=parsed.opponent_name,
                                            opponent_name=parsed.reference_player), index=index, as_of=as_of)
    for observed, role in ((opponent, "opponent"), (own, "self")):
        attacking = defaultdict(list)
        for event in parsed.events:
            if event.event_type == "use" and logs._actor_role(event.actor, parsed) == role:
                damage = re.search(r"(?:a infligé|did|dealt)\s+([0-9][0-9\s]{0,5})\s+(?:dégâts|damage)", event.evidence, re.I)
                identity = opponent_observer._card_identity(event.card_name)
                if damage and identity:
                    attacking[identity["normalized_name"]].append(int(re.sub(r"\s", "", damage[1])))
        family=observed["classification"]["label"]
        if role=="opponent" and family and index and index.get("primary_names_by_family",{}).get(family):
            primaries=set(index["primary_names_by_family"][family])
            seen_names={c["normalized_name"] for c in observed["observed_partial"]["cards"]}
            specific_attackers={name for name in attacking if name in index.get("pokemon_names",{})}
            if not (primaries & seen_names) and specific_attackers and not (primaries & specific_attackers):
                # An evolution engine is not proof of its most familiar attacker:
                # another deck may use the same Stage 1 for drawing cards.
                observed["classification"]={"label":None,"basis":"evolution_engine_only_with_different_attacker","exact_deck_proven":False}
        if observed["classification"]["label"] is None and index:
            choices = [c for c in observed["observed_partial"]["cards"]
                       if c["normalized_name"] in index.get("pokemon_names", {})]
            if choices:
                chosen = max(choices, key=lambda c: (
                    bool(attacking[c["normalized_name"]]), len(attacking[c["normalized_name"]]),
                    max(attacking[c["normalized_name"]], default=0),
                    " ex" in index["pokemon_names"][c["normalized_name"]], c["occurrences"]))
                canonical = index["pokemon_names"][chosen["normalized_name"]]
                display = index.get("pokemon_display_names", {}).get(canonical, canonical)
                observed["classification"] = {"label": "Noyau observé : " + display,
                    "basis": "observed_signature_archetype_unresolved", "signature_id": canonical,
                    "exact_deck_proven": False}
    evidence = [{"sequence": e.sequence, "turn": e.turn_number,
                 "role": logs._actor_role(e.actor, parsed), "type": e.event_type,
                 "card": e.card_name if e.event_type != "draw" else None,
                 "text": _redacted(e.evidence, parsed), "confidence": e.confidence,
                 "target": _redacted(e.target, parsed) if e.target else None}
                for e in parsed.events if e.event_type != "draw"]
    prizes = {}
    for role in ("self", "opponent"):
        selected = [e for e in parsed.events if e.event_type == "prize" and logs._actor_role(e.actor, parsed) == role]
        prizes[role] = sum(int(e.target) for e in selected) if selected else None
    return {"match": match_id, "outcome": {"W": "wins", "L": "losses"}.get(parsed.outcome, "unknown"),
            "max_observed_turn": parsed.max_turn, "opponent": opponent["classification"],
            "opponent_hypothesis": opponent["archetype_hypothesis"],
            "opponent_cards": opponent["observed_partial"]["cards"],
            "own_deck_hypothesis": own["classification"], "own_cards": own["observed_partial"]["cards"],
            "personal_deck_version": "unknown", "battle_date": "unknown",
            "explicit_prize_totals": prizes,
            "exact_opponent_60": False, "warnings": list(parsed.warnings), "evidence": evidence,
            "causal_loss_reason": "unknown"}


def group_matches(records):
    groups = {}
    for record in records:
        label = record["opponent"]["label"] or "unknown"
        g = groups.setdefault(label, {"archetype": label, "basis": "inferred_from_visible_cards",
            "wins": 0, "losses": 0, "unknown": 0, "matches": [], "observed_cards": Counter()})
        g[record["outcome"]] += 1
        g["matches"].append(record["match"])
        g["observed_cards"].update({c["name"] for c in record["opponent_cards"]})
    for g in groups.values():
        g["games"] = len(g["matches"])
        g["n"] = g["wins"] + g["losses"]
        g["observed_cards"] = [{"name": n, "games_seen": count} for n, count in sorted(
            g["observed_cards"].items(), key=lambda item: (-item[1], item[0].casefold(), item[0]))]
        g["loss_share_of_selected_games"] = g["losses"] / g["n"] if g["n"] else None
        g["recurrent_loss"] = g["losses"] >= 2
        g["causal_effect"] = "unknown"
        sample = [r for r in records if r["match"] in g["matches"]]
        g["signals"] = []
        for code, predicate, explanation in (
            ("DAMAGE_COUNTERS_REPORTED", lambda r: any(e["type"] == "damage" for e in r["evidence"]),
             "Marqueurs de dégâts consignés; attribution cible/propriétaire potentiellement ambiguë."),
            ("SHORT_OBSERVED_GAME", lambda r: r["max_observed_turn"] is not None and r["max_observed_turn"] <= 6,
             "Fin avant ou au sixième en-tête de tour observé; ne prouve pas une erreur d’installation."),
            ("PRIZE_RACE_BEHIND_IN_EXPLICIT_TRACE", lambda r: all(v is not None for v in r["explicit_prize_totals"].values())
                and r["explicit_prize_totals"]["self"] < r["explicit_prize_totals"]["opponent"],
             "Moins de Récompenses prises dans la trace explicite des deux côtés; causalité non démontrée.")):
            supporting = [r for r in sample if predicate(r)]
            if supporting:
                g["signals"].append({"code": code, "explanation": explanation,
                    "loss_games": sum(r["outcome"] == "losses" for r in supporting),
                    "win_games": sum(r["outcome"] == "wins" for r in supporting),
                    "refs": [r["match"] for r in supporting], "causal_effect": "unknown"})
    return sorted(groups.values(), key=lambda g: (-g["losses"], -g["n"], g["archetype"]))


def _new_file(path, raw):
    if path.exists():
        safe_path(path.parent, path)
        if path.stat().st_nlink != 1 or path.read_bytes() != raw:
            raise ValueError("BATCH_MEMORY_CONFLICT_NO_OVERWRITE")
        return False
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return True


def signature_mechanics(reference_db, signature, as_of):
    """Candidate descriptive text, explicitly NOT an opponent printing proof."""
    with closing(sqlite3.connect(reference_db.as_uri() + "?mode=ro&immutable=1", uri=True)) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("SELECT printing_id,name FROM catalog_translations WHERE language='en' AND status='present' "
            "AND lower(name)=? AND substr(retrieved_at,1,10)<=? ORDER BY retrieved_at DESC,printing_id DESC LIMIT 12",
            (signature, as_of)).fetchall()
        for row in rows:
            observation = deck_knowledge._observation(reference_db, con,
                {"tcgdex_ids":[row["printing_id"]],"card_name":row["name"]}, as_of)
            if observation:
                return [{"card":row["name"],"knowledge_card_id":"observed-signature-candidate",
                    "roles":deck_knowledge._roles(observation),"text":observation,
                    "scope":"candidate_printing_opponent_identity_unknown"}]
    return []


def published_variants(root, pair, family, as_of):
    """Existing PUBLIC compositions only; never alter a personal played deck."""
    if not family or family=="unknown" or family.startswith("Noyau observé"):
        return []
    groups,_,_,_=competitive._advisor_snapshot(root,pair[0],as_of)
    candidates=[g for g in groups.values() if not g["quality"] and any(
        canonical_family(o["archetype"],{family})==family for o in g["occurrences"])]
    if len(candidates)<2:
        return []
    base=min(candidates,key=lambda g:sum(competitive._quantitative_diff(g,other,60)["counts"]["removed"] for other in candidates))
    variants=[]
    for other in candidates:
        change=competitive._quantitative_diff(base,other,60)
        if 0<change["counts"]["removed"]<=10:
            variants.append((change["counts"]["removed"],other["occurrences"][0]["selector"],change))
    result=[]
    for _,selector,change in sorted(variants)[:2]:
        guide=deck_knowledge.knowledge_show(root,*pair,selector=selector,as_of=as_of,use_set_aliases=True)
        result.append({"kind":"published_same_family_variant_not_personal_swap","base_selector":base["occurrences"][0]["selector"],
            "candidate_selector":selector,"family":family,"diff":change,"export":guide["export"],
            "source":guide["source_list"],"legality":guide["preflight"]["status"],"live":"unknown",
            "hypothesis":"Tester un seul changement de ressource/séquence à la fois; aucune amélioration causale démontrée."})
    return result


def save_memory(root, report, *, as_of):
    target = safe_path(root, Path(root) / "data/local/battle-intelligence", exists=False)
    target.mkdir(parents=True, exist_ok=True)
    stable = copy.deepcopy({k: v for k, v in report.items() if k != "memory"})
    stable["persistence"].pop("imports", None)  # invocation bookkeeping is not a new observation
    key = digest(stable)
    facts = [{k: v for k, v in match.items() if k not in {
        "opponent", "opponent_hypothesis", "own_deck_hypothesis", "causal_loss_reason"}} for match in report["matches"]]
    journal = learning_loop.append_record([], record_id="batch-observations", kind="observed_game_event", recorded_at=as_of,
        payload={"provenance": "explicit-owner-folder", "version": VERSION, "matches": facts}, refs=["source:selected-folder"])
    journal = learning_loop.append_record(journal, record_id="batch-statistics", kind="derived_statistic", recorded_at=as_of,
        payload={"coverage": report["coverage"], "outcomes": report["outcomes"], "groups": report["groups"]}, refs=["batch-observations"])
    journal = learning_loop.append_record(journal, record_id="batch-test-plan", kind="test_plan", recorded_at=as_of,
        payload={"recommendations": report["recommendations"], "published_variants":report["published_same_family_variants"],
                 "causal_effect": "unknown"}, refs=["batch-observations", "batch-statistics"])
    hypothesis = {"opponent_families": [{"match": m["match"], "hypothesis": m["opponent_hypothesis"]} for m in report["matches"]],
                  "own_decks": report["own_decks"], "causal_loss_reason": "unknown"}
    refs, revises = ["batch-observations", "batch-statistics"], None
    if report.get("revision_of"):
        journal = learning_loop.append_record(journal, record_id="prior-classification", kind="hypothesis_to_test", recorded_at=as_of,
            payload={"source": "previous-local-snapshot", **report["revision_of"]}, refs=["batch-observations"])
        hypothesis["reason"] = "Public alias, French owner and evolution-engine corrections; deterministic equal-count card ordering. Earlier snapshot preserved."
        refs.append("prior-classification")
        revises = "prior-classification"
    journal = learning_loop.append_record(journal, record_id="batch-hypotheses", kind="hypothesis_to_test", recorded_at=as_of,
        payload=hypothesis, refs=refs, revises=revises)
    prefix = target / ("analysis-" + key)
    paths = [prefix.with_suffix(s) for s in (".json", ".learning.json", ".txt")]
    raws = [(json.dumps(stable, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode(),
            (json.dumps(journal, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode(), human_report(report).encode()]
    created = sum(_new_file(p, raw) for p, raw in zip(paths, raws))
    # Friendly links for the first immutable snapshot on this date. A later
    # corrected snapshot never overwrites that earlier report.
    aliases = [target / f"report-{as_of}-{VERSION}.json", target / f"report-{as_of}-{VERSION}.txt"]
    for alias, raw in zip(aliases, (raws[0], raws[2])):
        if not alias.exists():
            _new_file(alias, raw)
    return {"status": "SAVED_LOCAL" if created else "ALREADY_PRESENT_IDENTICALLY",
            "report": str(paths[0].relative_to(root)), "learning": str(paths[1].relative_to(root)),
            "text": str(paths[2].relative_to(root)), "raw_logs_saved": False}


def batch_analyze(root, *, folder, player, db, as_of, apply=False, recommendations=True,
                  cancelled=None, progress=None, complete_only=False):
    from pokemind import diagnostics
    started, journal = time.monotonic(), diagnostics.get('analysis')
    def lap(phase):
        # Phase and elapsed time only, never a log, name or deck: shows where a slow analysis waits.
        journal.info('Analyse · %s · %.1f s', phase, time.monotonic() - started)
    def checkpoint():
        if cancelled and cancelled():
            raise ValueError('BATCH_CANCELLED')
    checkpoint()
    competitive._advisor_context(as_of)
    if not isinstance(player, str) or not player.strip() or len(player) > 100 or any(not c.isprintable() for c in player):
        raise ValueError("BATCH_EXPLICIT_PLAYER_REQUIRED")
    root = Path(root).absolute()
    safe_path(root, db, expected="data/local/pokemind.sqlite3", exists=False)
    paths, refusals, total = files_in_folder(root, folder)
    folder = Path(folder).absolute()
    index, pair, source = public_context(root, as_of)
    lap('contexte public')
    checkpoint()
    persistence = database_preflight(root, db)
    personal_references = registered_decks(root, db, persistence, as_of)
    lap('base locale')
    records, seen, accepted, reasons, duplicate = [], set(), [], Counter(refusals), 0
    equivalents = set()
    valid_files, isolated_segments = 0, 0
    for file_index, path in enumerate(paths):
        checkpoint()
        if progress:
            progress(file_index, len(paths))
        try:
            text, encoding = read_selected(folder, path)
            pieces = segments(text)
            isolated_segments += max(0, len(pieces) - 1)
            file_valid = False
            for ordinal, piece in enumerate(pieces, 1):
                semantic = digest(semantic_text(piece))
                equivalent = equivalent_text_key(piece)
                if semantic in seen or equivalent in equivalents:
                    duplicate += 1
                    continue
                seen.add(semantic)
                equivalents.add(equivalent)
                try:
                    parsed = parse_selected(piece, player)
                    if complete_only and (not parsed.max_turn or parsed.outcome not in {'W', 'L'}):
                        raise ValueError('BATCH_INCOMPLETE_LOG_REFUSED')
                except ValueError as exc:
                    reasons[str(exc) if str(exc).startswith("BATCH_") else "BATCH_UNREADABLE_OR_MALFORMED"] += 1
                    continue
                record = analyze_record(parsed, index, as_of=as_of, match_id=f"M{len(records) + 1:04d}")
                record.update(semantic_identity=semantic, encoding=encoding,
                              source_relative=str(path.relative_to(folder)), source_segment=ordinal)
                records.append(record)
                accepted.append((piece, parsed))
                file_valid = True
            valid_files += int(file_valid)
        except (ValueError, OSError) as exc:
            code = str(exc) if str(exc).startswith("BATCH_") else "BATCH_UNREADABLE_OR_MALFORMED"
            reasons[code] += 1
    checkpoint()
    if progress:
        progress(len(paths), len(paths))  # every file is read; the plans below can still take a while
    lap(f'{len(paths)} fichiers lus')
    groups = group_matches(records)
    from pokemind.batch_public_research import load_public_research
    research = load_public_research(root, as_of)
    own_counts=Counter(r["own_deck_hypothesis"]["label"] or "unknown" for r in records)
    own_family=own_counts.most_common(1)[0][0] if own_counts else None
    variants=[]
    if recommendations and index:
        try:variants=published_variants(root,pair,own_family,as_of)
        except (ValueError,OSError,sqlite3.Error,KeyError):pass
    lap('familles et variantes publiques')
    recos = []
    if recommendations and index:
        targets = [g for g in groups if g["losses"] and g["archetype"] != "unknown"][:5]
        # Plans read public data only: kept for the next analysis while none of those files changes.
        shared_plans = counter_deck.public_memo(*pair, as_of)
        for number, g in enumerate(targets, 1):
            if number > 1:
                lap(f'plan contre-deck {number - 1}/{len(targets)}')
            checkpoint()
            try:
                plan = counter_deck.counter_plan(root, *pair, as_of=as_of, target=g["archetype"], use_set_aliases=True,
                                                 shared=shared_plans)
                signature = next((r["opponent"].get("signature_id") for r in records
                                  if r["opponent"]["label"] == g["archetype"] and r["opponent"].get("signature_id")), None)
                if not plan["target"]["mechanics"] and signature:
                    candidate = signature_mechanics(pair[1], signature, as_of)
                    if candidate:
                        plan["target"]["mechanics"] = candidate
                        plan["target"]["basis"] = "observed_signature_candidate_printing_not_proven"
                        plan["target"]["missing_evidence"] = ["OPPONENT_EXACT_PRINTING_UNKNOWN","CURRENT_NORMATIVE_RULES_UNKNOWN"]
                        for alternative in plan["alternatives"]:
                            alternative["target_interaction_tests"] = counter_deck._interactions(alternative["mechanics"], candidate)
                        plan["alternatives"].sort(key=lambda option:(-len(option["target_interaction_tests"]),
                            -option["evidence_quality"]["supported_mechanics"], option["switch_cost"]["copies_replaced"]))
                recos.append({"archetype": g["archetype"], "loss_match_refs": [r["match"] for r in records
                    if r["outcome"] == "losses" and r["opponent"]["label"] == g["archetype"]],
                    "kind": "testable_hypothesis_not_proven_counter", "plan": plan,
                    "personal_swaps": {"status": "BLOCKED_EXACT_PERSONAL_60_UNKNOWN", "changes": []}})
                if len(personal_references) == 1:
                    own_reference = personal_references[0]
                    from pokemind.set_code_aliases import build_aliases
                    with closing(sqlite3.connect(pair[1].as_uri() + "?mode=ro&immutable=1", uri=True)) as con:
                        con.row_factory = sqlite3.Row
                        bridge = build_aliases(con, as_of=as_of)
                        left, own_unknown = printing_map(competitive._card_map(own_reference["export"]), con, bridge)
                        changes = []
                        for alt in plan["alternatives"]:
                            right, other_unknown = printing_map(competitive._card_map(alt["export"]["text"]), con, bridge)
                            difference = competitive._quantitative_diff({"cards":left}, {"cards":right}, 60)
                            difference["identity_policy"] = "single_resolved_printing_alias_else_literal;unresolved_equivalence_unknown"
                            changes.append({"alternative_selector":alt["selector"],"archetypes":alt["archetypes"],
                                "diff":difference,"unresolved_identities":own_unknown+other_unknown})
                    recos[-1]["personal_swaps"] = {"status": "REGISTERED_REFERENCE_COMPARISON_NOT_PLAYED_VERSION",
                        "reference": {k: own_reference[k] for k in ("deck_id", "version", "scope")}, "changes": changes}
            except (ValueError, OSError, sqlite3.Error, KeyError):
                recos.append({"archetype": g["archetype"], "status": "BLOCKED_PUBLIC_EVIDENCE"})
        if targets:
            lap(f'plan contre-deck {len(targets)}/{len(targets)}')
    report = {"model_version": VERSION, "as_of": as_of, "scope": "OWNER_SELECTED_FOLDER_LOCAL_ONLY",
        "coverage": {"files_seen": len(paths) + sum(refusals.values()), "eligible_files": len(paths), "bytes": total,
            "valid_files": valid_files, "isolated_segments": isolated_segments,
            "valid": len(records), "duplicate": duplicate, "refused_or_malformed": sum(reasons.values()),
            "refusal_reasons": dict(reasons), "unknown_outcome": sum(r["outcome"] == "unknown" for r in records),
            "unknown_archetype": sum(r["opponent"]["label"] is None for r in records),
            "signature_only_archetype": sum(r["opponent"]["basis"] == "observed_signature_archetype_unresolved" for r in records)},
        "outcomes": {kind: sum(r["outcome"] == kind for r in records) for kind in ("wins", "losses", "unknown")},
        "own_decks": dict(own_counts),
        "published_same_family_variants":variants,
        "groups": groups, "matches": records, "recommendations": recos, "public_reference": source,
        "registered_deck_references": personal_references,
        "public_refresh": {"gets": research["gets"], "bytes": research["bytes"], "as_of": research["as_of"],
            "retained_facts": len(research["facts"]), "facts_by_kind": dict(Counter(f["kind"] for f in research["facts"])),
            "closed_hosts": research["closed_hosts"], "source_urls": [f["source_url"] for f in research["facts"]]} if research else None,
        "fresh_public_decks": [f for f in research["facts"] if f["kind"] == "deck60"] if research else [],
        "persistence": persistence, "release_status": "NOT_RELEASE_READY",
        "limits": ["Selected logs, not all games; no causal loss proof or guaranteed counter.",
                   "Personal deck versions, collection, credits and unobserved cards remain unknown."]}
    previous = root / f"data/local/battle-intelligence/report-{as_of}-battle-batch-v3.json"
    if not previous.exists():
        previous=root/f"data/local/battle-intelligence/report-{as_of}.json"
    if previous.exists():
        try:
            safe_path(root, previous)
            if previous.stat().st_nlink == 1 and previous.stat().st_size < 32 * 1024 * 1024:
                prior = json.loads(previous.read_text(encoding="utf-8"))
                if prior.get("scope") == report["scope"] and prior.get("model_version") != VERSION:
                    report["revision_of"] = {"model_version": prior["model_version"], "groups": prior["groups"],
                                              "outcomes": prior["outcomes"], "own_decks": prior["own_decks"]}
        except (OSError, ValueError, KeyError):
            report["revision_status"] = "PREVIOUS_SNAPSHOT_UNAVAILABLE_NOT_MODIFIED"
    if apply:
        checkpoint()
        if persistence["can_import"]:
            imports = []
            for text, _ in accepted:
                checkpoint()
                # The established observed-deck bucket is not an attested personal
                # version. No existing version is guessed from card overlap.
                try:
                    result = logs.import_battle_log(db, text, source_kind="file", reference_player=player,
                                                     parser_version="batch-explicit-player-v1")
                except (OSError, ValueError, sqlite3.Error):
                    report["persistence"]["status"] = "PARTIAL_IMPORT_BLOCKED_LOCAL_ANALYSIS_RETAINED"
                    break
                imports.append({"battle_id": result["battle_id"], "duplicate": result["duplicate"]})
            report["persistence"]["imports"] = imports
            lap(f'{len(imports)} parties importées')
        checkpoint()
        try:
            report["memory"] = save_memory(root, report, as_of=as_of)
        except (ValueError, OSError):
            report["memory"] = {"status": "BLOCKED_DERIVED_MEMORY_REVIEW_REQUIRED", "raw_logs_saved": False}
        lap('mémoire enregistrée')
    if progress:
        progress(len(paths), len(paths))
    return report


def human_report(report):
    c, outcome = report["coverage"], report["outcomes"]
    lines = [f"PokeMind — analyse réelle locale au {report['as_of']}",
        f"{c['files_seen']} fichiers; {c['valid']} matchs uniques admissibles; {c['duplicate']} doublons; "
        f"{c['refused_or_malformed']} refus/erreurs.",
        f"Victoires {outcome['wins']} / défaites {outcome['losses']} / inconnus {outcome['unknown']}.",
        f"Familles non identifiables : {c['unknown_archetype']}; signatures seules, variante d’archétype non confirmée : {c['signature_only_archetype']}; versions personnelles : unknown.",
        "Vos decks observés (hypothèses) : " + ", ".join(f"{k} ({v})" for k, v in report["own_decks"].items()),
        f"Références personnelles enregistrées exactes60 : {len(report['registered_deck_references'])}; aucune version jouée inférée.",
        "\nAdversaires à travailler — classement descriptif des journaux sélectionnés :"]
    if report.get("revision_of"):
        lines.insert(1, "Révision corrigée : alias publics, propriétaire des actions FR et moteur d’évolution distinct de l’attaquant; précédent rapport conservé.")
    for g in report["groups"][:5]:
        lines.append(f"• {g['archetype']} : {g['wins']}V/{g['losses']}D/{g['unknown']}?; n={g['n']}, "
                     f"récurrent={'oui' if g['recurrent_loss'] else 'non démontré'}; matchs {', '.join(g['matches'])}.")
        lines.append("  Cartes vues : " + ", ".join(f"{x['name']} ({x['games_seen']} matchs)" for x in g["observed_cards"][:8]))
        for signal in g["signals"]:
            lines.append(f"  Indice : {signal['explanation']} Dans {signal['loss_games']} défaites et {signal['win_games']} victoires; "
                         f"preuves {', '.join(signal['refs'])}. Ceci ne prouve pas la cause d’une défaite.")
        for match in [m for m in report["matches"] if m["match"] in g["matches"] and m["outcome"] == "losses"][:3]:
            lines.append(f"  {match['match']} : tours observés {match['max_observed_turn']}; cause causale inconnue.")
            decisive = [e for e in match["evidence"] if e["type"] in {"damage", "knockout", "prize", "use"}]
            for e in (decisive or match["evidence"])[-4:]:
                lines.append(f"    événement {e['sequence']}, tour {e['turn']}, {e['role']} : {e['text']}")
    lines.append("\nPlan d’amélioration : préserver les faits, tester une hypothèse à la fois; aucune carte responsable démontrée.")
    if report["published_same_family_variants"]:
        lines.append("\nVariantes publiées proches de votre famille observée — propositions de test, pas votre version jouée :")
        for variant in report["published_same_family_variants"]:
            lines.append(f"  {variant['family']} : modèle PUBLIC {variant['base_selector']} → variante {variant['candidate_selector']}; "
                         f"{variant['diff']['counts']['removed']} copies remplacées, total vérifié60.")
            for key,label in (("removed","Retirer du modèle PUBLIC"),("added","Ajouter au modèle PUBLIC")):
                for card in variant["diff"][key]:
                    lines.append(f"    {label} {card['quantity']} × {card['name']} {card['set']} {card['number']}.")
            lines.append("    " + variant["hypothesis"] + "; légalité actuelle/Live et équivalences d’impression à vérifier.")
            lines.extend("    Source variante : "+s["list_url"] for s in variant["source"]["observations"][:1])
    exports_shown, quotes_shown = set(), set()
    for reco in report["recommendations"]:
        plan = reco.get("plan")
        if not plan:
            continue
        lines.append(f"\nContre {reco['archetype']} — pistes de test, avantage unknown :")
        for mechanic in plan["target"]["mechanics"][:2]:
            observation = mechanic["text"]
            provenance = observation["dated_provenance"]
            url = provenance["url"]
            effects = [a.get("effect", "") for a in observation["fields"].get("attacks") or [] if isinstance(a, dict)]
            effects = [effect for effect in effects if isinstance(effect, str)]
            if not any(effects):
                effects = [observation["fields"].get("effect") or ""]
            if url not in quotes_shown and any(effects):
                excerpt = " ".join(next(e for e in effects if e).split()[:20])
                lines.append(f"  Mécanique descriptive sourcée de {mechanic['card']} : « {excerpt}… »")
                lines.append(f"    {observation['printing_id']}, {observation['language']}, au {provenance.get('retrieved_at', report['as_of'])}; {url}")
                quotes_shown.add(url)
                if mechanic.get("scope"):
                    lines.append("    Impression candidate descriptive : l’impression exacte de l’adversaire et ses errata restent à prouver.")
        lines.append("  Garder le deck : vérifier la séquence installation → recherche/pioche sourcée → Énergie → attaque; "
                     "préparer le dernier K.O. et les Récompenses selon le plateau visible. "
                     "Ne pas exposer inutilement les cibles fragiles si la mécanique citée place des dégâts sur le Banc.")
        target_roles = {role["role"] for m in plan["target"]["mechanics"] for role in m["roles"]}
        if "bench_damage" in target_roles:
            lines.append("    Priorité de test : comptabiliser les dégâts possibles sur le Banc avant de poser une cible supplémentaire; "
                         "préserver une relève sans offrir de K.O. multiples. Le journal ne prouve pas quelles cartes étaient disponibles en main.")
        if "disruption" in target_roles:
            lines.append("    Priorité de test : préparer les ressources autorisées avant le verrou/perturbation cité; "
                         "contrôler sa durée et ses exceptions au texte, pas supposer que toutes les actions sont interdites.")
        if "attack_option" in target_roles:
            lines.append("    Course aux Récompenses : comparer le prochain K.O. confirmé et les ressources de relève; "
                         "ne pas distribuer des dégâts sans plan de conclusion, et vérifier les effets qui déplacent les marqueurs.")
        personal = reco["personal_swaps"]
        selected_changes = sorted(personal.get("changes", []), key=lambda change: change["diff"]["counts"]["removed"])
        small = [change for change in selected_changes if 0 < change["diff"]["counts"]["removed"] <= 10]
        if small:
            candidate = small[0]
            lines.append(f"  Ajustement à étudier depuis votre référence enregistrée v{personal['reference']['version']} "
                         f"(non attestée dans ces matchs), vers {candidate['alternative_selector']} :")
            for direction, label in (("removed", "Retirer"), ("added", "Ajouter")):
                for card in candidate["diff"][direction]:
                    lines.append(f"    {label} {card['quantity']} × {card['name']} {card['set']} {card['number']}.")
            lines.append("    Total après comparaison :60. Équivalences de langue/réimpression, légalité actuelle et coût restent à vérifier; "
                         "ce n’est pas une modification du deck joué ni la preuve qu’une carte cause vos défaites.")
            if candidate["unresolved_identities"]:
                lines.append(f"    Identités non résolues dans les deux références :{len(candidate['unresolved_identities'])}; "
                             "les différences littérales correspondantes ne prouvent pas un changement fonctionnel.")
        elif personal["status"].startswith("BLOCKED"):
            lines.append("  Swaps personnels bloqués : aucune liste personnelle exacte60 admissible; aucune carte manquante inventée.")
        else:
            lines.append("  Les références ne démontrent pas de petit swap sûr; comparer un autre deck comme hypothèse, sans achat ni craft.")
        for option in plan["alternatives"][:2]:
            lines.append(f"  Autre base à tester : {', '.join(option['archetypes'])}, référence {option['selector']}; "
                         "60 cartes publiées, légalité présentiel/Live et possession unknown.")
            for interaction in option["target_interaction_tests"][:2]:
                lines.append("    Pourquoi tester : " + interaction["question"])
            for question in option["conditional_questions"][:2]:
                lines.append("    " + question["question"])
            sources = option["source_list"].get("observations", [])
            lines.extend("    Source : " + s["list_url"] + "; récupérée " + str(s.get("fetched_at", "date non affichée")) for s in sources[:1])
            identity = digest(option["export"]["text"])
            if identity not in exports_shown:
                lines.append(option["export"]["text"])
                exports_shown.add(identity)
            else:
                lines.append("    Liste complète60 déjà affichée plus haut; les détails restent dans le rapport JSON local.")
    fresh = [fact for fact in report["fresh_public_decks"] if fact.get("archetype")]
    if fresh:
        lines.append("\nAutres références publiques nouvellement récupérées — pas de supériorité de matchup démontrée :")
        for fact in fresh[:3]:
            lines.append(f"  {fact['archetype']} :60 cartes; {fact['source_url']}; récupérée {fact['retrieved_at']}; "
                         "auteur/date de publication et légalité Live/Standard unknown.")
        alternative = next((f for f in fresh if "dragapult" not in f["archetype"].casefold()), fresh[0])
        if digest(alternative["export"]) not in exports_shown:
            lines.append("Référence à comparer en entraînement après validation réglementaire :\n" + alternative["export"])
    lines.append("\nMémoire SQLite : " + report["persistence"]["status"] + "; aucune migration ou création de DB.")
    if report.get("memory"):
        lines.append("Rapport et Learning Loop conservés localement : " + report["memory"]["status"])
    if report["public_refresh"]:
        public = report["public_refresh"]
        lines.append(f"Mémoire PUBLIC enrichie : {public['retained_facts']} faits sourcés; {public['gets']} GET, {public['bytes']} octets. "
                     f"Arrêts fournisseurs sans retry : {public['closed_hosts']}.")
    lines.append("Petits échantillons et biais de sélection; hypothèses de familles, pas de deck adverse exact. V1 NOT_RELEASE_READY.")
    return "\n".join(lines) + "\n"
