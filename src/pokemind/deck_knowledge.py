"""Dated PUBLIC deck knowledge views: observations, inferences and test plans.

No owner fallback, network, writes or generated replacement card text. Detailed
reports belong in the caller's isolated PUBLIC workspace, never in Git fixtures.
"""
from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import urlsplit

from pokemind import cards, competitive, public_deck_preflight, rules
from pokemind.catalog_batch_store import verified_payload
from pokemind.database import connect_readonly
from pokemind.set_code_aliases import payload_source


VERSION = "deck-knowledge-v1"
SCHEMA_VERSION = 1
ROLE_PATTERNS = {
    "draw": r"\bdraw (?:[0-9]+|a |an |cards|until)|look at the top|piochez",
    "search": r"search your deck|cherchez dans votre deck",
    "energy_acceleration": r"attach (?:a |up to |any number|[0-9]).*energy|attachez.*[ée]nergie",
    "recovery": r"discard pile.*(?:hand|deck)|(?:hand|deck).*discard pile|d[ée]fausse.*main",
    "disruption": r"opponent.*(?:hand|can't|cannot|discard)|adversaire.*(?:main|ne peut)",
    "switch": r"switch.*(?:active|benched)|[ée]changez.*actif",
    "bench_damage": r"damage counters.*benched|benched.*damage|d[ée]g[âa]ts.*banc",
    "healing": r"\bheal\b|soignez",
}


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def _observation(reference_db, connection, identity, as_of):
    """Only matched, present, fresh, hash-checked native texts support strategy."""
    if len(identity["tcgdex_ids"]) != 1:
        return None
    entity = identity["tcgdex_ids"][0]
    for language in ("en", "fr"):
        row = connection.execute("SELECT * FROM catalog_translations WHERE printing_id=? AND language=?",
                                 (entity, language)).fetchone()
        if (not row or row["status"] != "present" or not row["retrieved_at"]
                or row["retrieved_at"][:10] > as_of or urlsplit(row["source_url"] or "").scheme != "https"
                or urlsplit(row["source_url"] or "").hostname not in {"github.com", "api.tcgdex.net"}):
            continue
        payload = verified_payload(connection, "cards", entity, language, row["payload_sha256"])
        provenance = payload_source(connection, "cards", entity, language) if payload else None
        if (not payload or not provenance or payload.get("id") != entity
                or rules._normalized_name(payload.get("name")) != rules._normalized_name(identity["card_name"])
                or rules._normalized_name(row["name"]) != rules._normalized_name(payload.get("name"))):
            continue
        observed = cards.show_card(reference_db, entity, language)
        if observed["possibly_stale"] or not observed["provenance"]["url"]:
            continue
        fields = {key: payload.get(key) for key in ("name", "category", "stage", "evolveFrom", "energyType",
                                                   "trainerType", "suffix", "effect", "abilities", "attacks")}
        return {"kind": "fact", "meaning": "observed_catalog_text_not_official_rule_or_errata_certification",
                "printing_id": entity, "language": language, "fields": fields,
                "dated_provenance": {**observed["provenance"], **provenance, "url": provenance["source_url"], "provider": "TCGdex",
                                     "authority": "descriptive_catalog", "as_of": as_of},
                "community_french_used": False}
    return None


def _roles(observation):
    if observation is None:
        return []
    fields = observation["fields"]
    result = []
    for field in ("effect", "abilities", "attacks"):
        value = fields[field]
        if not value:
            continue
        # Keep independent effects and sentences apart. A once-per-turn limit
        # must not hide an earlier draw; an opponent mentioned in a condition
        # must not acquire a discard effect from a different sentence/ability.
        effects = [value] if isinstance(value, str) else [
            item.get("effect", "") for item in value if isinstance(item, dict)]
        fragments = [part for effect in effects if isinstance(effect, str)
                     for part in re.split(r"[.!?\n]+", effect) if part.strip()]
        for role, pattern in ROLE_PATTERNS.items():
            def supports(fragment):
                if role in {"draw", "search", "energy_acceleration", "healing"} and re.search(
                    r"can['’]t|cannot|does not|don['’]t|ne peut|ne pouvez", fragment, re.I):
                    return False
                return re.search(pattern, fragment, re.I) is not None

            if any(supports(fragment) for fragment in fragments):
                result.append({"role": role, "kind": "inference", "support_field": field,
                               "method": "conservative_text_pattern_hint_not_action_validation",
                               "condition": "Lire les restrictions du texte cité et vérifier le plateau réel.",
                               "source": observation["dated_provenance"]})
    if fields["attacks"]:
        result.append({"role": "attack_option", "kind": "fact", "support_field": "attacks",
                       "condition": "Option imprimée; coût et conditions à vérifier avant de la choisir.",
                       "source": observation["dated_provenance"]})
    return result


def _guide(card_rows, list_source):
    claims = []

    def add(section, kind, text, support, conditions):
        claims.append({"claim_id": "claim-" + str(len(claims) + 1), "section": section, "kind": kind,
                       "text": text, "support": support, "conditions": conditions,
                       "dated_provenance": list_source})

    observed = [r for r in card_rows if r["observed_card_text"]]
    by_name = {rules._normalized_name(r["observed_card_text"]["fields"]["name"]): r for r in observed}
    chains = []
    for row in observed:
        predecessor = row["observed_card_text"]["fields"]["evolveFrom"]
        if predecessor and rules._normalized_name(predecessor) in by_name:
            parent = by_name[rules._normalized_name(predecessor)]
            chains.append({"from": parent["card_name"], "to": row["card_name"],
                           "support": [row["knowledge_card_id"], parent["knowledge_card_id"]]})
    if chains:
        add("setup", "inference", "Préparer les maillons de ces évolutions avant de compter sur leurs attaques : " +
            "; ".join(x["from"] + " → " + x["to"] for x in chains),
            sorted({i for x in chains for i in x["support"]}),
            ["Disponibilité en main et sur le Banc inconnue; délais et exceptions d'évolution à vérifier."])
    for role, section, text in (
        ("draw", "opening", "Si ce moteur est disponible, comparer son usage avant une recherche; garder les restrictions du talent ou de l'effet."),
        ("search", "opening", "Choisir une recherche selon le maillon d'installation ou la ressource réellement manquante, après lecture de ses cibles et de son coût."),
        ("energy_acceleration", "resources", "Préparer les Énergies et cibles permises par ces effets avant de planifier une attaque; ne pas compter deux fois une ressource."),
        ("recovery", "midgame", "Réserver une récupération pour les ressources effectivement en défausse; vérifier destination et quantité avant de payer un coût."),
        ("bench_damage", "prizes", "Planifier les marqueurs ou dégâts de Banc à partir des PV et protections visibles; viser un futur K.O. reste conditionnel."),
        ("disruption", "counterplay", "Tester le moment de perturbation après avoir assuré son installation; l'effet sur la main adverse cachée reste inconnu."),
        ("switch", "counterplay", "Comparer les options de changement d'Actif aux coûts de retraite et cibles autorisées, selon le plateau visible."),
    ):
        support = [r["knowledge_card_id"] for r in observed if any(x["role"] == role for x in r["card_role"])]
        if support:
            names = [r["card_name"] for r in observed if r["knowledge_card_id"] in support]
            add(section, "inference", text + " Cartes concernées : " + ", ".join(names) + ".", support,
                ["Conseil conditionnel dérivé des champs cités, sans mesure de matchup."])
    attacks = []
    for row in observed:
        for attack in row["observed_card_text"]["fields"]["attacks"] or []:
            attacks.append({"card": row["card_name"], "attack": attack, "support": row["knowledge_card_id"]})
    if attacks:
        add("win_condition", "inference", "Construire des K.O. à partir des attaques effectivement présentes dans cette liste; adapter la cible au plateau visible et aux ressources restantes.",
            sorted({x["support"] for x in attacks}), ["Aucun plan gagnant garanti; plateau, défense adverse et Récompenses inconnus."])
        if chains:
            add("sequencing", "hypothesis_to_test", "Comparer l'usage des talents disponibles avant une évolution, puis vérifier le coût de l'attaque envisagée. Aucun enchaînement n'est garanti par la seule présence de ces cartes.",
                sorted({i for x in chains for i in x["support"]} | {x["support"] for x in attacks}),
                ["La fenêtre du talent, les cibles et les délais doivent être contrôlés dans les textes et règles applicables."])
        add("attacks", "inference", "Comparer les attaques ci-dessous et leurs coûts au plateau et aux Énergies disponibles; préparer l'attaquant suivant avant d'engager toutes les ressources.",
            sorted({x["support"] for x in attacks}), ["Aucune attaque exécutable, suite garantie ou victoire déduite de la seule liste."])
        add("prizes", "hypothesis_to_test", "Tester un plan de K.O. et de fin de partie fondé sur ces attaques; recalculer les seuils après chaque changement du plateau.",
            sorted({x["support"] for x in attacks}), ["PV, protections, Récompenses restantes et récompense par K.O. non attestés ici."])
    if observed:
        add("mistakes", "inference", "Éviter de confondre présence d'une carte et effet utilisable : vérifier coûts, cibles, délais, limites par tour et ressources restantes dans les textes cités.",
            [r["knowledge_card_id"] for r in observed], ["Aucune erreur personnelle observée dans ce lot."])
        add("test_plan", "hypothesis_to_test", "À l'entraînement volontaire, noter si l'installation, les coûts d'attaque et le relais d'attaquant ont pu être assurés; comparer plusieurs parties avant de changer la liste.",
            [r["knowledge_card_id"] for r in observed], ["Aucune partie importée; aucune statistique ou causalité actuelle."])
    return claims, chains, attacks


def knowledge_show(root, db, reference_db, *, selector, as_of, use_set_aliases=False):
    report = public_deck_preflight.competitive_preflight(
        root, db, reference_db, as_of=as_of, format="standard", platform="in_person",
        selectors=[selector], use_set_aliases=use_set_aliases)
    option = report["options"][0]
    event, place = selector.split(":")
    text = competitive.competitive_export(root, db, event, int(place))
    # Reuse the existing 60-card parser/serializer and source-checked composition.
    if competitive._composition_id(competitive._card_map(text)) != option["source"]["composition_id"]:
        raise ValueError("DECK_KNOWLEDGE_EXPORT_SOURCE_CONFLICT")
    source = {"provider": "Limitless", "authority": "observed_tournament_list_not_normative",
              "as_of": as_of, "observations": option["list_observations"]}
    connection = connect_readonly(reference_db)
    try:
        card_rows = []
        for row in option["cards"]:
            observation = _observation(reference_db, connection, row, as_of)
            card_rows.append({"knowledge_card_id": "card-" + str(row["ordinal"]),
                              **{key: row[key] for key in ("quantity", "card_name", "set_code", "collector_number",
                                                          "tcgdex_ids", "identity_status")},
                              "observed_card_text": observation, "card_role": _roles(observation),
                              "uncertainty": [] if observation else ["MATCHED_DATED_NATIVE_CARD_TEXT_MISSING"],
                              "identity_evidence": row["structure_identity"], "legality_evidence": row["verdict"]})
    finally:
        connection.close()
    claims, chains, attacks = _guide(card_rows, source)
    missing = [r["knowledge_card_id"] for r in card_rows if r["observed_card_text"] is None]
    groups, _, _, _ = competitive._advisor_snapshot(root, db, as_of)
    selected = competitive._select_group(groups, selector)
    own_families = {competitive._family(label) for label in option["source"]["archetypes"]}
    related, seen_families = [], set()
    for other in sorted(groups.values(), key=lambda g: (g["occurrences"][0]["archetype"], g["composition_id"])):
        family = competitive._family(other["occurrences"][0]["archetype"])
        if other["quality"] or family in own_families or family in seen_families:
            continue
        related.append({"kind": "public_alternative_to_test", "source": competitive._group_public(other),
                        "selector": other["occurrences"][0]["selector"],
                        "construction_diff_copies": competitive._quantitative_diff(selected, other, 1)["counts"],
                        "matchup_advantage": "unknown", "interpretation": "construction_difference_not_strength"})
        seen_families.add(family)
        if len(related) == 3:
            break
    result = {"schema_version": SCHEMA_VERSION, "model_version": VERSION, "as_of": as_of,
              "archetype": option["source"]["archetypes"],
              "variant": {"composition_id": option["source"]["composition_id"], "selector": selector},
              "source_list": source, "dated_provenance": source,
              "related_public_options": related,
              "card_role": card_rows, "strategic_claim": claims, "evolution_links": chains,
              "attack_options": attacks,
              "resources": {"published_energy_copies": sum(x.quantity for x in competitive.parse_deck_export(text).cards
                                                            if x.card_type == "energy"),
                            "resolved_energy_copies": sum(r["quantity"] for r in option["cards"]
                                                          if rules._normalized_name(r["structure_identity"]["category"]) == "energy"),
                            "energy_identity_scope": "published_section_separate_from_resolved_catalog_category"},
              "uncertainty": {"missing_card_text": missing, "normative_errata_coverage": "unknown",
                              "matchups": "unknown", "winrate": "unknown", "strength_ranking": None,
                              "live_availability": "unknown", "ownership": "unknown", "credits": "unknown",
                              "craftability": "unknown", "hidden_game_state": "unknown",
                              "selection_bias": "published_selected_placements_not_random_players_or_matches",
                              "sample_events": report["events"], "sampled_placements": report["sampled_placements"]},
              "preflight": {key: option[key] for key in ("status", "counts", "blockers", "structure_validation")},
              "set_code_bridge": report["set_code_bridge"],
              "export": {"text": text, "total_cards": 60, "format": "PTCGL",
                         "command": f"meta competitive-export --event {event} --placement {place} --db <same-PUBLIC-db>",
                         "historical_serializer_status": "FIELD_VALIDATED", "clipboard_used": False,
                         "live_legality": "unknown"},
              "status": "PARTIAL_WITH_EVIDENCE", "read_only": True, "network_used": False,
              "owner_database_opened": False, "database_mutated": False, "release_status": "NOT_RELEASE_READY"}
    result["version_sha256"] = _digest(result)
    return result


def human_knowledge(report):
    print(f"Deck Knowledge PUBLIC — {', '.join(report['archetype'])} / {report['variant']['selector']}")
    print(f"Au {report['as_of']} : {report['status']}; version {report['version_sha256'][:12]}")
    print("Source : " + ", ".join(sorted({o['list_url'] for o in report['source_list']['observations']})))
    print(f"Présentiel : {report['preflight']['status']}; Live, possession et matchups : unknown.")
    for row in report["card_role"]:
        roles = ", ".join(sorted({r["role"] for r in row["card_role"]})) or "unknown"
        print(f"  {row['quantity']} {row['card_name']} {row['set_code']} {row['collector_number']} : {roles}")
        observation = row["observed_card_text"]
        if observation:
            p = observation["dated_provenance"]
            print(f"    Texte {observation['language']} TCGdex, {p['retrieved_at']} : {p['url']}")
            fields = observation["fields"]
            if fields["effect"]:
                print("    Effet observé : " + fields["effect"])
            for ability in fields["abilities"] or []:
                print(f"    Talent observé {ability.get('name', '')} : {ability.get('effect', 'unknown')}")
    for claim in report["strategic_claim"]:
        print(f"[{claim['kind']} / {claim['section']}] {claim['text']}")
        print("  Conditions : " + " ".join(claim["conditions"]))
    for item in report["attack_options"]:
        attack = item["attack"]
        print(f"  {item['card']} — {attack.get('name')}: coût {attack.get('cost')}; dégâts {attack.get('damage', 'unknown')}; {attack.get('effect', '')}")
    for alternative in report["related_public_options"]:
        print(f"Alternative publique à tester : {alternative['selector']} / {', '.join(alternative['source']['archetypes'])}; "
              f"diff copies {alternative['construction_diff_copies']}; avantage de matchup unknown.")
    print(f"Textes manquants : {len(report['uncertainty']['missing_card_text'])}; détails sourcés et champs observés : --json.")
    print("Export 60/60 pour copie manuelle :\n" + report["export"]["text"])
