"""Explicit, bounded PUBLIC-only campaign in a new disposable SQLite.

Never opens the owner's database. No participants, card text, IDs or paths in the
aggregate report; no image endpoints, protected APIs or Trainer Hill scraping.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pokemind.cards import CatalogApiClient, sync_cards, cards_coverage
from pokemind.meta import LimitlessApiClient, sync_meta, meta_coverage
from pokemind.updates import OfficialSourceClient

ROOT = Path(__file__).resolve().parents[1]


def run_campaign():
    base = ROOT / "data" / "local" / "public-campaigns"
    if base.is_symlink() or any(p.is_symlink() for p in base.parents):
        raise ValueError("CAMPAIGN_DIRECTORY_UNSAFE")
    base.mkdir(parents=True, exist_ok=True)
    report = {"observed_at": datetime.now(timezone.utc).isoformat(), "owner_database_opened": False,
              "private_values_disclosed": False, "trainer_hill": "BLOCKED_WITH_REASON",
              "budgets": {"tcgdex": 16, "limitless": 14, "official": 2},
              "interval_seconds": .5, "timeout_seconds": 10, "global_get_limit": 32}
    with tempfile.TemporaryDirectory(prefix="h-public-", dir=base) as raw:
        db = Path(raw) / "public.sqlite3"
        client = CatalogApiClient(16, timeout=10, interval=.5)
        result = sync_cards(db, max_requests=16, phase="balanced", client=client)
        coverage = cards_coverage(db)
        report["tcgdex"] = {"get_attempts": client.requests_made,
            "unique_printings": coverage["unique_printings"], "sets": coverage["sets_discovered"],
            "discovery_complete": coverage["discovery"]["complete"],
            "languages": {lang: {"details_present": coverage["languages"][lang]["details_present"],
                           "snapshot": coverage["languages"][lang]["index"]["snapshot"]} for lang in ("en", "fr")}}
        meta = LimitlessApiClient(14, timeout=10, interval=.5)
        result = sync_meta(db, max_requests=14, max_tournaments=3, client=meta)
        coverage = meta_coverage(db)
        report["limitless"] = {"get_attempts": meta.requests_made, "provider_remaining": meta.provider_remaining,
            "context": coverage["context"], "period": coverage["period"], "tournaments": coverage["tournaments"],
            "matches": coverage["matches"], "placements": coverage["placements"], "winrate": None}
        urls = ["https://www.pokemon.com/us/pokemon-news/2026-pokemon-tcg-standard-format-rotation-announcement",
                "https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources"]
        official = OfficialSourceClient(2, timeout=10, interval=.5, allowed_urls=urls)
        probes = []
        for url in urls:
            if official.remaining <= 0:
                break
            try:
                observation = official.probe(url)
                probes.append({"url": url, "http_status": observation["http_status"],
                               "truncated": observation["truncated"], "full_document_reviewed": False})
            except ValueError:
                probes.append({"url": url, "status": "PUBLIC_SOURCE_NOT_READABLE", "full_document_reviewed": False})
        report["official"] = {"get_attempts": official.requests_made, "probes": probes,
                              "normative_assertions_added": 0}
    report["temporary_database_removed"] = True
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-public-campaign", action="store_true")
    args = parser.parse_args()
    if not args.execute_public_campaign:
        parser.error("explicit --execute-public-campaign required; no network by default")
    print(json.dumps(run_campaign(), ensure_ascii=False, indent=2))
