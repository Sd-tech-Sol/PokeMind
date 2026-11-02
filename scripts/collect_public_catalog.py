"""Manual, fresh PUBLIC-only catalog acquisition with one cumulative envelope.

No old workspace can be reopened. Interrupted/error runs require owner review,
not an automatic retry. No scheduler, personal DB, images or other provider.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from urllib.request import HTTPRedirectHandler, build_opener

from pokemind.cards import CatalogApiClient, NetworkFailure, sync_cards
from pokemind.paths import find_project_root
from pokemind.public_campaign import campaign_plan, require_public_database
from pokemind.recovery import _ProcessLock, _atomic_bytes, _canonical
from pokemind.security import neutral_exception_code


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # urllib's default redirect handler drains the body without a read cap.
        fp.close()
        raise NetworkFailure("TCGDEX_REDIRECT_STOPPED")


def collect(root, campaign, *, maximum_gets=50_000, maximum_body_bytes=134_217_728,
            execute=False):
    if (type(maximum_gets) is not int or not 1 <= maximum_gets <= 50_000
            or type(maximum_body_bytes) is not int or not 1 <= maximum_body_bytes <= 134_217_728):
        raise ValueError("PUBLIC_CATALOG_ENVELOPE_INVALID")
    # Reuse the namespace/reparse validation without relaxing the old 24-GET API.
    campaign_plan(root, campaign, tcgdex_budget=1, meta_budget=0, official_budget=0)
    report = {"schema_version": 1, "campaign": campaign,
              "status": "DRY_RUN", "maximum_gets": maximum_gets,
              "maximum_body_bytes": maximum_body_bytes, "get_attempts": 0,
              "body_bytes_read": 0, "minimum_interval_seconds": .5,
              "network_used": False, "owner_database_opened": False,
              "old_campaign_reused": False, "images_collected": False,
              "batches": [], "coverage": None}
    if not execute:
        return report
    target = root / "data/local/public-campaigns" / ("lot-i-" + campaign)
    target.mkdir(parents=True, exist_ok=False)
    _atomic_bytes(target / "PUBLIC_ONLY.json", _canonical({
        "kind": "pokemind_public_only_lot_i", "campaign": campaign, "schema_version": 1,
    }), overwrite=False)
    db = target / "public.sqlite3"
    report["status"] = "IN_PROGRESS"
    save = lambda: _atomic_bytes(target / "collection-report.json", _canonical(report))
    save()
    with _ProcessLock(target / ".public-campaign.lock"):
        phase = "index"
        try:
            while report["get_attempts"] < maximum_gets and report["body_bytes_read"] < maximum_body_bytes:
                require_public_database(root, db)
                budget = min(100, maximum_gets - report["get_attempts"])
                if report["get_attempts"]:
                    time.sleep(.5)  # also between client instances
                client = CatalogApiClient(budget, timeout=10, interval=.5,
                    maximum_attempts=1, stop_on_access_denial=True,
                    maximum_body_bytes=maximum_body_bytes - report["body_bytes_read"],
                    opener=build_opener(NoRedirect()))
                try:
                    result = sync_cards(db, max_requests=budget, phase=phase, client=client)
                finally:
                    report["get_attempts"] += client.requests_made
                    report["body_bytes_read"] += client.body_bytes_read
                    report["network_used"] = report["get_attempts"] > 0
                    save()
                report["coverage"] = result["coverage"]
                report["batches"].append({"phase": phase,
                    "get_attempts": client.requests_made, "body_bytes_read": client.body_bytes_read,
                    "last_http_status": client.last_http_status, "error": result["error"],
                    "blocked_reason": client.blocked_reason, "stopped_reason": result["stopped_reason"]})
                save()
                print(json.dumps({"status": "PROGRESS", "phase": phase,
                    "get_attempts": report["get_attempts"], "body_bytes_read": report["body_bytes_read"],
                    "unique_printings": result["coverage"]["unique_printings"],
                    "details": {lang: result["coverage"]["languages"][lang]["details_present"] for lang in ("en", "fr")},
                    "error": result["error"]}), flush=True)
                if result["error"] or client.blocked_reason:
                    report["status"] = ("BODY_BUDGET_STOP" if result["error"] == "TCGDEX_BODY_BUDGET_EXHAUSTED" else "SOURCE_STOP")
                    break
                coverage = result["coverage"]
                if coverage["complete"]:
                    report["status"] = "OBSERVED_CACHE_COMPLETE"
                    break
                if phase == "index" and coverage["discovery"]["complete"]:
                    if not coverage["current_indexes_complete"]:
                        report["status"] = "INDEX_MEMBERSHIP_INCONCLUSIVE_STOP"
                        break
                    phase = "details"
                elif result["stopped_reason"] == "nothing_pending" or client.requests_made == 0:
                    report["status"] = "NO_PROGRESS_STOP"
                    break
            else:
                report["status"] = "ENVELOPE_STOP"
        except Exception as exc:
            report["status"] = "LOCAL_ERROR_STOP"
            report["error"] = neutral_exception_code(exc, "CAMPAIGN")
        finally:
            report["maximum_gets_respected"] = report["get_attempts"] <= maximum_gets
            report["maximum_body_bytes_respected"] = report["body_bytes_read"] <= maximum_body_bytes
            save()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--maximum-gets", type=int, default=50_000)
    parser.add_argument("--maximum-body-bytes", type=int, default=134_217_728)
    parser.add_argument("--execute-authorized-public-collection", action="store_true")
    args = parser.parse_args()
    report = collect(find_project_root(), args.campaign, maximum_gets=args.maximum_gets,
                     maximum_body_bytes=args.maximum_body_bytes,
                     execute=args.execute_authorized_public_collection)
    print(json.dumps({k: v for k, v in report.items() if k not in {"coverage", "batches"}}, indent=2))
    return 0 if report["status"] in {"DRY_RUN", "OBSERVED_CACHE_COMPLETE", "ENVELOPE_STOP", "BODY_BUDGET_STOP"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
