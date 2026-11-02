"""Bounded, resumable PUBLIC-only workspace. No caller-supplied database path."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from pokemind.cards import CatalogApiClient, sync_cards, cards_coverage
from pokemind.meta import LimitlessApiClient, sync_meta, meta_coverage
from pokemind.recovery import _ProcessLock, _atomic_bytes, _canonical, _redirected
from pokemind.security import neutral_exception_code
from pokemind.updates import OfficialSourceClient
from pokemind.database import connect_readonly
from pokemind.public_card_selection import selection_plan, sync_public_selection


URLS = (
    "https://www.pokemon.com/us/pokemon-news/2026-pokemon-tcg-standard-format-rotation-announcement",
    "https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources",
)
MODERN_URLS = ("https://play.pokemon.com/en-us/resources/documents/",
               "https://play.pokemon.com/en-us/resources/rules/")


def _public_database_only(db):
    """Defense in depth: reject populated owner/unknown tables, not just a marker.

    This does not cryptographically certify arbitrary catalog/metadata contents.
    Never copy an owner database into a PUBLIC workspace.
    """
    if not db.exists():
        return
    connection = connect_readonly(db)
    try:
        names = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for name in names:
            if name == "metadata" or name.startswith(("sqlite_", "catalog_", "official_", "meta_", "public_source_", "knowledge_update_")):
                continue
            # Empty FTS5 indexes still contain internal config/header rows.
            if name in {"sections_fts_data", "sections_fts_idx", "sections_fts_docsize", "sections_fts_config"}:
                continue
            quoted = '"' + name.replace('"', '""') + '"'
            if connection.execute("SELECT 1 FROM " + quoted + " LIMIT 1").fetchone():
                raise ValueError("PUBLIC_CAMPAIGN_OWNER_OR_UNKNOWN_DATA_BLOCKED")
    finally:
        connection.close()


def public_database_path(root: Path, db: Path) -> Path:
    """Validate only the declared namespace, without inspecting any file."""
    root, db = root.absolute(), db.absolute()
    campaign = db.parent.name.removeprefix("lot-i-")
    if (db.name != "public.sqlite3" or db.parent.parent != root / "data/local/public-campaigns"
            or db.parent.name != "lot-i-" + campaign
            or not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", campaign)):
        raise ValueError("PUBLIC_UPDATE_WORKSPACE_REQUIRED")
    return db


def require_public_database(root: Path, db: Path) -> None:
    """Validate a marked PUBLIC workspace before any unattended update.

    No default owner database, creation, migration, or network request here.
    A marker alone is insufficient: existing owner/unknown data is rejected.
    """
    db = public_database_path(root, db)
    if any(_redirected(path) for path in (db, *db.parents)):
        raise ValueError("PUBLIC_UPDATE_DIRECTORY_UNSAFE")
    marker = db.parent / "PUBLIC_ONLY.json"
    if (_redirected(marker) or not marker.is_file() or marker.stat().st_nlink != 1
            or marker.stat().st_size > 1024):
        raise ValueError("PUBLIC_UPDATE_WORKSPACE_UNATTESTED")
    campaign = db.parent.name.removeprefix("lot-i-")
    if (db.parent.name != "lot-i-" + campaign
            or not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", campaign)
            or json.loads(marker.read_text(encoding="utf-8")) != {
                "kind": "pokemind_public_only_lot_i", "campaign": campaign, "schema_version": 1,
            }):
        raise ValueError("PUBLIC_UPDATE_WORKSPACE_UNATTESTED")
    for candidate in (db, *(Path(str(db) + suffix) for suffix in ("-wal", "-shm", "-journal"))):
        if _redirected(candidate) or (candidate.exists() and (
                not candidate.is_file() or candidate.stat().st_nlink != 1)):
            raise ValueError("PUBLIC_UPDATE_DATABASE_ALIAS_BLOCKED")
    _public_database_only(db)


def campaign_plan(root, campaign, *, phase="index", tcgdex_budget=12, meta_budget=8, official_budget=2,
                  card_ids=None, languages="en,fr"):
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", campaign) or phase not in {"index", "details", "balanced", "refresh"}:
        raise ValueError("PUBLIC_CAMPAIGN_ARGUMENT_INVALID")
    if any(type(v) is not int or v < 0 for v in (tcgdex_budget, meta_budget, official_budget)) or not 1 <= tcgdex_budget + meta_budget + official_budget <= 24 or official_budget > 2:
        raise ValueError("PUBLIC_CAMPAIGN_BUDGET_INVALID")
    selection = None
    if card_ids is not None:
        if phase != "details" or not tcgdex_budget or meta_budget or official_budget:
            raise ValueError("PUBLIC_SELECTION_REQUIRES_TCGDEX_DETAILS_ONLY")
        selection = selection_plan(card_ids, languages)
    target = root / "data/local/public-campaigns" / ("lot-i-" + campaign)
    if any(_redirected(p) for p in (target, *target.absolute().parents)) or not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("PUBLIC_CAMPAIGN_DIRECTORY_UNSAFE")
    return {"mode": "dry_run", "network_used": False, "owner_database_opened": False,
            "campaign": campaign, "phase": phase, "maximum_gets": tcgdex_budget + meta_budget + official_budget,
            "budgets": {"tcgdex": tcgdex_budget, "limitless": meta_budget, "official": official_budget},
            "interval_seconds": .5, "timeout_seconds": 10, "resumable": True,
            "provider_total": "unknown_non_atomic_pagination", "trainer_hill": "BLOCKED_WITH_REASON",
            **({"selection": selection} if selection is not None else {})}


def run_campaign(root, campaign, *, create=False, execute=False, phase="index", tcgdex_budget=12, meta_budget=8, official_budget=2, official_scope="legacy",
                 card_ids=None, languages="en,fr", recheck_absent=False, response_limit=None, cancelled=None):
    if official_scope not in {"legacy", "modern"}:
        raise ValueError("PUBLIC_CAMPAIGN_OFFICIAL_SCOPE_INVALID")
    if recheck_absent and card_ids is None:
        raise ValueError("PUBLIC_SELECTION_RECHECK_REQUIRES_CARD_IDS")
    plan = campaign_plan(root, campaign, phase=phase, tcgdex_budget=tcgdex_budget,
                         meta_budget=meta_budget, official_budget=official_budget,
                         card_ids=card_ids, languages=languages)
    if card_ids is not None:
        plan["selection"]["recheck_absent"] = bool(recheck_absent)
    if not execute:
        return plan
    target = root / "data/local/public-campaigns" / ("lot-i-" + campaign)
    marker = target / "PUBLIC_ONLY.json"
    expected = {"kind": "pokemind_public_only_lot_i", "campaign": campaign, "schema_version": 1}
    if create:
        target.mkdir(parents=True, exist_ok=False)
        _atomic_bytes(marker, _canonical(expected), overwrite=False)
    if _redirected(marker) or not marker.is_file() or marker.stat().st_nlink != 1 or marker.stat().st_size > 1024 or json.loads(marker.read_text(encoding="utf-8")) != expected:
        raise ValueError("PUBLIC_CAMPAIGN_WORKSPACE_UNATTESTED")
    db = target / "public.sqlite3"
    if _redirected(db) or (db.exists() and db.stat().st_nlink != 1):
        raise ValueError("PUBLIC_CAMPAIGN_DATABASE_ALIAS_BLOCKED")
    report = {**plan, "mode": "executed", "observed_at": datetime.now(timezone.utc).isoformat(),
              "get_attempts": 0, "normative_assertions_added": 0, "winrate": None}
    with _ProcessLock(target / ".public-campaign.lock"):
        _public_database_only(db)
        if tcgdex_budget:
            client = CatalogApiClient(tcgdex_budget, timeout=10, interval=.5, stop_on_access_denial=True)
            if card_ids is not None:
                result = sync_public_selection(db, plan["selection"], client, recheck_absent=recheck_absent)
            else:
                result = sync_cards(db, max_requests=tcgdex_budget, phase="index" if phase == "refresh" else phase,
                                    refresh_index=phase == "refresh", client=client)
            coverage = cards_coverage(db)
            report["tcgdex"] = {"get_attempts": client.requests_made, "error": result.get("error"),
                "last_http_status": getattr(client, "last_http_status", None),
                "blocked_reason": result.get("blocked_reason") or getattr(client, "blocked_reason", None), "details": result.get("details", {}),
                "stopped_reason": result["stopped_reason"],
                "languages": {lang: {key: coverage["languages"][lang][key] for key in
                    ("details_present", "statuses", "possibly_stale_details")} for lang in ("en", "fr")},
                "sets_union": coverage["sets_discovered"], "printing_union": coverage["unique_printings"],
                "snapshots": {f"{kind}:{lang}": coverage["languages"][lang][section]["snapshot"]
                    for kind, section in (("sets", "sets"), ("cards", "index")) for lang in ("en", "fr")},
                **({key: result[key] for key in ("selection", "cache_hits", "pending_pairs_before",
                    "pending_pairs_after", "selection_resolved", "index_scan_performed", "limits")}
                   if card_ids is not None else {})}
            report["get_attempts"] += client.requests_made
        if meta_budget:
            limits = {'max_response_bytes':response_limit, 'cancelled':cancelled} if response_limit is not None else {}
            client = LimitlessApiClient(meta_budget, timeout=10, interval=.5, stop_on_access_denial=True, **limits)
            result = sync_meta(db, max_requests=meta_budget, max_tournaments=1, client=client)
            coverage = meta_coverage(db)
            report["limitless"] = {"get_attempts": client.requests_made, "error": result.get("error"),
                "blocked_reason": getattr(client, "blocked_reason", None),
                **{key: coverage[key] for key in ("context", "period", "tournaments", "matches", "placements")}}
            report["get_attempts"] += client.requests_made
            if response_limit is not None:
                report['response_bytes_received'] = client.bytes_received
        if official_budget:
            urls = URLS if official_scope == "legacy" else MODERN_URLS
            client = OfficialSourceClient(official_budget, timeout=10, interval=.5, allowed_urls=list(urls), stop_on_access_denial=True)
            probes = []
            for url in urls[:official_budget]:
                if client.remaining <= 0:
                    break
                try:
                    evidence = client.probe(url)
                    probes.append({"url": url, **{k: evidence[k] for k in ("http_status", "truncated", "content_sha256")},
                                   "full_document_reviewed": False, "assertions_verified": False})
                except ValueError as exc:
                    probes.append({"url": url, "error": neutral_exception_code(exc, "OFFICIAL")})
                    if getattr(client, "blocked_reason", None):
                        break
            report["official"] = {"get_attempts": client.requests_made, "probes": probes,
                                  "blocked_reason": getattr(client, "blocked_reason", None)}
            report["get_attempts"] += client.requests_made
        report["network_used"] = report["get_attempts"] > 0
        report["maximum_gets_respected"] = report["get_attempts"] <= plan["maximum_gets"]
        _atomic_bytes(target / "latest-report.json", _canonical(report))
    return report


def main():
    from pokemind.paths import find_project_root
    parser = argparse.ArgumentParser(description="Campagne publique cumulable; aucune base personnelle, aucun réseau par défaut.")
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--phase", default="index", choices=("index", "details", "balanced", "refresh"))
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--execute-public-campaign", action="store_true")
    parser.add_argument("--tcgdex-budget", type=int, default=12)
    parser.add_argument("--meta-budget", type=int, default=8)
    parser.add_argument("--official-budget", type=int, default=2)
    parser.add_argument("--official-scope", choices=("legacy", "modern"), default="legacy")
    parser.add_argument("--card-ids", help="sélection publique bornée d'identifiants; exige details, budgets meta/officiel zéro")
    parser.add_argument("--lang", default="en,fr", help="langues de la sélection: en,fr; aucune traduction de repli")
    parser.add_argument("--recheck-absent", action="store_true", help="sélection: redemander les traductions déclarées absentes")
    args = parser.parse_args()
    try:
        result = run_campaign(find_project_root(), args.campaign, create=args.create,
            execute=args.execute_public_campaign, phase=args.phase, tcgdex_budget=args.tcgdex_budget,
            meta_budget=args.meta_budget, official_budget=args.official_budget, official_scope=args.official_scope,
            card_ids=args.card_ids, languages=args.lang, recheck_absent=args.recheck_absent)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error_code": neutral_exception_code(exc, "CAMPAIGN")}))
        return 2
