"""Conservative opponent observations, separate from hypotheses and PUBLIC proxies."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, timedelta
from urllib.parse import urlsplit
from collections import defaultdict

from pokemind import battle_logs, competitive, rules


VERSION = "opponent-observer-v1"


def composition_key(export):
    """Order/whitespace/case independent, quantities additive; printing identities stay distinct."""
    counts = defaultdict(int)
    for c in battle_logs_deck(export).cards:
        counts[(c.card_type, rules._normalized_name(c.name), (c.set_code or '').upper(),
                (c.collector_number or '').upper())] += c.quantity
    return _digest(sorted((*key, n) for key, n in counts.items()))


def public_family(export, index):
    """A corroborated family for deduplication, including old owner/coach files; ties stay unknown."""
    pokemon = {rules._normalized_name(c.name) for c in battle_logs_deck(export).cards if c.card_type == 'pokemon'}
    canonical = (index or {}).get('pokemon_names', {})
    pokemon |= {canonical[n] for n in pokemon if n in canonical}
    candidates = []
    for family, primary in (index or {}).get('primary_names_by_family', {}).items():
        signatures = set(primary) | {canonical[n] for n in primary if n in canonical}
        if not pokemon & signatures:
            continue
        names = {canonical.get(n, n) for r in index['references'] if r['archetype'] == family for n in r['names']}
        score = len(pokemon & names)
        candidates.append((score, family))
    candidates.sort(reverse=True)
    if not candidates or (len(candidates) > 1 and candidates[0][0] == candidates[1][0]):
        return None
    return 'public-family:' + rules._normalized_name(candidates[0][1])


def conditional_public_deck(match, index, *, as_of):
    """013 deterministic admission. No network, model, write, player name or raw evidence in receipt.

    >=4 observed turns, >=6 distinct names / >=8 visible mentions, >=2 Pokémon including a primary
    signature; all observed Pokémon present, >=80% name overlap, and >=2 names ahead of every other
    composition. A different printing is disclosed, not rejected as a different name. PUBLIC lists
    must have a checked HTTPS Limitless source and a dated sample/cache no older than 28 days.
    Wins additionally require explicit totals of exactly 6 and 5 taken prizes. Unknown totals skip.
    """
    reject = lambda reason: {'status': 'SKIPPED', 'reason': reason, 'hypothesis': True}
    outcome = (match or {}).get('outcome')
    prizes = (match or {}).get('explicit_prize_totals') or {}
    if outcome not in {'losses', 'L', 'loss'} and not (
            outcome in {'wins', 'W', 'win'} and prizes.get('self') == 6 and prizes.get('opponent') == 5):
        return reject('OUTCOME_NOT_ELIGIBLE')
    observed = (match or {}).get('opponent_cards') or []
    names = {c.get('normalized_name') or rules._normalized_name(c.get('name')) for c in observed}
    if (len(names) < 6 or sum(c.get('occurrences', 1) for c in observed) < 8
            or (match.get('max_observed_turn') or 0) < 4):
        return reject('INSUFFICIENT_EVIDENCE')
    if not index or not index.get('references'):
        return reject('PUBLIC_REFERENCE_UNAVAILABLE')
    pokemon = names & set(index.get('pokemon_names', {}))
    if len({index['pokemon_names'][n] for n in pokemon}) < 2:
        return reject('INSUFFICIENT_EVIDENCE')
    since = (date.fromisoformat(as_of) - timedelta(days=27)).isoformat()
    candidates = {}
    for ref in index['references']:
        source = ref.get('composition') or {}
        dates = source.get('date_range') or [str(source.get('retrieved_at') or '')[:10]]
        urls = source.get('source_urls') or []
        if (not dates or any(not re.fullmatch(r'\d{4}-\d{2}-\d{2}', d) or d > as_of for d in dates)
                or max(dates) < since or not urls or any(urlsplit(u).scheme != 'https'
                    or urlsplit(u).hostname not in {'limitlesstcg.com', 'www.limitlesstcg.com', 'play.limitlesstcg.com'}
                    or urlsplit(u).username or urlsplit(u).password for u in urls)):
            continue
        # Name corroboration deliberately tolerates another printing, with an explicit caveat below.
        by_name = [dict(c, set_code=None, collector_number=None) for c in observed]
        result = reconstruct(by_name, {'references': [ref]}, as_of=as_of)
        choices = result['variants'] or result['incompatible_references']
        if not choices:
            continue
        candidate = choices[0]
        hits = set(candidate['matched_names'])
        primary = set(index.get('primary_names_by_family', {}).get(ref['archetype'], []))
        candidate['admissible'] = (len(hits) / len(names) >= .8 and pokemon <= hits
                                   and bool(primary & hits) and not any(
                                       c['reason'] == 'observed_minimum_exceeds_reference' for c in candidate['contradictions']))
        candidate['family_key'] = public_family(candidate['export'], index)
        if candidate['family_key'] != 'public-family:' + rules._normalized_name(ref['archetype']):
            candidate['admissible'] = False
        candidates.setdefault(composition_key(candidate['export']), candidate)
    if not candidates:
        return reject('PUBLIC_REFERENCE_UNAVAILABLE')
    ranked = sorted(candidates.values(), key=lambda c: (-len(c['matched_names']), c['composition_id']))
    best = ranked[0]
    if len(ranked) > 1 and len(best['matched_names']) - len(ranked[1]['matched_names']) < 2:
        return reject('AMBIGUOUS_PUBLIC_REFERENCE')
    if not best['admissible']:
        return reject('INSUFFICIENT_EVIDENCE')
    # Keep the original observed identities separate from the assumed public 60.
    best['observed'] = [{k: c[k] for k in ('name', 'normalized_name', 'set_code', 'collector_number',
                                         'minimum_quantity', 'occurrences') if k in c} for c in observed]
    original = reconstruct(observed, {'references': [r for r in index['references']
        if composition_key(r['export']) == composition_key(best['export'])][:1]}, as_of=as_of)
    full = (original['variants'] or original['incompatible_references'])[0]
    best['unknowns'] = full['unknowns']
    return {'status': 'ELIGIBLE', 'hypothesis': True, 'candidate': best,
            'evidence': {'distinct_observed': len(names), 'visible_mentions': sum(c.get('occurrences', 1) for c in observed),
                         'matched_names': len(best['matched_names']), 'policy': 'public-opponent-013-v1'}}


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":")).encode()).hexdigest()


def _card_identity(name):
    name = name or ""
    match = re.fullmatch(r"(.+?) ([A-Z][A-Z0-9-]{1,9}) ([0-9]{1,4}[A-Za-z]?|[A-Z]{1,3}[0-9]{1,4})", name)
    title, code, number = match.groups() if match else (name, None, None)
    normalized = rules._normalized_name(title)
    if (not normalized or normalized in {"pokemon", "pokémon", "a pokémon", "un pokémon", "a card", "une carte",
                                          "energy", "énergie", "the active pokémon", "son pokémon actif"}
            or re.fullmatch(r"(?:(?:a|an|the|un|une|son|sa|ses|their|his|her|my|your) )?(?:active |benched |basic |de base )?"
                            r"(?:pok[eé]mon|energy|[ée]nergie|hand|main|supporter|stadium|stade|item|objet|ability|talent)s?", normalized)
            or re.search(r"\b(?:cards?|cartes?|attack|attaque|prize|récompense|damage counters|marqueurs)\b", normalized)
            or re.search(r"[,;]", normalized)
            or re.match(r"^[0-9]+\s", normalized)):
        return None
    return {"name": title, "normalized_name": normalized, "set_code": code, "collector_number": number}


def classify(observed, index):
    references = index["references"] if index else []
    families = defaultdict(set)
    for ref in references:
        families[ref["archetype"]].update(ref["names"])
    names = {x["normalized_name"] for x in observed}
    membership = {name: sorted(label for label, values in families.items() if name in values) for name in names}
    informative = {name for name, labels in membership.items() if labels and len(labels) < len(families)}
    candidates = []
    for label, values in sorted(families.items()):
        hits = sorted(informative & values)
        if hits:
            candidates.append({"archetype": label, "distinctive_matches": hits,
                               "shared_matches": sorted((names & values) - informative),
                               "confidence": "low" if len(hits) < 2 else "moderate",
                               "probability": None, "basis": "partial_name_overlap_not_calibrated_probability"})
    weights = (index or {}).get("signature_weights_by_family", {})
    maximum = max((len(c["distinctive_matches"]) * weights.get(c["archetype"], 1) for c in candidates), default=0)
    minimums = (index or {}).get("minimum_matches_by_family", {})
    best = [c["archetype"] for c in candidates if len(c["distinctive_matches"]) * weights.get(c["archetype"], 1) == maximum
            and len(c["distinctive_matches"]) >= minimums.get(c["archetype"], 1)]
    return {"kind": "archetype_hypothesis", "status": "unknown" if not best else "ambiguous" if len(best) != 1 else "hypothesized",
            "label": best[0] if len(best) == 1 else None, "candidates": candidates,
            "unmatched_names": sorted(name for name in names if not membership[name]),
            "non_discriminating_names": sorted(names - informative),
            "limits": ["A card absent from a partial log is not evidence of absence.",
                       "Observed names do not prove a printing or an exact archetype."]}


def observe(parsed, *, index=None, exact_export=None, reviews=None, as_of, source_parser_version=battle_logs.PARSER_VERSION):
    """Input is the existing parser's immutable result, never a hidden hand."""
    competitive._advisor_context(as_of)
    raw = []
    timeline, excluded = [], []
    by_card = {}
    for event in parsed.events:
        role = battle_logs._actor_role(event.actor, parsed)
        record = {"sequence": event.sequence, "turn": event.turn_number, "actor_role": role,
                  "event_type": event.event_type, "card_name": event.card_name, "evidence": event.evidence,
                  "confidence": event.confidence, "source": "battle_events", "parser_version": source_parser_version}
        raw.append(record)
        if role != "opponent":
            continue
        identity = _card_identity(event.card_name)
        visible_draw_play = event.event_type == "draw" and bool(re.search(
            r"and played (?:it|them)|et (?:l['’]a jouée?|les a jouées?|a joué (?:la|les))", event.evidence, re.I))
        if identity is None or (event.event_type not in {"play", "reveal", "attach", "use", "place", "evolve"} and not visible_draw_play):
            excluded.append({**record, "reason": "HIDDEN_DRAW_GENERIC_OR_UNSUPPORTED_CARD_EVIDENCE"})
            continue
        key = (identity["normalized_name"], identity["set_code"], identity["collector_number"])
        current = by_card.setdefault(key, {**identity, "minimum_quantity": 1, "occurrences": 0,
                                          "quantity_basis": "at_least_one;mentions_do_not_prove_extra_copies", "evidence_sequences": []})
        current["occurrences"] += 1
        current["evidence_sequences"].append(event.sequence)
        timeline.append({**record, "identity": identity})
    observed = list(by_card.values())
    hypothesis = classify(observed, index)
    history = []
    for review in reviews or []:
        if (not isinstance(review, dict) or not isinstance(review.get("review_id"), str)
                or review.get("status") not in {"active", "withdrawn"} or not review.get("source")
                or not isinstance(review.get("recorded_at"), str)
                or (review["status"] == "active" and (not isinstance(review.get("label"), str) or not review["label"].strip()))):
            raise ValueError("OPPONENT_REVIEW_EXPLICIT_HISTORY_REQUIRED")
        competitive._advisor_context(review["recorded_at"][:10])
        if review["recorded_at"][:10] <= as_of:
            history.append(dict(review))
    if len({x["review_id"] for x in history}) != len(history):
        raise ValueError("OPPONENT_REVIEW_ID_DUPLICATE")
    history.sort(key=lambda x: (x["recorded_at"], x["review_id"]))
    active = history[-1] if history and history[-1]["status"] == "active" else None
    classification = {"label": active["label"] if active else hypothesis["label"],
                      "basis": "owner_observed_label" if active else hypothesis["status"],
                      "exact_deck_proven": False}
    labels = [classification["label"]] if classification["label"] else [c["archetype"] for c in hypothesis["candidates"]]
    proxies = []
    for label in labels:
        choices = [r for r in (index or {}).get("references", []) if r["archetype"] == label]
        if choices:
            ref = min(choices, key=lambda r: r["composition"]["composition_id"])
            proxies.append({"kind": "public_reference_proxy", "archetype": label,
                            "selector": ref["selector"], "source": ref["composition"], "total_cards": ref["total_cards"],
                            "is_exact_opponent_deck": False, "legality": "unknown", "live_availability": "unknown"})
    exact = None
    if exact_export is not None:
        # Existing serializer rejects totals other than 60 and unsafe/duplicate entries.
        from pokemind.deck_exports import serialize_deck
        exported = serialize_deck(battle_logs_deck(exact_export).cards)
        listed = competitive._card_map(exported)
        def present(card):
            return any(rules._normalized_name(c["name"]) == card["normalized_name"]
                       and (not card["set_code"] or (c["set"] == card["set_code"] and c["number"] == card["collector_number"]))
                       for c in listed.values())
        if (parsed.reference_player and parsed.opponent_name
                and not battle_logs._same_name(parsed.reference_player, parsed.opponent_name)
                and all(present(card) for card in observed)):
            exact = {"kind": "exact_confirmed_60", "basis": "explicitly_supplied_complete_opponent_export",
                     "total_cards": 60, "composition_id": competitive._composition_id(listed),
                     "legality": "unknown", "independently_verified_game_deck": False}
        else:
            excluded.append({"reason": "EXPLICIT_EXPORT_CONFLICTS_WITH_OBSERVED_CARDS"})
    report = {"model_version": VERSION, "as_of": as_of, "valid_log": parsed.valid,
              "reference_sample": {k: index.get(k) for k in ("as_of", "sampled_placements", "events", "scope")} if index else None,
              "raw_parser_events": raw, "observed_partial": {"kind": "observed_partial", "cards": observed,
                  "minimum_copies_not_additive_across_partial_identities": True,
                  "total_seen_names": len({r["normalized_name"] for r in observed}), "total_deck_size": "unknown"},
              "timeline": timeline, "excluded_evidence": excluded, "archetype_hypothesis": hypothesis,
              "classification": classification, "classification_history": history,
              "public_reference_proxy": proxies, "exact_confirmed_60": exact,
              "unknowns": ["hidden_hand", "unseen_cards_and_copies", "causal_loss_reason", "legality", "ownership"],
              "read_only": True, "network_used": False}
    report["version_sha256"] = _digest(report)
    return report


def battle_logs_deck(text):
    from pokemind.decks import parse_deck_export
    return parse_deck_export(text)


def reconstruct(observed, index, *, as_of, limit=3):
    """Rank sourced 60-card variants; overlap is never a calibrated probability."""
    competitive._advisor_context(as_of)
    if not 1 <= limit <= 3:
        raise ValueError('OPPONENT_VARIANT_LIMIT')
    candidates, seen = [], set()
    for ref in (index or {}).get('references', []):
        export = ref.get('export')
        if not export:
            continue
        cards = list(competitive._card_map(export).values())
        if sum(c['quantity'] for c in cards) != 60:
            continue
        identity = competitive._composition_id(competitive._card_map(export))
        if identity in seen:
            continue
        seen.add(identity)
        rows = ref.get('cards') or cards
        matched, contradictions, unknown = [], [], []
        for card in observed:
            name = card.get('normalized_name') or rules._normalized_name(card.get('name'))
            found = [c for c in rows if name in set(c.get('aliases', [])) | {rules._normalized_name(c['name'])}]
            if not found:
                contradictions.append({'name': card['name'], 'reason': 'observed_card_not_in_reference'})
                continue
            if card.get('set_code'):
                exact = [c for c in found if c['set'] == card['set_code'] and c['number'] == card.get('collector_number')]
                if not exact:
                    unknown.append({'name': card['name'], 'reason': 'printing_equivalence_unproven'})
                    continue
                found = exact
            minimum = card.get('minimum_quantity', 1)
            if sum(c['quantity'] for c in found) < minimum:
                contradictions.append({'name': card['name'], 'reason': 'observed_minimum_exceeds_reference'})
            else:
                matched.append(name)
        source = ref.get('composition', {})
        dates = source.get('date_range') or []
        if dates and max(dates) > as_of:
            continue
        annotated = [dict(c, status='observed_name_probable_quantity' if any(
            n in set(c.get('aliases', [])) | {rules._normalized_name(c['name'])} for n in matched)
            else 'probable_unconfirmed', printing_status='unknown') for c in rows]
        candidates.append({'kind': 'RECONSTRUCTION_HYPOTHESIS', 'selector': ref['selector'],
            'archetype': ref['archetype'], 'composition_id': identity, 'source': source,
            'as_of': as_of, 'total_cards': 60, 'export': export, 'cards': annotated,
            'observed': observed, 'matched_names': sorted(set(matched)), 'contradictions': contradictions,
            'unknowns': unknown, 'compatible': not contradictions and bool(matched),
            'coverage': {'matched_names': len(set(matched)), 'observed_names': len(observed)},
            'is_exact_opponent_deck': False, 'probability': None,
            'legality': 'unknown', 'live_availability': 'unknown'})
    candidates.sort(key=lambda c: (not c['compatible'], -len(c['matched_names']), len(c['contradictions']),
        -int((''.join(c['source'].get('date_range') or ['0000-00-00'])[-10:]).replace('-', '') or '0'), c['composition_id']))
    compatible = [c for c in candidates if c['compatible']]
    return {'status': 'HYPOTHESES' if compatible else 'NO_COMPATIBLE_REFERENCE',
        'variants': compatible[:limit], 'incompatible_references': candidates[:limit] if not compatible else [],
        'observed': observed, 'as_of': as_of, 'exact_deck': False,
        'interpretation': 'Ranked compatibility, not a calibrated probability; unseen cards remain unconfirmed.'}


def human_opponent(report):
    print(f"Adversaire — observation partielle au {report['as_of']}; deck complet : unknown.")
    for card in report["observed_partial"]["cards"]:
        print(f"  {card['name']} : au moins {card['minimum_quantity']}, {card['occurrences']} mentions; "
              f"preuves événements {card['evidence_sequences']}.")
    print(f"Archétype : {report['classification']['label'] or 'unknown'} ({report['classification']['basis']}).")
    for proxy in report["public_reference_proxy"]:
        print(f"  Référence PUBLIC60 : {proxy['selector']} / {proxy['archetype']}; ce proxy n'est pas son deck exact.")
    if report["exact_confirmed_60"]:
        print("Export adverse complet explicitement fourni et cohérent60; légalité unknown.")
    print("Main cachée, cartes non vues, exemplaires supplémentaires et cause de perte : unknown. Détails : --json.")
