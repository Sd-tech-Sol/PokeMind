"""Manual PUBLIC-only full descriptive catalog, acquired in fixed-query pages."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pokemind.cards import CatalogError, cards_coverage, _record_sync_metadata
from pokemind.catalog_batch_store import (initialize_batch_tables, pending_language_ids,
                                        store_page, store_selection, verify_head)
from pokemind.catalog_snapshots import record_failure
from pokemind.database import connect_writable, initialize_schema, utc_now
from pokemind.paths import find_project_root
from pokemind.public_campaign import campaign_plan, require_public_database
from pokemind.recovery import _ProcessLock, _atomic_bytes, _canonical, _redirected
from pokemind.security import neutral_exception_code
from pokemind.tcgdex_batch import BatchClient


def collect(root, campaign, *, execute=False, create=False, maximum_requests=50_000,
            discovery_bytes=0, initial_requests=0, initial_body_bytes=0, client=None):
    campaign_plan(root, campaign, tcgdex_budget=1, meta_budget=0, official_budget=0)
    if (type(discovery_bytes) is not int or not 0 <= discovery_bytes < 134_217_728
            or type(maximum_requests) is not int or not 1 <= maximum_requests <= 50_000):
        raise CatalogError("PUBLIC_BATCH_ENVELOPE_INVALID")
    report = {"schema_version": 1, "status": "DRY_RUN", "campaign": campaign,
              "source": "TCGdex public GraphQL fixed read-only queries",
              "owner_database_opened": False, "old_campaign_reused": False,
              "images_requested": False, "maximum_requests": maximum_requests,
              "maximum_body_bytes": 134_217_728, "discovery_bytes": discovery_bytes,
              "http_requests": initial_requests, "body_bytes_read": initial_body_bytes,
              "coverage": None, "head_probes_passed": False,
              "limits": ["Observed paginated catalog, not an atomic worldwide total or legality/Live proof.",
                         "Null single-resource results confirm language absence, not an HTTP404.",
                         "GraphQL does not expose every REST field: level, weight, pricing, updated and set abbreviation omitted."]}
    if not execute:
        return report
    target = root / "data/local/public-campaigns" / ("lot-i-" + campaign)
    if create:
        target.mkdir(parents=True, exist_ok=False)
        _atomic_bytes(target / "PUBLIC_ONLY.json", _canonical({
            "kind": "pokemind_public_only_lot_i", "campaign": campaign, "schema_version": 1,
        }), overwrite=False)
    db = target / "public.sqlite3"
    require_public_database(root, db)
    report_path = target / "batch-report.json"
    if not create:
        if (_redirected(report_path) or not report_path.is_file() or report_path.stat().st_nlink != 1
                or report_path.stat().st_size > 2 * 1024 * 1024):
            raise CatalogError("PUBLIC_BATCH_EXISTING_RUN_UNATTESTED")
        old = json.loads(report_path.read_text(encoding="utf-8"))
        if old.get("status") == "OBSERVED_CATALOG_COMPLETE" and cards_coverage(db)["complete"]:
            return {**old, "status": "CACHE_HIT_COMPLETE", "new_http_requests": 0,
                    "network_used": False, "database_modified": False}
        raise CatalogError("PUBLIC_BATCH_EXISTING_RUN_CLOSED")
    responses = target / "responses"
    responses.mkdir()
    report["status"] = "IN_PROGRESS"
    report["network_used"] = False

    def save():
        _atomic_bytes(report_path, _canonical(report))

    def checkpoint(actual):
        report.update(http_requests=actual.requests_made, body_bytes_read=actual.body_bytes_read,
                      total_body_bytes=discovery_bytes + actual.body_bytes_read,
                      network_used=actual.requests_made > initial_requests)
        save()

    actual = client or BatchClient(maximum_requests=maximum_requests,
        maximum_body_bytes=134_217_728 - discovery_bytes,
        requests_made=initial_requests, body_bytes_read=initial_body_bytes, checkpoint=checkpoint)
    actual.checkpoint = checkpoint
    checkpoint(actual)

    def receipt(label):
        raw = getattr(actual, "last_raw", None)
        if raw is not None:
            _atomic_bytes(responses / (label + ".json"), raw, overwrite=False)

    with _ProcessLock(target / ".public-campaign.lock"):
        connection = connect_writable(db)
        active_scope = None
        try:
            initialize_schema(connection)
            initialize_batch_tables(connection)
            for kind in ("sets", "cards"):
                for language in ("en", "fr"):
                    active_scope = f"{kind}:{language}"
                    page = 1
                    while True:
                        before = actual.requests_made
                        rows = actual.page(kind, language, page)
                        receipt(f"{kind}-{language}-{page:04}")
                        done = store_page(connection, kind, language, page, rows,
                                          actual.last_evidence, request_attempts=actual.requests_made - before)
                        if page % 20 == 0 or done:
                            report["coverage"] = cards_coverage(db, _connection=connection)
                            checkpoint(actual)
                            print(json.dumps({"scope": active_scope, "page": page,
                                "requests": actual.requests_made, "bytes": actual.body_bytes_read,
                                "printings": report["coverage"]["unique_printings"],
                                "complete_scan": done}), flush=True)
                        if done:
                            break
                        page += 1
            # Never infer a missing translation from membership alone. Explicit
            # exact-ID queries independently resolve every remaining language pair.
            for kind in ("sets", "cards"):
                for language in ("en", "fr"):
                    active_scope = f"{kind}:{language}"
                    pending = pending_language_ids(connection, kind, language)
                    for offset in range(0, len(pending), 30):
                        selected = actual.missing(kind, language, pending[offset:offset + 30])
                        receipt(f"missing-{kind}-{language}-{offset:05}")
                        store_selection(connection, kind, language, selected, actual.last_evidence)
                    print(json.dumps({"scope": active_scope, "resolved_missing_pairs": len(pending),
                                      "requests": actual.requests_made}), flush=True)
            for kind in ("sets", "cards"):
                for language in ("en", "fr"):
                    active_scope = f"{kind}:{language}"
                    rows = actual.page(kind, language, 1)
                    receipt(f"head-{kind}-{language}")
                    verify_head(connection, kind, language, rows)
            report["head_probes_passed"] = True
            report["coverage"] = cards_coverage(db, _connection=connection)
            report["status"] = "OBSERVED_CATALOG_COMPLETE" if report["coverage"]["complete"] else "COVERAGE_INCOMPLETE_STOP"
        except Exception as exc:
            connection.rollback()
            code = neutral_exception_code(exc, "CATALOG_BATCH")
            report.update(status="SOURCE_STOP", error=code, last_http_status=actual.last_http_status,
                          blocked_reason=actual.blocked_reason, failed_scope=active_scope)
            if active_scope:
                with connection:
                    record_failure(connection, active_scope, "discovery", utc_now())
        finally:
            _record_sync_metadata(connection, actual.requests_made,
                                  success=bool(connection.execute("SELECT 1 FROM catalog_printings LIMIT 1").fetchone()),
                                  error=report.get("error"))
            report["coverage"] = cards_coverage(db, _connection=connection)
            report["maximum_requests_respected"] = actual.requests_made <= maximum_requests
            report["maximum_bytes_respected"] = discovery_bytes + actual.body_bytes_read <= 134_217_728
            checkpoint(actual)
            connection.close()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--execute-authorized-public-collection", action="store_true")
    parser.add_argument("--maximum-requests", type=int, default=50_000)
    parser.add_argument("--discovery-bytes", type=int, default=0)
    parser.add_argument("--initial-requests", type=int, default=0)
    parser.add_argument("--initial-body-bytes", type=int, default=0)
    args = parser.parse_args()
    report = collect(find_project_root(), args.campaign, execute=args.execute_authorized_public_collection,
        create=args.create, maximum_requests=args.maximum_requests, discovery_bytes=args.discovery_bytes,
        initial_requests=args.initial_requests, initial_body_bytes=args.initial_body_bytes)
    print(json.dumps({key: value for key, value in report.items() if key != "coverage"}, indent=2))
    return 0 if report["status"] in {"DRY_RUN", "OBSERVED_CATALOG_COMPLETE", "CACHE_HIT_COMPLETE"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
