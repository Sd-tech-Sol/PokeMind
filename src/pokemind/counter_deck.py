"""Read-only PUBLIC alternatives and conditional experiments, never matchup odds."""
from __future__ import annotations

from pokemind import competitive, deck_knowledge, deck_library, recommendations, rules
from pokemind.decks import parse_deck_export


def _mechanics(guide):
    return [{"card": row["card_name"], "knowledge_card_id": row["knowledge_card_id"],
             "roles": row["card_role"], "text": row["observed_card_text"]}
            for row in guide["card_role"] if row["observed_card_text"]]


def _interactions(own, target):
    questions = []
    for our_role, their_roles, text in (
        ("disruption", {"draw", "search"}, "Tester le moment d'une perturbation face au moteur de pioche/recherche cité; vérifier coûts, cibles et reconstruction adverse."),
        ("healing", {"bench_damage", "attack_option"}, "Comparer les soins permis aux dégâts observables de l'attaque citée; vérifier cibles, quantités et fenêtre avant le K.O."),
        ("switch", {"attack_option"}, "Tester le relais d'Actif face aux attaques citées; les cibles, coûts de retraite et Énergies réellement disponibles restent à contrôler."),
        ("energy_acceleration", {"attack_option"}, "Tester si l'accélération citée prépare le coût de notre attaque avant l'engagement adverse; aucun gain de vitesse acquis."),
        ("draw", {"disruption"}, "Tester la reconstruction après la perturbation adverse citée; les cartes effectivement piochées restent inconnues."),
    ):
        ours = [m for m in own if any(r["role"] == our_role for r in m["roles"])]
        theirs = [m for m in target if any(r["role"] in their_roles for r in m["roles"])]
        if ours and theirs:
            questions.append({"kind": "hypothesis_to_test", "question": text,
                "own_support": [m["knowledge_card_id"] for m in ours],
                "target_proxy_support": [m["knowledge_card_id"] for m in theirs],
                "conditions": "Textes datés descriptifs; vérifier restrictions, règles/errata et plateau. Proxy ≠ adversaire exact.",
                "advantage": "unknown"})
    return questions


def _structure(guide):
    parsed = parse_deck_export(guide["export"]["text"])
    return {"published_copies": {kind: sum(c.quantity for c in parsed.cards if c.card_type == kind)
                                 for kind in ("pokemon", "trainer", "energy")},
            "catalog_stages": {stage: sum(r["quantity"] for r in guide["card_role"]
                               if r["observed_card_text"] and r["observed_card_text"]["fields"]["stage"] == stage)
                               for stage in ("Basic", "Stage1", "Stage2")},
            "missing_text_copies": sum(r["quantity"] for r in guide["card_role"] if not r["observed_card_text"]),
            "energy_colors_consistency_prize_trade": "unknown"}


def counter_plan(root, db, reference_db, *, as_of, target, options=4, base=None, use_set_aliases=False):
    competitive._advisor_context(as_of)
    if not isinstance(target, str) or not target.strip() or len(target) > 100:
        raise ValueError("COUNTER_EXPLICIT_TARGET_ARCHETYPE_REQUIRED")
    if type(options) is not int or not 1 <= options <= 4:
        raise ValueError("COUNTER_OPTIONS_1_TO_4")
    if db is None or reference_db is None:
        raise ValueError("COUNTER_EXPLICIT_PUBLIC_DATABASES_REQUIRED")
    # Same composition verification, medoid selection and printing exact diffs.
    inventory = deck_library.library_list(root, db, as_of=as_of)
    try:
        shortlist = competitive.competitive_shortlist(root, db, as_of=as_of, options=max(2, options), base=base)
        selected = shortlist["options"][:options]
    except ValueError as exc:
        if options != 1 or str(exc) != "COMPETITIVE_ADVISOR_DISTINCT_ALTERNATIVE_MISSING":
            raise
        # A lone verified baseline is still a useful explicit one-option plan.
        groups, _, _, _ = competitive._advisor_snapshot(root, db, as_of)
        candidates = [g for g in groups.values() if not g["quality"] and
                      competitive._family(g["occurrences"][0]["archetype"]) == "Dragapult"]
        reference = competitive._select_group(groups, base) if base else min(candidates, key=lambda g: (
            sum(competitive._quantitative_diff(g, other, 1)["counts"]["removed"] for other in candidates), g["composition_id"]))
        selected = [competitive._group_public(reference, detail=True)]
    guides = {o["reference"]: deck_knowledge.knowledge_show(root, db, reference_db,
        selector=o["reference"], as_of=as_of, use_set_aliases=use_set_aliases) for o in selected}
    baseline = selected[0]["reference"]
    target_rows = [r for r in inventory["library"] if any(
        rules._normalized_name(competitive._family(label)) == rules._normalized_name(target)
        for label in r["archetypes"])]
    target_guide = None
    if target_rows:
        selector = min(target_rows, key=lambda r: r["composition_id"])["selector"]
        target_guide = guides.get(selector) or deck_knowledge.knowledge_show(root, db, reference_db,
            selector=selector, as_of=as_of, use_set_aliases=use_set_aliases)
    target_mechanics = _mechanics(target_guide) if target_guide else []
    alternatives = []
    base_structure = _structure(guides[baseline])
    for item in selected:
        selector = item["reference"]
        guide = guides[selector]
        mechanics = _mechanics(guide)
        # Full exact differences, including every printing/copy, never a top-N truncation.
        diff = competitive.competitive_compare(root, db, baseline, selector, as_of=as_of, limit=60)["changes"]
        structure = _structure(guide)
        roles = sorted({r["role"] for m in mechanics for r in m["roles"]})
        interactions = _interactions(mechanics, target_mechanics)
        questions = [{"kind": "hypothesis_to_test", "mechanic": role,
            "question": "Tester ce moteur selon les restrictions du texte cité et le plateau visible contre " + target + ".",
            "support": [m["knowledge_card_id"] for m in mechanics if any(r["role"] == role for r in m["roles"])],
            "potential_benefit": "conditional_resource_or_timing_option_not_matchup_advantage",
            "matchup_advantage": "unknown"} for role in roles]
        alternatives.append({"selector": selector, "archetypes": guide["archetype"],
            "decision": "keep_published_base_and_test_play" if selector == baseline else "test_published_alternative",
            "source": {k: item[k] for k in ("composition_id", "reference", "archetypes", "placements",
                "placement_range", "events", "date_range", "source_urls", "quality")},
            "source_list": guide["source_list"], "export": guide["export"],
            "construction_changes": diff, "structure": structure,
            "published_type_delta": {k: structure["published_copies"][k] - base_structure["published_copies"][k]
                                     for k in structure["published_copies"]},
            "switch_cost": {"copies_replaced": diff["counts"]["removed"], "ownership": "unknown", "credits": "unknown"},
            "mechanics": mechanics, "conditional_questions": questions, "target_interaction_tests": interactions,
            "ko_lines": {"status": "unknown", "printed_attack_options": guide["attack_options"],
                "missing": ["visible_target_HP_and_protections", "dated_normative_effects", "energy_and_board_state"],
                "plan": "Lire coûts et effets cités, puis calculer les K.O. seulement sur un plateau attesté."},
            "evidence_quality": {"dated_text_rows": len(mechanics), "total_rows": len(guide["card_role"]),
                "supported_mechanics": len(roles), "supported_interaction_tests": len(interactions),
                "target_text_available": bool(target_mechanics)},
            "test_plan": recommendations.public_test_plan(target=target, selector=selector,
                support=[m["knowledge_card_id"] for m in mechanics]),
            "preflight": guide["preflight"], "uncertainty": guide["uncertainty"]})
    # Evidence coverage and the usefulness of a test, never tournament finish or strength.
    alternatives.sort(key=lambda o: (-int(o["evidence_quality"]["target_text_available"]),
        -o["evidence_quality"]["supported_interaction_tests"],
        -o["evidence_quality"]["supported_mechanics"],
        -(o["evidence_quality"]["dated_text_rows"] / max(1, o["evidence_quality"]["total_rows"])),
        o["switch_cost"]["copies_replaced"], o["source"]["composition_id"]))
    return {"model_version": "counter-deck-v1", "as_of": as_of, "status": "PARTIAL_WITH_EVIDENCE",
        "target": {"label": target, "basis": "caller_supplied_archetype_hypothesis",
            "public_reference_proxy": target_guide["variant"] if target_guide else None,
            "source_list": target_guide["source_list"] if target_guide else None,
            "mechanics": target_mechanics, "is_exact_opponent_deck": False,
            "missing_evidence": [] if target_mechanics else ["DATED_TARGET_TEXT_MISSING"]},
        "baseline_selector": baseline, "requested_options": options, "alternatives": alternatives,
        "available_compositions": inventory["available_compositions"],
        "sample": {"events": inventory["events"], "placements": inventory["available_placements"],
                   "bias": "selected_public_placements_not_match_samples"},
        "ranking_basis": "test_plan_relevance_and_dated_evidence_coverage_then_copy_change_cost_not_strength",
        "adaptation": {"kind": "hypothesis_to_test", "export": None,
            "proposal": "Conserver la liste de référence; isoler une seule question de séquence ou de ressource avant de proposer un changement de carte.",
            "validation_required": "exact_60_dated_rules_and_full_variant_review_before_any_variant_export"},
        "collect_more_games": {"kind": "test_plan", "recommended": True,
            "reason": "Aucune partie personnelle, aucun contre démontré; collecter volontairement les preuves avant de conclure."},
        "predicted_winrate": None, "matchup_advantage": "unknown", "causal_loss_reason": "unknown",
        "read_only": True, "network_used": False, "owner_database_opened": False,
        "database_mutated": False, "release_status": "NOT_RELEASE_READY"}


def human_counter(report):
    print(f"Counter-Deck Lab PUBLIC au {report['as_of']} — cible hypothétique {report['target']['label']}")
    print("Ordre = qualité des preuves et pertinence du test; avantage de matchup : unknown.")
    print(f"Échantillon PUBLIC : {len(report['sample']['events'])} événements, {report['sample']['placements']} placements sélectionnés.")
    for option in report["alternatives"]:
        print(f"{option['selector']} / {', '.join(option['archetypes'])} : {option['decision']}; 60/60.")
        print(f"  Changement exact : {option['construction_changes']['counts']}; crédits et possession : unknown.")
        for action, label in (("removed", "Retirer"), ("added", "Ajouter")):
            for card in option["construction_changes"][action]:
                print(f"    {label} {card['quantity']} {card['name']} {card['set']} {card['number']}")
        print(f"  Différence des sections publiées : {option['published_type_delta']}; consistance et échange des Récompenses : unknown.")
        print("  Sources : " + ", ".join(option["source"]["source_urls"]))
        for mechanic in option["mechanics"]:
            if mechanic["roles"]:
                p = mechanic["text"]["dated_provenance"]
                print(f"  {mechanic['card']} : {', '.join(r['role'] for r in mechanic['roles'])}; {p['retrieved_at']} {p['url']}")
        for question in option["conditional_questions"]:
            print("  Hypothèse : " + question["mechanic"] + "; " + question["question"])
        for interaction in option["target_interaction_tests"]:
            print("  Face au proxy ciblé : " + interaction["question"])
        for step in option["test_plan"]["protocol"]:
            print("  Test : " + step)
        print("  K.O., légalité présentiel/Live et disponibilité : voir preuves/inconnus, aucun contre certifié.")
        print(option["export"]["text"])
    print("Adaptation : hypothesis_to_test, aucun export de variante. Recueillir davantage de parties avant de conclure.")
