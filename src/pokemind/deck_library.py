"""Searchable views over already cached PUBLIC compositions; no writes/network."""
from __future__ import annotations

import re
from contextlib import closing

from pokemind import competitive, rules
from pokemind.catalog_batch_store import verified_payload
from pokemind.database import connect_readonly
from pokemind.public_campaign import require_public_database
from pokemind.public_deck_preflight import _reference_schema
from pokemind.set_code_aliases import build_aliases, payload_source


def library_list(root, db, *, as_of, archetype=None, event=None, since=None, until=None, version=None):
    competitive._advisor_context(as_of)
    for value in (since, until):
        if value is not None:
            competitive._advisor_context(value)
    if (since and until and since > until) or (until and until > as_of):
        raise ValueError("DECK_LIBRARY_DATE_RANGE_INVALID")
    if event is not None and not re.fullmatch(r"[1-9][0-9]*", event):
        raise ValueError("DECK_LIBRARY_EVENT_INVALID")
    if version is not None and not re.fullmatch(r"[0-9a-f]{64}", version):
        raise ValueError("DECK_LIBRARY_COMPOSITION_VERSION_REQUIRED")
    groups, events, issues, placements = competitive._advisor_snapshot(root, db, as_of)
    selected = []
    for group in groups.values():
        if version is not None and group["composition_id"] != version:
            continue
        occurrences = [o for o in group["occurrences"] if
                       (archetype is None or archetype.casefold() in o["archetype"].casefold())
                       and (event is None or o["event_id"] == event)
                       and (since is None or o["date"] >= since) and (until is None or o["date"] <= until)]
        if not occurrences:
            continue
        view = {**group, "occurrences": occurrences}
        public = competitive._group_public(view)
        public.update(selector=occurrences[0]["selector"], total_cards=60,
                      show_command="meta deck-knowledge", export_command="meta competitive-export",
                      compare_command="meta competitive-compare", legality="unknown", live_availability="unknown")
        selected.append(public)
    selected.sort(key=lambda row: (row["archetypes"], row["composition_id"]))
    return {**competitive._advisor_context(as_of), "status": "PARTIAL_WITH_EVIDENCE" if issues else "OK",
            "filters": {"archetype": archetype, "event": event, "since": since, "until": until, "version": version},
            "library": selected, "matching_compositions": len(selected),
            "matching_placements": sum(x["placements"] for x in selected),
            "available_compositions": len(groups), "available_placements": placements,
            "events": list(events.values()), "issues": issues, "read_only": True,
            "interpretation": "dated_selected_placements_not_matchup_strength_ranking"}


def reference_index(root, db, *, as_of, reference_db=None):
    """Names on real PUBLIC reference lists; aliases only from verified payloads."""
    groups, events, issues, placements = competitive._advisor_snapshot(root, db, as_of)
    aliases = {}
    if reference_db is not None:
        require_public_database(root, reference_db)
        _reference_schema(reference_db)
        with closing(connect_readonly(reference_db)) as con:
            bridge = build_aliases(con, as_of=as_of)
            for group in groups.values():
                for key, card in group["cards"].items():
                    if key in aliases:
                        continue
                    aliases[key] = set()
                    identity = rules._resolve_structure_identity(con, {"card_name": card["name"], "set_code": card["set"],
                        "collector_number": card["number"]}, set_aliases=bridge)
                    if len(identity["ids"]) != 1:
                        continue
                    entity = identity["ids"][0]
                    for row in con.execute("SELECT * FROM catalog_translations WHERE printing_id=? AND status='present'", (entity,)):
                        language = row["language"]
                        if language not in {"en", "fr"} or not row["retrieved_at"] or row["retrieved_at"][:10] > as_of:
                            continue
                        stale = con.execute(f"SELECT detail_stale_{language} FROM catalog_printings WHERE tcgdex_id=?", (entity,)).fetchone()[0]
                        payload = verified_payload(con, "cards", entity, language, row["payload_sha256"])
                        if (payload and not stale and payload.get("id") == entity and payload_source(con, "cards", entity, language)
                                and rules._normalized_name(payload.get("name")) == rules._normalized_name(row["name"])):
                            aliases[key].add(rules._normalized_name(row["name"]))
    result = []
    for group in groups.values():
        if group["quality"]:
            continue
        names = {rules._normalized_name(c["name"]) for c in group["cards"].values()}
        for key in group["cards"]:
            names.update(aliases.get(key, set()))
        labels = {competitive._family(o["archetype"]) for o in group["occurrences"]}
        if len(labels) == 1:
            result.append({"archetype": next(iter(labels)), "names": sorted(names),
                           "composition": competitive._group_public(group),
                           "selector": group["occurrences"][0]["selector"], "total_cards": 60,
                           "cards": [dict(c, aliases=sorted(aliases.get(key, set()) | {rules._normalized_name(c['name'])}))
                                     for key, c in group['cards'].items()],
                           "export": competitive_export_for_group(root, db, group)})
    return {"references": result, "as_of": as_of, "issues": issues,
            "sampled_placements": placements, "events": len(events),
            "scope": "public_reference_lists_not_opponent_exact_deck"}


def competitive_export_for_group(root, db, group):
    row = group['occurrences'][0]
    return competitive.competitive_export(root, db, row['event_id'], row['placement'])


def human_library(report):
    print(f"Bibliothèque PUBLIC au {report['as_of']} : {report['matching_compositions']} compositions / "
          f"{report['matching_placements']} placements retenus, sur {report['available_compositions']} / {report['available_placements']}.")
    for row in report["library"]:
        print(f"{row['selector']} — {', '.join(row['archetypes'])}; 60/60; version {row['composition_id']}")
        print(f"  Dates {row['date_range']}; placements {row['placement_range']} / n={row['placements']}; légalité/Live : unknown.")
        print("  Sources : " + ", ".join(row["source_urls"]))
    print("Fiche : meta deck-knowledge --selector ... ; comparaison : meta competitive-compare --left ... --right ...")
    print("Export : meta competitive-export --event ... --placement ... ; mêmes DB PUBLIC explicites. Aucun classement de force.")
