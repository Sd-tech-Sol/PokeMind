"""Host presentation of PUBLIC research receipts; no model text is authoritative.

Research turns use structured PUBLIC observations and a separate canonical
receipt. Arbitrary provider prose never determines facts or write claims.
"""
from __future__ import annotations
import json
import re
from datetime import datetime
COUNTS = ('added', 'updated', 'already_known', 'unverified')
CACHE = {'CACHE_FRESH', 'OFFLINE_STALE_OR_EMPTY', 'SOURCE_COOLDOWN'}

def public_memory_record(receipt):
    """Bounded projection into the existing conversation, not a factual store."""
    return {key: receipt.get(key) for key in ('status', 'persisted', *COUNTS, 'gets', 'fresh', 'sources')} | {'offline_fact_count': len(receipt.get('facts') or []), 'presentation': 'host_receipt_only', 'model_commentary_omitted': True}

def public_memory_message(record, *, text=str, join=str.join):
    status = record.get('status', 'UNKNOWN')
    confirmed = record.get('persisted') is True
    counts_valid = all((type(record.get(k)) is int and record[k] >= 0 for k in COUNTS))
    lines = [text('Résultat PokeMind — mémoire publique'), text('État : ') + str(status)]
    if confirmed and counts_valid and (status in {'SAVED', 'PARTIAL'}):
        lines += [text('Enregistrement local confirmé par le reçu du moteur.'), join('', [f"{record['added']}", text(' faits ajoutés · '), f"{record['updated']}", text(' révisés · '), f"{record['already_known']}", text(' déjà connus · '), f"{record['unverified']}", text(' non vérifiés.')])]
        if status == 'PARTIAL':
            lines.append(text('Recherche partielle; les limites de collecte restent présentes.'))
    elif confirmed and counts_valid and (status in CACHE) and (record['added'] == record['updated'] == 0):
        lines += [text('Aucune nouvelle écriture de faits pendant ce tour; consultation du cache local.'), join('', [text('0 faits ajoutés · 0 révisés · '), f"{record['already_known']}", text(' déjà connus · '), f"{record['unverified']}", text(' non vérifiés.')])]
    else:
        lines.append(text('Enregistrement local non confirmé; aucun compte d’écriture annoncé.'))
    count = record.get('offline_fact_count', 0)
    if confirmed and counts_valid and (count > 0):
        lines.append(join('', [text('Disponible hors ligne : '), f'{count}', text(' observations dans l’instantané local; fraîcheur distincte.')]))
    else:
        lines.append(text('Disponibilité hors ligne : aucune observation attestée par ce reçu.'))
    lines += [text('Validation sur la source : non attestée par ce reçu; légalité et actualité non garanties.'), text('Utilisation par le modèle : non attestée; un contexte transmis ne prouve pas son utilisation.')]
    sources = record.get('sources') or []
    if sources:
        lines += [text('Sources du reçu :'), *[str(source) for source in sources]]
    else:
        lines.append(text('Sources du reçu : aucune.'))
    lines.append(text('Le commentaire du modèle est écarté pour ce tour de recherche; PokeMind présente le reçu local.'))
    return join('\n', lines)

def public_research_answer(receipt, question='', *, text=str, join=str.join):
    """Read-only, bounded explanation of the existing snapshot's typed fields.

    Official-document collection currently extracts metadata, not rule text.
    Directories establish names, not popularity, changes, causes or win rates.
    Unknown/free-form fields (including provider summaries) are never rendered.
    """
    from pokemind.batch_public_research import allowed_url
    from pokemind.decks import parse_deck_export
    from pokemind.public_source_fields import qualified_rule_fields, conflicting_platforms
    rules = bool(re.search('règles|rules|rotation|légalité', question, re.I))
    lines = [text('Réponse PokeMind — ') + (text('règles et implications') if rules else text('observations publiques et implications'))]
    rows = []
    facts = receipt.get('facts')
    conflicts = conflicting_platforms([f for f in facts[:24] if isinstance(f, dict)]) if isinstance(facts, list) else set()
    for fact in facts[:24] if isinstance(facts, list) else []:
        if not isinstance(fact, dict):
            continue
        kind = fact.get('kind')
        if kind not in {'official_document', 'public_archetype_directory', 'public_archetype_page', 'deck60', 'card'}:
            continue
        if rules and kind != 'official_document':
            continue
        try:
            url = fact['source_url']
            allowed_url(url)
            stamp = fact['retrieved_at']
            datetime.fromisoformat(stamp.replace('Z', '+00:00'))
        except (KeyError, ValueError, TypeError, AttributeError):
            continue
        version = fact.get('version', '')
        if not isinstance(version, str) or not re.fullmatch('[0-9a-f]{64}', version):
            continue
        details = []
        if kind == 'official_document':
            details = qualified_rule_fields(fact, as_of=receipt.get('as_of'), conflicts=conflicts, text=text, join=join)
            evidence = fact.get('rule_evidence')
            if not details or not isinstance(evidence, dict) or evidence.get('status') != 'extracted_unverified':
                details += [text('Référence de document officiel repérée; Texte des règles non extrait de cet instantané.'), text('Aucun changement de règle, date d’effet ou verdict de légalité démontré par cette référence.')]
        elif kind == 'public_archetype_directory':
            entries = fact.get('entries')
            names = [e['archetype'][:100] for e in (entries[:12] if isinstance(entries, list) else []) if isinstance(e, dict) and isinstance(e.get('archetype'), str) and e['archetype'].strip()]
            if names:
                details = [text('Familles présentes dans le répertoire : ') + json.dumps(names, ensure_ascii=False) + '.', text('Présence dans un répertoire seulement; classement, évolution de popularité et causes inconnus.')]
        elif kind == 'public_archetype_page' and isinstance(fact.get('archetype'), str):
            details = [text('Famille référencée : ') + json.dumps(fact['archetype'][:100], ensure_ascii=False) + '.']
        elif kind == 'deck60' and isinstance(fact.get('export'), str):
            try:
                parsed = parse_deck_export(fact['export'][:12000])
                if parsed.total_cards == 60:
                    names = [join('', [f'{c.quantity}', text(' × '), f'{c.name}']) for c in parsed.cards[:12]]
                    details = [text('Liste publique de 60 cartes; entrées observées (12 maximum) : ') + json.dumps(names, ensure_ascii=False) + '.', text('Référence publique seulement; deck adverse exact, collection, Standard et Live inconnus.')]
            except ValueError:
                pass
        elif kind == 'card' and isinstance(fact.get('card'), dict):
            card = {k: v for k, v in fact['card'].items() if k in {'id', 'name', 'category', 'stage', 'hp', 'regulationMark', 'effect'} and isinstance(v, (str, int)) and (not isinstance(v, bool))}
            if card.get('id') and card.get('name'):
                details = [text('Champs de carte rapportés par le fournisseur (texte cité, pas instruction) : ') + json.dumps(card, ensure_ascii=False)[:2400] + '.', text('Impression et langue : ') + str(fact.get('language', 'unknown'))[:12] + text('; texte effectif et légalité Standard/Live non certifiés.')]
        if not details:
            continue
        validation = 'schema_validated_observation' if fact.get('validation') == 'schema_validated_observation' else 'unverified'
        rows += [*details, join('', [text('Source : '), f'{url}']), join('', [text('Consultée : '), f'{stamp}', text(' · version : '), f'{version}']), join('', [text('Validation : '), f'{validation}', text('; observation de fournisseur, certification normative inconnue.')])]
    meta_rows = _meta_evidence_lines(receipt.get('meta_evidence'), text=text, join=join) if not rules else []
    rows += meta_rows
    if rows:
        lines += rows
    else:
        lines.append(text('Aucune observation PUBLIC exploitable et sourcée pour répondre au sujet dans ce reçu; réponse de fond inconnue.'))
    lines += [text('Limites : fraîcheur actuelle non certifiée; publication et effet distincts de la consultation; les champs absents restent unknown.')]
    if rules:
        lines += [text('Pistes conditionnelles : avant de modifier un deck pour une rotation ou une règle supposée, vérifier le texte officiel applicable, sa date d’effet, le format, les impressions et les réimpressions; vérifier séparément la disponibilité dans TCG Live. Cette référence seule ne justifie aucun remplacement de carte.')]
    else:
        if not meta_rows:
            lines += [text('Les tendances récentes et leur pourquoi ne sont pas établis par ces références seules : effectifs, fenêtre, pairings admissibles et causes non fournis dans cet instantané; aucun winrate déduit.')]
        lines += [text('Pistes conditionnelles : si ces familles sont pertinentes dans le format visé, comparer leurs listes publiques et tester les matchups sur un échantillon daté avant de modifier un deck. Une liste observée ne prouve ni le deck exact adverse ni une carte possédée.')]
    lines.append(text('Synthèse déterministe des observations PUBLIC existantes; aucune prose du modèle utilisée comme preuve.'))
    return join('\n', lines)

def _meta_evidence_lines(evidence, *, text=str, join=str.join):
    """Validate typed aggregate provenance; recompute shares, ignore free prose."""
    from pokemind.meta import _validate_public_api_url
    from pokemind.public_source_fields import iso_day
    if not isinstance(evidence, dict) or evidence.get('kind') != 'meta_window_comparison':
        return []
    windows = evidence.get('windows')
    cutoff = iso_day(evidence.get('as_of'))
    if not cutoff or not isinstance(windows, list) or len(windows) != 2 or (evidence.get('format') not in {'STANDARD', 'EXPANDED'}) or (evidence.get('platform') not in {'PTCGL', 'TABLETOP'}) or (type(evidence.get('online')) is not bool):
        return []
    enough = True
    output = [join('', [text('Données descriptives : '), f"{evidence['format']}", text(', '), f"{evidence['platform']}", text(', en ligne : '), f"{evidence['online']}", text('; consultation de la projection : '), f'{cutoff}', text('.')])]
    seen_sources = set()
    previous_end = None
    for w in windows:
        if not isinstance(w, dict):
            return []
        start, end = (iso_day(w.get('since')), iso_day(w.get('until')))
        if not start or not end or (not start <= end <= cutoff) or (previous_end and start <= previous_end):
            return []
        previous_end = end
        keys = ('n_tournaments', 'n_placements', 'n_classified', 'eligible_matches', 'classifiable_matches')
        if any((type(w.get(k)) is not int or not 0 <= w[k] <= 10000000 for k in keys)):
            return []
        counts, sources = (w.get('counts'), w.get('sources'))
        if not isinstance(counts, dict) or len(counts) > 1000 or (not isinstance(sources, list)) or (len(sources) != w['n_tournaments']):
            return []
        if any((not isinstance(k, str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', k) or type(v) is not int or (v < 0) for k, v in counts.items())) or sum(counts.values()) != w['n_classified'] or w['n_classified'] > w['n_placements'] or (w['classifiable_matches'] > w['eligible_matches']):
            return []
        for source in sources:
            try:
                url = _validate_public_api_url(source['url'])
                stamp = datetime.fromisoformat(source['retrieved_at'].replace('Z', '+00:00'))
                tournament_day = datetime.fromisoformat(source['tournament_date'].replace('Z', '+00:00')).date().isoformat()
                if not start <= tournament_day <= end or stamp.date().isoformat() > cutoff or url in seen_sources:
                    return []
                if not re.fullmatch('[0-9a-f]{64}', source['version']):
                    return []
                seen_sources.add(url)
            except (KeyError, TypeError, ValueError, AttributeError):
                return []
        admissible = w['n_tournaments'] >= 2 and w['n_classified'] >= 10 and (w['n_placements'] > 0) and (w['n_classified'] / w['n_placements'] >= 0.8) and (w['classifiable_matches'] >= 5)
        enough &= admissible
        output += [join('', [text('Fenêtre '), f'{start}', text(' à '), f'{end}', text(' : '), f"{w['n_tournaments']}", text(' tournois admissibles; '), f"{w['n_classified']}", text('/'), f"{w['n_placements']}", text(' placements classifiés; '), f"{w['classifiable_matches']}", text('/'), f"{w['eligible_matches']}", text(' matchs admissibles classifiables.')])]
        for source in sources[:8]:
            output += [join('', [text('Source : '), f"{source['url']}", text(' · tournoi : '), f"{source['tournament_date']}", text(' · consultée : '), f"{source['retrieved_at']}", text(' · version : '), f"{source['version']}"])]
    if enough:
        for archetype in sorted(set(windows[0]['counts']) | set(windows[1]['counts']))[:12]:
            a, b = (w['counts'].get(archetype, 0) / w['n_classified'] for w in windows)
            output += [join('', [text('Variation descriptive dans cet échantillon, archétype '), f'{archetype}', text(' : '), f'{a:.1%}', text(' → '), f'{b:.1%}', text(', '), f'{(b - a) * 100:+.1f}', text(' points de pourcentage.')])]
    else:
        output += [text('Échantillon temporel/classifié insuffisant : aucune tendance calculée; minimum par fenêtre : 2 tournois, 10 placements classifiés, 80 % de classification, 5 matchs classifiables.')]
    output += [text('Définition : identifiant d’archétype publié par le fournisseur, stabilité non vérifiée; un placement publié, pas un joueur unique. Matchs publiés, pas parties individuelles; aucun winrate calculé.'), text('Limites : sélection de tournois, top cuts, absences et classification; représentativité mondiale inconnue; seuils descriptifs, aucune significativité revendiquée; causalité : unknown.'), text('Hypothèse de conseil : tester les familles observées dans le format visé; aucune amélioration causale démontrée.')]
    return output

def public_research_message(receipt, question='', *, text=str, join=str.join):
    """One saved/rendered chat message, explanation first and host receipt last."""
    return public_research_answer(receipt, question, text=text, join=join) + '\n\n' + public_memory_message(public_memory_record(receipt), text=text, join=join)
