"""Rebuild a bounded PUBLIC sample from its existing verified page cache only.

No GET, default owner DB, download, clipboard, migration or game interaction.
The caller must already have an authorized local PUBLIC workspace.
"""
from __future__ import annotations

import argparse
import json

from pokemind.competitive import (
    BoundedPages, INDEX_URL, competitive_summary, parse_event, parse_list,
    parse_statistics, qualify_standard, store_event,
)
from pokemind.paths import find_project_root
from pokemind.public_campaign import campaign_plan, require_public_database
from pokemind.security import neutral_exception_code


def import_cached(root, campaign, event_ids, *, as_of, sample_size=16, apply=False):
    campaign_plan(root, campaign, tcgdex_budget=1, meta_budget=0, official_budget=0)
    if (not 1 <= len(event_ids) <= 3 or len(set(event_ids)) != len(event_ids)
            or any(not event.isdigit() or int(event) < 1 for event in event_ids)
            or not 1 <= sample_size <= 45 or sample_size * len(event_ids) > 45):
        raise ValueError("COMPETITIVE_SAMPLE_SCOPE_INVALID")
    if not apply:
        return {"status": "OFFLINE_IMPORT_PLAN", "network_used": False,
                "owner_database_opened": False, "maximum_lists": sample_size * len(event_ids)}
    target = root / "data/local/public-campaigns" / ("lot-i-" + campaign)
    db = target / "public.sqlite3"
    require_public_database(root, db)
    # This adapter cannot contact the network even if future importer logic drifts.
    class OfflineOnly:
        def open(self, *args, **kwargs):
            raise ValueError("COMPETITIVE_OFFLINE_NETWORK_FORBIDDEN")
    pages = BoundedPages(target, opener=OfflineOnly())
    index = pages.cached(INDEX_URL)
    prepared = []
    for event_id in event_ids:
        url = "https://www.limitlesstcg.com/tournaments/" + event_id
        event = qualify_standard(parse_event(pages.cached(url), url, as_of=as_of), index)
        event["statistics"] = parse_statistics(pages.cached(url + "/statistics"))
        if event["statistics"]["denominator"] != event["published_result_rows"]:
            raise ValueError("COMPETITIVE_DENOMINATOR_CONFLICT")
        event["statistics"]["source_url"] = url + "/statistics"
        event["selection"] = f"first_{sample_size}_published_placements; canonical_list_urls_may_repeat"
        items = []
        for row in event["placements"][:sample_size]:
            record = next(r for r in pages.report["requests"] if r["url"] == row["list_url"])
            items.append({**row, "deck_text": parse_list(pages.cached(row["list_url"])),
                          "page_sha256": record["sha256"], "fetched_at": record["fetched_at"]})
        prepared.append((event, items))
    for event, items in prepared:
        store_event(root, db, event, items)
    return competitive_summary(root, db)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--event", required=True, action="append")
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--sample-size", type=int, default=16)
    parser.add_argument("--apply-offline", action="store_true")
    args = parser.parse_args()
    try:
        result = import_cached(find_project_root(), args.campaign, args.event,
                               as_of=args.as_of, sample_size=args.sample_size, apply=args.apply_offline)
        print(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, StopIteration) as exc:
        print(json.dumps({"ok": False, "error_code": neutral_exception_code(exc, "COMPETITIVE")}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
