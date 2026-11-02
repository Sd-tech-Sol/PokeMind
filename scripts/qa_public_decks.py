"""Manual offline QA using existing PUBLIC readers; no discovery or cache writes.

The caller must authorize both databases, their PUBLIC markers and the source
ledger/pages referenced by the competitive cache. Output contains public
aggregate evidence, never raw lists, card texts or database fingerprints.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from pokemind import competitive, counter_deck, deck_knowledge, deck_library, public_deck_preflight
from pokemind.public_campaign import public_database_path, require_public_database
from pokemind.recovery import _redirected


def _fingerprint(path):
    if (any(_redirected(p) for p in (path, *path.absolute().parents))
            or not path.is_file() or path.stat().st_nlink != 1):
        raise ValueError("PUBLIC_QA_SOURCE_UNSAFE")
    before = path.stat()
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").digest()
    after = path.stat()
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
    if identity(before) != identity(after):
        raise ValueError("PUBLIC_QA_SOURCE_CHANGED_DURING_READ")
    return identity(after), digest


def _protected_files(root, db, reference_db):
    # Validate both lexical namespaces before any filesystem access.
    for path in (db, reference_db):
        public_database_path(root, path)
    paths = set()
    for path in (db, reference_db):
        require_public_database(root, path)
        if any(Path(str(path) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
            raise ValueError("PUBLIC_QA_SIDECAR_PRESENT_STOP")
        paths.update((path, path.parent / "PUBLIC_ONLY.json"))
    ledger = db.parent / "requests.json"
    _fingerprint(ledger)
    if ledger.stat().st_size > competitive.MAX_RESPONSE:
        raise ValueError("PUBLIC_QA_LEDGER_TOO_LARGE")
    records = json.loads(ledger.read_text(encoding="utf-8"))["requests"]
    if not isinstance(records, list) or len(records) > competitive.MAX_GETS:
        raise ValueError("PUBLIC_QA_LEDGER_INVALID")
    paths.add(ledger)
    for record in records:
        digest = record.get("sha256")
        if record.get("state") != "complete":
            continue
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("PUBLIC_QA_LEDGER_INVALID")
        # Exact content-addressed paths only; no directory listing or glob.
        competitive.cached_page(db.parent, record)
        paths.add(db.parent / "pages" / (digest + ".body"))
    return {p: _fingerprint(p) for p in paths}


def assess(root, db, reference_db, *, as_of):
    competitive._advisor_context(as_of)
    protected = _protected_files(root, db, reference_db)
    inventory = deck_library.library_list(root, db, as_of=as_of)
    if inventory["issues"]:
        raise ValueError("PUBLIC_QA_SOURCE_ISSUES_STOP")
    groups, _, _, placements = competitive._advisor_snapshot(root, db, as_of)
    lists, guides, unresolved = [], [], set()
    for group in groups.values():
        for occurrence in group["occurrences"]:
            event, rank = occurrence["selector"].split(":")
            text = competitive.competitive_export(root, db, event, int(rank))
            if (competitive.parse_deck_export(text).total_cards != 60 or
                    competitive._composition_id(competitive._card_map(text)) != group["composition_id"]):
                raise ValueError("PUBLIC_QA_EXPORT_CONFLICT")
            lists.append({**occurrence, "composition_id": group["composition_id"], "reparsed_cards": 60})
    for entry in inventory["library"]:
        guide = deck_knowledge.knowledge_show(root, db, reference_db,
            selector=entry["selector"], as_of=as_of, use_set_aliases=True)
        live = public_deck_preflight.competitive_preflight(root, db, reference_db,
            selectors=[entry["selector"]], as_of=as_of, format="standard", platform="live",
            use_set_aliases=True)["options"][0]
        rows = guide["card_role"]
        missing = [r for r in rows if not r["observed_card_text"]]
        unresolved.update((r["card_name"], r["set_code"], r["collector_number"]) for r in missing)
        guides.append({"selector": entry["selector"], "archetypes": guide["archetype"],
            "composition_id": entry["composition_id"], "rows": len(rows),
            "dated_text_rows": len(rows) - len(missing),
            "resolved_copies": sum(r["quantity"] for r in rows if r["identity_status"] == "resolved"),
            "in_person": guide["preflight"]["status"], "live": live["status"],
            "identity": guide["preflight"]["counts"]["identity"],
            "sections": sorted({c["section"] for c in guide["strategic_claim"]}),
            "text_dates": sorted({r["observed_card_text"]["dated_provenance"]["retrieved_at"]
                                  for r in rows if r["observed_card_text"]}),
            "missing_text_by_set": dict(Counter(r["set_code"] for r in missing))})
    families = {competitive._family(label) for row in guides for label in row["archetypes"]}
    targets = [label for label in ("Dragapult", "Basic Box", "Hydrapple", "Dhelmise") if label in families]
    counters = []
    for target in targets:
        plan = counter_deck.counter_plan(root, db, reference_db, as_of=as_of,
            target=target, use_set_aliases=True)
        if any(competitive.parse_deck_export(o["export"]["text"]).total_cards != 60
               for o in plan["alternatives"]):
            raise ValueError("PUBLIC_QA_COUNTER_EXPORT_CONFLICT")
        counters.append({"target": target, "exports60": len(plan["alternatives"]),
            "interaction_tests": sum(len(o["target_interaction_tests"]) for o in plan["alternatives"]),
            "target_is_exact_opponent_deck": plan["target"]["is_exact_opponent_deck"],
            "matchup_advantage": plan["matchup_advantage"]})
    if len(lists) != placements:
        raise ValueError("PUBLIC_QA_PLACEMENT_COUNT_CONFLICT")
    for path, fingerprint in protected.items():
        if _fingerprint(path) != fingerprint:
            raise ValueError("PUBLIC_QA_CACHE_MUTATED_STOP")
    for path in (db, reference_db):
        if any(Path(str(path) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
            raise ValueError("PUBLIC_QA_NEW_SIDECAR_STOP")
    return {"scope": "CODEX_LOCAL_REPORTED_PUBLIC_CACHE_QA", "as_of": as_of,
        "observed_at": datetime.now(timezone.utc).isoformat(), "events": inventory["events"],
        "placements": len(lists), "compositions": len(guides), "families": len(families),
        "exports60": len(lists), "lists": lists, "guides": guides, "counter_plans": counters,
        "text_rows": sum(g["dated_text_rows"] for g in guides),
        "row_denominator": sum(g["rows"] for g in guides), "unique_missing_text_identities": len(unresolved),
        "in_person": dict(Counter(g["in_person"] for g in guides)),
        "live": dict(Counter(g["live"] for g in guides)),
        "protected_files": len(protected), "cache_bytes_and_metadata_unchanged": True,
        "directory_scan_performed": False, "provider_gets": 0, "network_used": False,
        "owner_database_opened": False, "release_status": "NOT_RELEASE_READY"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--reference-db", required=True, type=Path)
    parser.add_argument("--as-of", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report = assess(root, args.db.absolute(), args.reference_db.absolute(), as_of=args.as_of)
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
