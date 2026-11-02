"""Manual offline import of a reviewed, pinned PUBLIC TCGdex literal snapshot."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pokemind.cards import CatalogError, _canonical_sha256, _record_sync_metadata, cards_coverage
from pokemind.catalog_batch_store import initialize_batch_tables, store_page, store_selection
from pokemind.database import connect_writable, fts_checks, initialize_schema, utc_now
from pokemind.paths import find_project_root
from pokemind.public_campaign import campaign_plan, require_public_database
from pokemind.recovery import _ProcessLock, _atomic_bytes, _canonical, _redirected
from pokemind.security import neutral_exception_code
from pokemind.tcgdex_snapshot import Snapshot


def _receipt(snapshot, kind, language, ids, purpose):
    objects = {}
    for entity_id in ids:
        path = snapshot.path(kind, entity_id, language)
        candidates = snapshot.card_paths[entity_id] if kind == "cards" else [path]
        objects[entity_id] = {"source_url": snapshot.url(path), "git_blob": snapshot.blobs[path],
            "available_in_language": snapshot.available(kind, entity_id, language),
            "candidate_objects": [{"source_url": snapshot.url(p), "git_blob": snapshot.blobs[p]}
                                  for p in candidates]}
    evidence = {"operation": "literal_snapshot", "source_commit": snapshot.commit,
        "source_url": f"https://github.com/tcgdex/cards-database/tree/{snapshot.commit}/data",
        "tree_sha256": snapshot.tree_sha256, "language": language, "kind": kind,
        "purpose": purpose, "source_objects": objects,
        "absence_basis": "No card name or referenced set name in this language in the complete pinned literal source; no HTTP404 inferred."}
    evidence["query_sha256"] = _canonical_sha256(evidence)
    return evidence


def import_snapshot(root, source, campaign, *, execute=False, create=False):
    campaign_plan(root, campaign, tcgdex_budget=1, meta_budget=0, official_budget=0)
    report = {"schema_version": 1, "status": "DRY_RUN", "campaign": campaign,
        "network_used": False, "new_http_requests": 0, "database_modified": False,
        "owner_database_opened": False, "old_campaign_reused": False,
        "source": "Official pinned TCGdex literal data; upstream code never executed",
        "limits": ["Complete for the selected data/ source tree at the pinned commit, not a worldwide total.",
                   "Missing language names/fields remain unavailable; no English-to-French substitution.",
                   "No pricing, images, Live support, reprint equivalence or format legality inferred."]}
    if not execute:
        return report
    target = root / "data/local/public-campaigns" / ("lot-i-" + campaign)
    report_path = target / "snapshot-report.json"
    db = target / "public.sqlite3"
    if not create:
        require_public_database(root, db)
        if (_redirected(report_path) or not report_path.is_file() or report_path.stat().st_nlink != 1
                or report_path.stat().st_size > 2 * 1024 * 1024):
            raise CatalogError("PUBLIC_SNAPSHOT_EXISTING_RUN_UNATTESTED")
        old = json.loads(report_path.read_text(encoding="utf-8"))
        if old.get("status") == "PINNED_CATALOG_COMPLETE" and cards_coverage(db)["complete"]:
            return {**old, "status": "CACHE_HIT_COMPLETE", "database_modified": False}
        raise CatalogError("PUBLIC_SNAPSHOT_EXISTING_RUN_CLOSED")

    # All source integrity, linking and payload validation precedes DB creation.
    snapshot = Snapshot(root, source)
    payloads, memberships = {}, {}
    for kind, entities in (("sets", snapshot.sets), ("cards", snapshot.cards)):
        for language in ("en", "fr"):
            values = {}
            for entity_id in sorted(entities):
                if snapshot.available(kind, entity_id, language):
                    values[entity_id] = (snapshot.set_payload if kind == "sets" else
                                         snapshot.card_payload)(entity_id, language)
            payloads[kind, language] = values
            memberships[kind + ":" + language] = {"present": len(values),
                "absent": len(entities) - len(values), "membership_sha256": _canonical_sha256(list(values))}
    identities = [snapshot.identity(i) for i in sorted(snapshot.cards)]
    target.mkdir(parents=True, exist_ok=False)
    _atomic_bytes(target / "PUBLIC_ONLY.json", _canonical({"kind": "pokemind_public_only_lot_i",
        "campaign": campaign, "schema_version": 1}), overwrite=False)
    require_public_database(root, db)
    _atomic_bytes(target / "TCGDEX_MIT_LICENSE.txt", snapshot.license.encode("utf-8"), overwrite=False)
    report.update(status="IN_PROGRESS", source_commit=snapshot.commit,
        source_tree_sha256=snapshot.tree_sha256, verified_source_files=snapshot.source_files,
        source_card_objects=sum(len(v) for v in snapshot.card_paths.values()),
        unique_printings=len(snapshot.cards), sets=len(snapshot.sets), membership=memberships)
    _atomic_bytes(report_path, _canonical(report))
    with _ProcessLock(target / ".public-campaign.lock"):
        connection = connect_writable(db)
        try:
            initialize_schema(connection)
            initialize_batch_tables(connection)
            now = utc_now()
            # Explicit identities include objects with neither EN nor FR names.
            with connection:
                for entity_id, path in snapshot.sets.items():
                    value = snapshot.modules[path].value
                    connection.execute("""INSERT INTO catalog_sets
                        (tcgdex_id,series_id,card_count_official,discovered_at,updated_at) VALUES (?,?,?,?,?)""",
                        (entity_id, value["serie"].get("id"), value["cardCount"]["official"], now, now))
            for kind, entities in (("sets", snapshot.sets), ("cards", snapshot.cards)):
                if kind == "cards":
                    with connection:
                        for identity in identities:
                            connection.execute("""INSERT OR IGNORE INTO catalog_printings
                                (tcgdex_id,set_id,local_id,category,hp,stage,regulation_mark,rarity,
                                 illustrator,types_json,brief_source_url,discovered_at,updated_at,brief_retrieved_at)
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (*identity, now, now, now))
                for language in ("en", "fr"):
                    values = payloads[kind, language]
                    ids = list(values)
                    page, offset = 1, 0
                    while True:
                        group = ids[offset:offset + 100]
                        done = store_page(connection, kind, language, page, [values[i] for i in group],
                            _receipt(snapshot, kind, language, group, f"page:{page}"), request_attempts=0)
                        if done:
                            break
                        page, offset = page + 1, offset + 100
                    absent = sorted(set(entities) - set(values))
                    for offset in range(0, len(absent), 30):
                        group = absent[offset:offset + 30]
                        store_selection(connection, kind, language, dict.fromkeys(group),
                            _receipt(snapshot, kind, language, group, "explicit_literal_absence"))
                    print(json.dumps({"scope": kind + ":" + language,
                        "present": len(ids), "absent": len(absent), "new_http_requests": 0}), flush=True)
            with connection:
                connection.execute("INSERT INTO metadata VALUES (?,?)", ("catalog_pinned_source", json.dumps({
                    "repository": "tcgdex/cards-database", "commit": snapshot.commit,
                    "tree_sha256": snapshot.tree_sha256, "verified_files": snapshot.source_files,
                    "card_objects": report["source_card_objects"], "imported_at": utc_now()})))
            _record_sync_metadata(connection, 0, success=True)
            report["coverage"] = cards_coverage(db, _connection=connection)
            report["integrity_check"] = connection.execute("PRAGMA integrity_check").fetchone()[0]
            report["foreign_key_errors"] = len(connection.execute("PRAGMA foreign_key_check").fetchall())
            report["fts"] = fts_checks(connection)
            healthy = report["coverage"]["complete"] and report["integrity_check"] == "ok" and not report["foreign_key_errors"]
            healthy = healthy and all(item["status"] == "ok" for item in report["fts"].values())
            report["status"] = "PINNED_CATALOG_COMPLETE" if healthy else "VALIDATION_INCOMPLETE_STOP"
            report["database_modified"] = True
        except Exception as exc:
            connection.rollback()
            report.update(status="OFFLINE_IMPORT_STOP", error=neutral_exception_code(exc, "CATALOG_SNAPSHOT"))
        finally:
            connection.close()
            _atomic_bytes(report_path, _canonical(report))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--execute-reviewed-public-snapshot", action="store_true")
    args = parser.parse_args()
    report = import_snapshot(find_project_root(), args.source, args.campaign, create=args.create,
                             execute=args.execute_reviewed_public_snapshot)
    print(json.dumps({k: v for k, v in report.items() if k not in {"coverage", "fts"}}, indent=2))
    return 0 if report["status"] in {"DRY_RUN", "PINNED_CATALOG_COMPLETE", "CACHE_HIT_COMPLETE"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
