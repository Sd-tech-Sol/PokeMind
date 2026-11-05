"""Read models over PokeMind's existing engines. No alternative brain or DB."""
from __future__ import annotations
from pokemind.desktop.locale_text import T, J

import json
import re
import sqlite3
import hashlib
from contextlib import closing
from datetime import date
from pathlib import Path

from pokemind import battle_batch, battle_coach, cards, coach_cards, competitive, decks, diagnostics, legacy_bridge, rules, seasons
from pokemind.database import connect_readonly
from pokemind.public_deck_preflight import SCOPED_PUBLIC_CACHES


DECK_VIOLATIONS = {'DECK_TOTAL_QUANTITY_MISMATCH', 'DECK_TOTAL_NOT_REQUIRED_COUNT',
                   'DECK_COPY_LIMIT_EXCEEDED', 'DECK_HAS_NO_BASIC_POKEMON',
                   'DECK_ACE_SPEC_LIMIT_EXCEEDED', 'DECK_RADIANT_LIMIT_EXCEEDED'}
SPECIAL_PROBLEMS = {'acespec': ('ACE_SPEC_MAXIMUM_1', 'Une seule carte AS TACTIQUE (ACE SPEC) par deck.'),
                    'radiant': ('RADIANT_MAXIMUM_1', 'Un seul Pokémon Radieux par deck.')}
# The owner's own recorded games, stats or decks. A pronoun alone (« fais-moi »,
# « je veux ») is not personal data: it used to turn deck requests into a stats dump.
PERSONAL = re.compile(r"\b(?:stats?|statistiques|statistics|combats?|défaites?|defaites?|victoires?|perdu|perds"
                      r"|parties?|battles?|losses|matches|matchs?|matchups?|historique)\b"
                      r"|\b(?:mes|mon|ma|my)\s+(?:decks?|listes?|lists?|cartes?|cards?|collection)\b", re.I)
MY_DECKS = battle_coach.REPORT_DIR + '/my-decks'
SAVE_REQUEST = re.compile(r'\b(?:enregistr\w*|sauvegard\w*|conserv\w*|save|ajout\w*|cré\w*|cree\w*|construi\w*'
                          r'|reconstrui\w*)\b.*\b(?:deck|liste|candidat)', re.I)
BUILD = re.compile(r"\b(?:fais|faire|fait|crée\w*|cree\w*|créer|construi\w*|bâti\w*|bati\w*|propos\w*|sugg[eéè]r\w*"
                   r"|recommand\w*|donne|amélior\w*|amelior\w*|build|make|create|suggest|improve)\b", re.I)


def personal_kind(option):
    # The French source label, whatever the display language (an English UI used to leak these).
    return 'personnelle' in getattr(option['kind'], 'fr', option['kind'])

MATCHUPS_SHOWN = 15
TOOL_BUDGET = 20000  # under the coach tool cap (assistant.tools.MAX_TOOL_BYTES), envelope included


def _bytes(value):
    return len(json.dumps(value, ensure_ascii=False).encode())


def research_view(receipt):
    """The coach's copy of a research receipt: counts and sources, then whole facts while they fit.

    The host keeps the complete receipt; a whole one exceeded the tool cap, so the coach got only
    an error (owner's diagnostic, 2026-11-05).
    """
    facts = list(receipt.get('facts') or [])
    sources = list(receipt.get('sources') or [])
    view = {key: value for key, value in receipt.items() if key not in {'facts', 'history', 'meta_evidence'}}
    view.update(sources=sources[:12], facts_total=len(facts), facts=[])
    used = _bytes(view)
    if receipt.get('meta_evidence') is not None:
        size = _bytes(receipt['meta_evidence']) + 20
        if used + size <= TOOL_BUDGET // 2:
            view['meta_evidence'] = receipt['meta_evidence']
            used += size
        else:
            view['meta_evidence'] = 'Trop long ici; operation matchups pour le détail.'
    for fact in facts:
        size = _bytes(fact) + 2
        if used + size <= TOOL_BUDGET:
            view['facts'].append(fact)
            used += size
    if len(view['facts']) < len(facts) or len(sources) > 12:
        view['shortened'] = 'Reçu raccourci à la taille permise; la mémoire locale garde tout.'
    return view


def context_delta(context, previous=None):
    """The data to paste for this turn: all of it, or only what changed since the last turn that the same
    engine session already received (audit A-7). The digests stay in memory, never on disk."""
    digests = {key: hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()
               for key, value in context.items()}
    if not previous:
        return context, digests
    unchanged = sorted(key for key, digest in digests.items() if previous.get(key) == digest)
    payload = {key: value for key, value in context.items() if key not in unchanged}
    if unchanged:
        payload['unchanged_since_previous_message'] = unchanged
        payload['unchanged_note'] = ('Données déjà reçues au message précédent de cette session; '
                                     'pokemind_tool operation=context les redonne au besoin.')
    return payload, digests


class Services:
    def __init__(self, root):
        self.root = Path(root).absolute()
        self.report = None  # the season shown (owner, 2026-11-05); full_report holds every game
        self.full_report = None
        self.season_key = seasons.CURRENT
        self.season_rows = []
        self.season_dates = {}
        self.learning = None
        self._loaded = None
        self.match_index = {}
        self.selected_match = None
        self.research_allowed = False
        self.candidate_allowed = False
        self.cancelled = None
        self.private_decks_allowed = False
        self.annotation_allowed = False
        self.last_research_receipt = None
        self.saved_deck = None
        self._aliases = None

    @staticmethod
    def personal_question(question):
        return bool(PERSONAL.search(question))

    @staticmethod
    def build_request(question):
        """« Fais-moi un deck… »: the coach builds it, even when stats stay local."""
        return bool(BUILD.search(question) and re.search(r'\b(?:decks?|listes?|lists?)\b', question, re.I))

    def local_answer(self, question):
        """A privacy-preserving real answer when cloud sharing is public-only."""
        report = self.report
        if not report:
            return T('Aucun rapport local valide disponible. Utilise Actualiser ou colle un journal complet; aucune partie inventée.')
        outcomes = report['outcomes']
        season = report.get('season', {}).get('name')
        text = (T('PokeMind · données locales\n') + (T('Saison : ') + season + '\n' if season else '')
            + str(report['coverage']['valid']) + T(' parties uniques enregistrées : ')
            + str(outcomes['wins']) + T(' victoires, ') + str(outcomes['losses']) + T(' défaites, ')
            + str(outcomes.get('unknown', 0)) + T(' issues inconnues.\n')
            + T('Corpus choisi; taux de victoire global inconnu. Les défaites orientent les priorités pédagogiques.\n'))
        groups = report.get('groups', [])
        selected = [g for g in groups if g['archetype'].casefold() in question.casefold()] or groups[:5]
        for g in selected[:5]:
            text += '\n' + g['archetype'] + ' : ' + str(g['wins']) + T(' V / ') + str(g['losses']) + T(' D, n=') + str(g['n']) + T('. Famille hypothétique.\n')
            for signal in g.get('signals', [])[:2]:
                text += signal['explanation'] + T(' Observé dans ') + str(signal['loss_games']) + T(' défaites et ') + str(signal['win_games']) + T(' victoires; causalité inconnue.\n')
        text += T('\nSource : rapport canonique PokeMind ') + report['as_of'] + ' / ' + report['model_version'] + T(', Learning Loop local. pokemind://page/1\n')
        if re.search(r'dernier|partie|perdu|adversaire|opponent|last', question, re.I) and self.match():
            value = self.match()
            text += T('\nPartie sélectionnée : issue ') + str(value.get('outcome', 'unknown')) + T('; version jouée ') + str(value.get('personal_deck_version', 'unknown')) + '.\n'
            text += T('Cartes adverses observées : ') + J(', ',(c['name'] for c in value.get('opponent_cards', []))) + '.\n'
            if re.search(r'deck|adversaire|reconstr', question, re.I):
                reconstruction = self.reconstruct(value)
                text += T('\nReconstruction : ') + reconstruction['status'] + T('. Aucune liste exacte adverse prouvée.\n')
                for variant in reconstruction['variants']:
                    text += T('\nRECONSTRUCTION / HYPOTHÈSE · ') + variant['archetype'] + T(' · 60/60 · légalité/Live inconnus\n')
                    text += variant['export'] + T('\nSources : ') + J(', ',(variant['source'].get('source_urls', []))) + '\n'
        return (text + T('Réponse locale : les statistiques ne sont pas envoyées au cloud avec ton réglage actuel.')
            + '\n' + T('Pour que Codex ou Claude s’en servent, choisis « Ajouter statistiques… » dans Réglages.'))

    def load(self, update=False, cancelled=None, progress=None):
        if cancelled and cancelled():
            raise ValueError('DESKTOP_CANCELLED')
        if update:
            from pokemind.desktop.ingestion import refresh
            result = refresh(self.root, cancelled=cancelled, progress=progress)
        else:
            target = battle_batch.safe_path(self.root, self.root / battle_coach.REPORT_DIR, exists=False)
            if not target.exists():
                return {"status": "EMPTY", "report": None, "learning": None}
            selected, _ = battle_coach._discover(self.root, target)
            if selected is None:
                return {"status": "EMPTY", "report": None, "learning": None}
            paired = selected.with_name(selected.stem + '.learning.json')
            key = (selected.name, legacy_bridge._stamp(selected),
                   legacy_bridge._stamp(paired) if paired.exists() else None)
            if self._loaded and self._loaded[0] == key:
                # Every coach question reloads; an unchanged snapshot is not re-parsed.
                _, result, self.match_index = self._loaded
                self.learning = result.get('learning')
                self.set_full_report(result.get('report'))
                return result
            result = None
            if paired.exists():
                try:
                    result = legacy_bridge.saved_report(self.root, report=selected, learning=paired)
                except (OSError, ValueError):
                    result = None
            if result is None:
                result = legacy_bridge.saved_report(self.root, report=selected)
                if paired.exists():
                    result['learning_status'] = 'UNAVAILABLE_NOT_MODIFIED'
        if cancelled and cancelled():
            raise ValueError('DESKTOP_CANCELLED')
        self.learning = result.get('learning')
        self.set_full_report(result.get('report'))
        from pokemind.desktop.ingestion import match_index
        self.match_index = match_index(self.root)
        self._loaded = (key, result, self.match_index) if not update else None
        return result

    def set_full_report(self, report):
        """Every game; the report shown is the chosen season of it."""
        self.full_report = report
        self.season_dates = seasons.added_dates(self.root, (report or {}).get('matches', []))
        self.set_season(self.season_key)

    def set_season(self, key):
        self.season_key = key if isinstance(key, str) else seasons.CURRENT
        self.season_rows = seasons.periods(self.root)
        if self.full_report is None and self.report is not None:
            return self.report  # a report given directly (tests) keeps its own scope
        self.report = seasons.scoped(self.full_report, seasons.resolve(self.season_key, self.season_rows),
                                     self.season_dates)
        return self.report

    def season_summary(self):
        return seasons.summary(self.full_report, self.season_dates, self.season_rows or seasons.periods(self.root))

    def _public_db(self, catalog=True):
        path = self.root / SCOPED_PUBLIC_CACHES[1 if catalog else 0]
        battle_batch.safe_path(self.root, path)
        if not path.is_file() or path.stat().st_nlink != 1:
            raise ValueError('DESKTOP_PUBLIC_CACHE_UNAVAILABLE')
        return path

    def search_cards(self, query, language='all'):
        return cards.search_cards(self._public_db(), str(query)[:200], language=language, limit=40)

    def browse_cards(self, language='fr', offset=0, limit=18):
        return cards.browse_cards(self._public_db(), language=language, offset=max(0, int(offset)), limit=limit)

    def find_cards(self, query, limit=12, batch=False):
        """Coach lookup: current TCG printings first, with export code and number.

        A batch ("Salamèche; Super Bonbon; ...") answers up to 15 names in one
        tool call; one round trip per card made a deck take minutes.
        """
        path, as_of = self._public_db(), date.today().isoformat()
        names = [name.strip() for name in re.split(r'[;\n]', str(query)) if name.strip()][:15] if batch else []
        if len(names) < 2:
            return coach_cards.find_cards(path, str(query)[:200], as_of=as_of, limit=limit)
        found = [coach_cards.find_cards(path, name[:120], as_of=as_of, limit=3) for name in names]
        return {'as_of': as_of, 'standard_basis': next((f['standard_basis'] for f in found if f.get('standard_basis')), None),
                'results': [{'query': f['query'], 'cards': f['cards'], **({'hint': f['hint']} if f.get('hint') else {})}
                            for f in found]}

    def card(self, identity, language='fr'):
        path = self._public_db()
        result = cards.show_card(path, identity, language)
        as_of = date.today().isoformat()
        verdicts, presumed = {}, {}
        for platform in ('in_person', 'live'):
            try:
                verdicts[platform] = rules.check_card(path, identity, format='standard',
                    platform=platform, as_of=as_of)
            except (ValueError, sqlite3.Error, TypeError):
                verdicts[platform] = {'status': 'unknown', 'as_of': as_of}
            try:
                presumed[platform] = coach_cards.presume_printing(path, identity, as_of=as_of,
                    platform=platform, strict=verdicts[platform])
            except (ValueError, OSError, sqlite3.Error):
                presumed[platform] = {'status': 'unknown', 'confidence': 'low'}
        result['dated_legality'] = verdicts
        # Strict verdicts stay "unknown" once the rotation's observation window
        # closes; the presumption names its basis and verification date.
        result['standard_presume'] = presumed
        return result

    def meta(self):
        return competitive.competitive_inventory(self.root, self._public_db(False), as_of=date.today().isoformat())

    def my_decks(self):
        """Decks the coach saved on the owner's request, newest first."""
        folder = battle_batch.safe_path(self.root, self.root / MY_DECKS, exists=False)
        if not folder.is_dir():
            return []
        result = []
        for path in sorted(folder.glob('deck-*.json'))[:500]:
            try:
                battle_batch.safe_path(self.root, path)
                if path.stat().st_nlink != 1 or path.stat().st_size > 65536:
                    continue
                value = json.loads(path.read_text(encoding='utf-8'))
                if (isinstance(value, dict) and isinstance(value.get('name'), str) and isinstance(value.get('export'), str)
                        and path.name == 'deck-' + battle_batch.digest(value['export']) + '.json'):
                    result.append(value)
            except (OSError, ValueError):
                continue
        return sorted(result, key=lambda d: str(d.get('saved_at', '')), reverse=True)

    def save_deck(self, name, export):
        """Create-only: one file per distinct 60-card list, never an overwrite."""
        name = ' '.join(str(name).split())[:80]
        if not name or any(not c.isprintable() for c in name):
            return {'error': 'DECK_NAME_REQUIRED'}
        validation = self.validate_deck(export)
        if validation.get('total_cards') != 60:
            return {'error': 'DECK_REQUIRES_EXACT_60', 'validation': validation}
        broken = sorted({code for verdict in (validation.get('legality') or {}).values() if isinstance(verdict, dict)
                         for code in verdict.get('structure_problems', [])})
        if broken:
            return {'error': 'DECK_RULES_VIOLATED', 'structure_problems': broken, 'validation': validation,
                    'hint': 'Corriger la liste (validate_deck) puis réessayer save_deck.'}
        folder, _ = battle_coach._directory(self.root, MY_DECKS)
        path = battle_batch.safe_path(self.root, folder / ('deck-' + battle_batch.digest(export) + '.json'), exists=False)
        if path.exists():
            existing = next((d for d in self.my_decks() if d['export'] == export), None)
            return {'status': 'ALREADY_SAVED', 'name': existing['name'] if existing else name, 'total_cards': 60}
        from datetime import datetime
        record = {'schema_version': 1, 'name': name, 'export': export, 'source': 'coach',
                  'saved_at': datetime.now().isoformat(timespec='seconds'), 'played_version_attested': False}
        battle_batch._new_file(path, (json.dumps(record, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
        self.saved_deck = name
        return {'status': 'SAVED_DECK', 'name': name, 'total_cards': 60, 'validation': validation,
                'shown_in': 'Deck Lab · Mes decks', 'legality': 'unknown', 'collection': 'unknown'}

    def deck_options(self):
        result, seen, mine = [], set(), []
        for deck in self.my_decks():
            if deck['export'] not in seen:
                seen.add(deck['export'])
                # « personnelle » keeps these out of a public-only cloud context, like registered decks.
                mine.append({'label': deck['name'], 'selector': 'mon deck · ' + str(deck.get('saved_at', ''))[:10],
                    'export': deck['export'], 'source': {}, 'kind': T('Mon deck · référence personnelle enregistrée par le coach'),
                    'legality': T('Standard / Live inconnus'), 'collection': T('Inconnue'), 'credits': T('Inconnus')})
        folder = battle_batch.safe_path(self.root, self.root / battle_coach.REPORT_DIR, exists=False)
        if folder.exists():
            pointer, _ = battle_coach._control(self.root, folder / 'latest-candidate.json')
            if pointer and re.fullmatch(r'candidate-[0-9a-f]{64}\.txt', pointer.get('file', '')):
                path = battle_batch.safe_path(self.root, folder / pointer['file'])
                if path.stat().st_size <= 12000:
                    text = path.read_text(encoding='utf-8')
                    if pointer['file'] == 'candidate-' + battle_batch.digest(text) + '.txt':
                        result.append({'label':T('Candidat enregistré · non joué'), 'selector':'latest_candidate',
                            'export':text, 'source':{}, 'kind':T('Référence personnelle · candidat non joué'),
                            'legality':T('Standard / Live inconnus'), 'collection':T('Inconnue'), 'credits':T('Inconnus')})
                        seen.add(text)
        report = self.report or {}
        for item in report.get('recommendations', []):
            for option in item.get('plan', {}).get('alternatives', []):
                text = option['export']['text']
                if text in seen:
                    continue
                seen.add(text)
                result.append({'label': J(' / ',(option['archetypes'])), 'selector': option['selector'],
                    'export': text, 'source': option.get('source', {}), 'kind': T('Référence PUBLIC'),
                    'legality': T('Standard / Live inconnus'), 'collection': T('Inconnue'), 'credits': T('Inconnus')})
        for variant in report.get('published_same_family_variants', []):
            text = variant['export']['text']
            if text not in seen:
                seen.add(text)
                result.append({'label': variant['family'] + T(' · variante'), 'selector': variant['candidate_selector'],
                    'export': text, 'source': variant['source'], 'diff': variant['diff'],
                    'kind': T('Variante PUBLIC'), 'legality': T('Standard / Live inconnus')})
        db = self.root / battle_coach.DB
        preflight = battle_batch.database_preflight(self.root, db)
        if preflight.get('integrity') == 'ok':
            # Read-only legacy support already used by the batch engine.
            for item in battle_batch.registered_decks(self.root, db, preflight, date.today().isoformat(), all_versions=True):
                result.insert(0, {'label': T('Deck enregistré · version ') + str(item['version']),
                    'selector': item['deck_id'], 'version': item['version'], 'export': item['export'], 'source': {},
                    'kind': T('Référence personnelle; version jouée non attestée'),
                    'legality': T('Standard / Live inconnus'), 'collection': T('Inconnue'), 'credits': T('Inconnus')})
        try:
            public_db = self._public_db(False)
            for group in self.meta()['compositions']:
                event, placement = group['reference'].split(':')
                text = competitive.competitive_export(self.root, public_db, event, int(placement))
                if text not in seen:
                    seen.add(text)
                    result.append({'label': J(' / ',(group['archetypes'])), 'selector': group['reference'],
                        'export': text, 'source': {'urls': group['source_urls'], 'dates': group['date_range']},
                        'kind': T('Bibliothèque PUBLIC · ') + str(group['placements']) + T(' placements observés'),
                        'legality': T('Standard / Live inconnus'), 'collection': T('Inconnue'), 'credits': T('Inconnus')})
        except (ValueError, OSError, sqlite3.Error):
            pass
        return [r | {'total': decks.parse_deck_export(r['export']).total_cards} for r in mine + result
                if decks.parse_deck_export(r['export']).total_cards == 60]

    def deck_listing(self, sharing, query='', reference=''):
        """Every deck name with its reference, whole lists while they fit, one deck's list on request.

        All the lists at once exceeded the coach tool cap, so the coach saw no deck at all
        (owner's diagnostic, 2026-11-05). References stay the deck_options() positions.
        """
        allowed = sharing == 'aggregates' and self.private_decks_allowed
        visible = [(str(i), d) for i, d in enumerate(self.deck_options()) if allowed or not personal_kind(d)]

        def row(ref, deck):
            source = deck['source']
            if isinstance(source, dict):
                source = {key: value[:3] if isinstance(value, list) else value for key, value in source.items()}
            return {'reference': ref, 'label': deck['label'], 'kind': deck['kind'], 'version': deck.get('version'),
                    'played_version_attested': False, 'source': source, 'legality': deck['legality'],
                    'collection': deck.get('collection', 'unknown'), 'total_cards': deck.get('total')}
        if reference:
            chosen = next((row(ref, d) | {'export': d['export']} for ref, d in visible if ref == reference), None)
            return {'deck': chosen} if chosen else {'error': 'DECK_REFERENCE_INVALID',
                                                    'hint': 'reference = un numéro donné par decks.'}
        if query.strip():
            wanted = query.strip().casefold()
            visible = [(ref, d) for ref, d in visible if wanted in str(d['label']).casefold()]
        result = {'decks': [], 'total': len(visible)}
        used = _bytes(result) + 300
        for ref, deck in visible:
            entry = row(ref, deck)
            size = _bytes(entry) + 2
            if used + size > TOOL_BUDGET:
                break
            result['decks'].append(entry)
            used += size
        for entry, (_, deck) in zip(result['decks'], visible):
            size = _bytes(deck['export']) + 12
            if used + size > TOOL_BUDGET:
                break
            entry['export'] = deck['export']
            used += size
        if len(result['decks']) < len(visible) or any('export' not in entry for entry in result['decks']):
            result['hint'] = ('Liste complète d’un deck : operation decks avec reference = son numéro; '
                              'query = un nom pour filtrer.')
        return result

    def compare(self, left, right):
        return competitive._quantitative_diff({'cards': competitive._card_map(left['export'])},
            {'cards': competitive._card_map(right['export'])}, 60)

    def gallery_cards(self, export):
        """Resolve exact printings with the existing PUBLIC set-code bridge."""
        from pokemind.set_code_aliases import build_aliases, alias_sets, collector_key
        parsed = decks.parse_deck_export(export)
        result = []
        try:
            connection = connect_readonly(self._public_db())
        except (OSError, ValueError, sqlite3.Error):
            connection = None
        try:
            bridge = build_aliases(connection, as_of=date.today().isoformat()) if connection else None
            for card in parsed.cards:
                identity = None
                if connection and card.set_code and card.collector_number:
                    sets, _ = alias_sets(bridge, card.set_code)
                    rows = connection.execute('SELECT p.tcgdex_id,p.local_id,t.name FROM catalog_printings p '
                        'JOIN catalog_translations t ON t.printing_id=p.tcgdex_id WHERE p.set_id IN ('
                        + ','.join('?' for _ in sets) + ')', sets).fetchall() if sets else []
                    found = {r['tcgdex_id'] for r in rows if collector_key(r['local_id']) == collector_key(card.collector_number)
                        and cards._normalized_identity_name(r['name']) == cards._normalized_identity_name(card.name)}
                    if len(found) == 1:
                        identity = found.pop()
                result.append({'name':card.name,'quantity':card.quantity,'category':card.card_type,
                    'printing':(card.set_code or '?')+' '+(card.collector_number or '?'),'identity':identity})
        finally:
            if connection:
                connection.close()
        return result

    def health(self):
        result = {}
        for name, catalog in (('catalogue', True), ('méta', False)):
            try:
                self._public_db(catalog)
                result[name] = T('Cache local disponible')
            except (OSError, ValueError):
                result[name] = T('Cache absent ou non accessible')
        result['règles'] = T('Légalité datée à vérifier pour chaque impression')
        result['sqlite'] = (self.report or {}).get('persistence', {}).get('status', T('État non consulté'))
        return result

    def context(self, question, sharing='public'):
        """Allowlisted bounded projection: no raw events, identities, paths or hashes."""
        result = {'source': 'PokeMind · services locaux en lecture seule',
            'sampling': 'Un échantillon sélectionné ne mesure pas le taux de victoire global.',
            'limits': 'Faits visibles distincts des hypothèses; légalité/collection/crédits inconnus sans preuve.',
            'features': ['analyses de combats', 'decks60', 'cartes FR/EN', 'méta datée', 'Learning Loop']}
        result['personal_report_available'] = self.report is not None
        result['source_priority'] = '1. Rapport personnel local et Learning Loop; 2. textes/règles sourcés; 3. méta publique complémentaire. Ne pas déclarer les matchs absents si personal_report_available.'
        if self.report and sharing != 'aggregates':
            result['personal_context_withheld_by_preference'] = True
            result['limits'] += ' Rapport personnel présent mais non partagé : réponse locale requise pour ses statistiques, pas de remplacement par la méta.'
        if sharing == 'aggregates' and self.report:
            report = self.report
            query_words = set(re.findall(r'[\w-]{4,}', question.casefold())) - {'contre','quels','quelle','quelles','combats','parties','défaites','statistiques','decks','dans','pour','plus','avec'}
            groups = report['groups']
            relevant = [g for g in groups if any(word in g['archetype'].casefold() for word in query_words)]
            # The families named in the question, then the 15 that beat the owner most (groups are sorted by
            # losses); the coach asks the context tool for any other family (audit A-7).
            selected_groups = relevant[:20] + [g for g in groups if g not in relevant][:MATCHUPS_SHOWN]
            result.update(as_of=report['as_of'], valid_games=report['coverage']['valid'], outcomes=report['outcomes'],
                matchups=[{**{k: g[k] for k in ('archetype', 'wins', 'losses', 'unknown', 'n')},
                    'signals': [{k: s[k] for k in ('explanation', 'loss_games', 'win_games')}
                                for s in g.get('signals', [])[:3]] if i < 5 or g in relevant else []}
                    for i,g in enumerate(selected_groups)])
            if len(groups) > len(selected_groups):
                result['matchups_not_shown'] = len(groups) - len(selected_groups)
                result['matchups_more'] = 'Autres familles : pokemind_tool operation=context, query = nom de la famille.'
            result['observed_own_decks'] = report.get('own_decks', {})
            result['own_deck_scope'] = 'Familles inférées des cartes observées, version jouée non attestée; ne pas inventer une liste exacte.'
            result['matchup_groups_total'] = len(groups)
            if report.get('season'):  # the counts above are the season shown in the app
                result['season_shown'] = {k: v for k, v in report['season'].items() if k != 'key'}
                result['seasons'] = self.season_summary()
            result['corpus_scope'] = {'kind': 'corpus enregistré volontairement sélectionné',
                'representative': False, 'global_win_rate': 'unknown',
                'pedagogical_priority': 'défaites enregistrées; ne pas confondre fréquence de collecte et force du joueur'}
            result['personal_source'] = {'kind': 'rapport canonique PokeMind validé', 'as_of': report['as_of'],
                'model_version': report.get('model_version', 'unknown'), 'internal_url': 'pokemind://page/1',
                'learning': 'Learning Loop local; observations et hypothèses distinctes'}
            if 'deck' in question.casefold():
                result['personal_decks'] = [{'version': d.get('version'), 'cards': 60,
                    'played_version_attested': False, 'collection': 'unknown'}
                    for d in self.deck_options() if d['kind'].startswith('Référence personnelle')][:20]
            # Model receives no journal excerpts or per-game transcript by default.
            result['recommendations'] = [{'archetype': r['archetype'],
                'status': r.get('status', 'Hypothèses à tester; aucun contre garanti'),
                'public_candidates': [{'archetypes': o['archetypes'], 'source': o.get('source', {})}
                    for o in r.get('plan', {}).get('alternatives', [])[:2]]}
                for r in report.get('recommendations', [])[:5]]
        if not self.personal_question(question) and any(word in question.casefold() for word in ('deck', 'méta', 'meta', 'liste', 'contre')):
            try:
                meta = self.meta()
                selected = [g for g in meta['compositions'] if any(label.casefold() in question.casefold()
                    for label in g['archetypes'])] or meta['compositions'][:10]
                result['public_decks'] = selected[:10]
                result['public_meta_scope'] = 'Placements publiés sélectionnés; aucune supériorité de matchup prouvée.'
                if selected and any(word in question.casefold() for word in ('60', 'liste', 'export')):
                    event, placement = selected[0]['reference'].split(':')
                    result['public_deck_export'] = {'reference': selected[0]['reference'],
                        'text': competitive.competitive_export(self.root, self._public_db(False), event, int(placement)),
                        'sources': selected[0]['source_urls'], 'legality': 'unknown', 'collection': 'unknown'}
            except (ValueError, OSError, sqlite3.Error):
                result['public_meta_scope'] = 'Cache PUBLIC indisponible'
        try:
            found = self.find_cards(question, limit=5)
            if found['cards']:
                result['public_cards'], result['public_cards_basis'] = [], found.get('standard_basis')
            for index, row in enumerate(found['cards']):
                entry = dict(row, internal_url='pokemind://card/' + row['tcgdex_id'] + '?lang=fr')
                if index < 2:  # full text for the best matches; the coach searches the rest itself
                    try:
                        card = self.card(row['tcgdex_id'], 'fr')
                        entry.update(effect=(card.get('effect') or '')[:2000],
                            attacks=[{k: a.get(k) for k in ('name', 'effect', 'damage')} for a in (card.get('attacks') or [])[:4] if isinstance(a, dict)],
                            abilities=[{k: a.get(k) for k in ('name', 'effect')} for a in (card.get('abilities') or [])[:3] if isinstance(a, dict)],
                            provenance=card.get('provenance'), standard_presume=card['standard_presume'],
                            french_supplements=card.get('french_text_supplements'))
                    except (ValueError, OSError, sqlite3.Error):
                        entry['source_status'] = 'Détails non disponibles; ne pas inventer le texte.'
                result['public_cards'].append(entry)
        except (ValueError, OSError, sqlite3.Error):
            pass
        # Public references can contain large nested values. The display guard
        # removes private metadata; an explicit byte cap also bounds inference.
        clean = legacy_bridge._display(result)
        if 'personal_source' in clean:
            clean['personal_source']['internal_url'] = 'pokemind://page/1'
        for card in clean.get('public_cards', []):
            identity, language = card.get('tcgdex_id', ''), card.get('language', '')
            if re.fullmatch(r'[A-Za-z0-9_-][A-Za-z0-9_.-]{0,90}', identity) and '..' not in identity and language in {'fr','en'}:
                card['internal_url'] = 'pokemind://card/' + identity + '?lang=' + language
        raw = json.dumps(clean, ensure_ascii=False)
        if len(raw.encode('utf-8')) > 24000:
            for key in ('public_cards', 'public_deck_export', 'public_decks', 'recommendations'):
                clean.pop(key, None)
        if len(json.dumps(clean, ensure_ascii=False).encode()) > 24000:
            for group in clean.get('matchups', []):
                group['signals'] = []
        if len(json.dumps(clean, ensure_ascii=False).encode()) > 24000:
            clean['matchups'] = clean.get('matchups', [])[:5]
        if len(json.dumps(clean, ensure_ascii=False).encode()) > 24000:
            clean = {k: clean[k] for k in ('source', 'personal_report_available', 'as_of', 'valid_games',
                'outcomes', 'corpus_scope', 'personal_source', 'source_priority', 'limits') if k in clean}
            clean['context_size_cap'] = True
        return clean

    def read_tool(self, arguments, sharing):
        if isinstance(arguments, dict) and 'operation' in arguments:
            return self.tool_call(arguments, sharing)
        if not isinstance(arguments, dict) or set(arguments) - {'query'}:
            return {'error': 'READ_ONLY_QUERY_REQUIRED'}
        return self.context(str(arguments.get('query', ''))[:2000], sharing)

    def match(self, reference=None):
        matches = (self.full_report or self.report or {}).get('matches', [])  # any season, e.g. the game just imported
        chosen = next((m for m in matches if m['match'] == (reference or self.selected_match)), None)
        result = chosen or (matches[-1] if matches and not reference else None)
        return dict(result, **self.played_reference(result)) if result else None

    def played_reference(self, value):
        """Reuse the attestation engine after exact source matching, read-only."""
        if not value or not value.get('source_relative'):
            return {}
        from pokemind import matchup_analytics, version_evidence
        db = self.root / battle_coach.DB
        if not db.is_file():
            return {}
        try:
            db = battle_batch.safe_path(self.root, db, expected=battle_coach.DB)
            folder = self.root / battle_coach.LOG_DIR
            path = battle_batch.safe_path(self.root, folder / value['source_relative'])
            if not path.is_relative_to(folder):
                return {}
            text, _ = battle_batch.read_selected(folder, path)
            piece = battle_batch.segments(text)[int(value.get('source_segment', 1)) - 1]
            if battle_batch.digest(battle_batch.semantic_text(piece)) != value.get('semantic_identity'):
                return {}
            digest = hashlib.sha256(piece.replace('\r\n','\n').replace('\r','\n').encode('utf-8')).hexdigest()
            with closing(connect_readonly(db)) as con:
                tables = version_evidence._tables(con)
                if not {'battle_logs','battle_deck_versions','battle_version_attestations'}.issubset(tables):
                    return {}
                rows = con.execute('SELECT * FROM battle_logs WHERE source_sha256=? AND valid=1', (digest,)).fetchall()
                if len(rows) != 1:
                    return {}
                attested = matchup_analytics._attested(con, rows[0], date.today().isoformat())
                if attested.get('version') is None:
                    return {'played_version_evidence': attested.get('status', 'unknown')}
                return {'personal_deck_version': attested['version'],
                        'battle_date': attested.get('asserted_battle_date') or 'unknown',
                        'played_version_evidence': attested['status']}
        except (ValueError, KeyError, IndexError, OSError, sqlite3.Error):
            return {}

    def reconstruct(self, match=None):
        from pokemind.opponent_observer import reconstruct
        value = match or self.match()
        if not value:
            return {'status': 'NO_SELECTED_MATCH', 'variants': []}
        index, _, scope = battle_batch.public_context(self.root, date.today().isoformat())
        return reconstruct(value.get('opponent_cards', []), index, as_of=date.today().isoformat()) | {'reference_scope': scope}

    def prepare_question(self, question, sharing, *, cancelled=None, progress=lambda value: None, log_followup=False,
                         research=False):
        """Deterministic preparation shared by every provider, before inference.

        log_followup: the owner just pasted a combat log; the coach gets that game
        and may save the opponent's rebuilt deck in « Mes decks ».
        research: the owner chose « Recherche web » for this message (never inferred
        from its words); only then is a bounded public collection made.
        """
        from pokemind import batch_public_research
        self.last_research_receipt = None
        self.saved_deck = None
        self.cancelled = cancelled
        self.research_allowed = research
        self.private_decks_allowed = bool(re.search(r'deck|liste', question, re.I))
        self.annotation_allowed = bool(re.search(r'\b(annot\w*|not\w*|confirm\w*|corrig\w*|révoqu\w*|retir\w*)\b', question, re.I))
        self.candidate_allowed = bool(SAVE_REQUEST.search(question)) or log_followup
        result = self.context(question, sharing)
        progress(T('Consultation de la mémoire publique locale'))
        from pokemind import web_memory
        try:
            remembered = web_memory.search(self.root, question)
        except (ValueError, OSError, sqlite3.Error):
            remembered = {'status': 'UNAVAILABLE'}
        if remembered.get('notes'):  # local first: what an earlier web search already found
            result['web_memory'] = remembered
        topic = 'rules' if re.search(r'règles|rules|rotation|légalité', question, re.I) else 'meta'
        if self.research_allowed:
            progress(T('Recherche publique bornée → validation → mémoire locale'))
            # If collection fails after a possible disk write, do not claim
            # either success or rollback. A completed receipt supersedes this.
            self.last_research_receipt = {'status':'ERROR', 'persisted':None}
            try:
                receipt = batch_public_research.research(self.root, as_of=date.today().isoformat(), topic=topic, cancelled=cancelled)
            except (ValueError, OSError, sqlite3.Error):
                if cancelled and cancelled():
                    self.last_research_receipt['status'] = 'INTERRUPTED'
                raise
            # Hosts own the receipt, so a model cannot claim a fake write count.
            self.last_research_receipt = receipt
            result['public_research'] = receipt
            if topic == 'meta':
                progress(T('Tournois et pairings publics → instantané du cerveau existant'))
                result['public_matchup_refresh'] = batch_public_research.research_matchups(self.root,
                    as_of=date.today().isoformat(), cancelled=cancelled)
                db = batch_public_research.matchup_database(self.root)
                if db:
                    from pokemind import meta
                    result['public_archetypes_for_matchups'] = meta.meta_archetypes(db)
                    receipt['meta_evidence'] = batch_public_research.public_meta_evidence(
                        self.root, as_of=date.today().isoformat())
        else:
            result['public_memory'] = batch_public_research.knowledge_view(self.root, as_of=date.today().isoformat(), topic=topic)
        if sharing == 'aggregates' and (self.personal_question(question) or log_followup) and self.match():
            value = self.match()
            result['selected_match'] = self.match_projection(value)
            result['owner_annotations'] = self.annotations(value['match'])
            if log_followup or re.search(r'deck|adversaire|opponent|reconstr', question, re.I):
                progress(T('Comparaison des observations aux variantes publiques60'))
                result['opponent_reconstruction'] = self.reconstruct(value)
            if 'deck' in question.casefold():
                result['registered_deck_options'] = self.tool_call({'operation': 'decks'}, sharing)
        # Keep priority totals and match facts before cutting large public lists.
        for key in ('public_research', 'public_memory'):
            if key in result:
                result[key] = dict(result[key])
                result[key].pop('history', None)
                result[key]['facts'] = result[key].get('facts', [])[:12]
        if len(json.dumps(result, ensure_ascii=False).encode()) > 100000:
            for key in ('public_memory', 'public_research'):
                if key in result:
                    result[key]['facts'] = result[key].get('facts', [])[:3]
        return result

    @staticmethod
    def match_projection(value):
        return {k: value.get(k) for k in ('outcome', 'max_observed_turn', 'opponent', 'opponent_cards',
            'own_deck_hypothesis', 'own_cards', 'personal_deck_version', 'battle_date',
            'explicit_prize_totals', 'warnings', 'causal_loss_reason')} | {
            'reference': 'selected', 'version_played_attested': value.get('personal_deck_version') not in {None, 'unknown'},
            'events': [{k: e.get(k) for k in ('sequence', 'turn', 'role', 'type', 'card', 'target', 'confidence')}
                       for e in value.get('evidence', [])[:160]],
            'source': 'PokeMind · partie sélectionnée, événements locaux anonymisés',
            'date_basis': 'battle_date unknown unless explicitly attested'}

    def tool_call(self, arguments, sharing='public'):
        from pokemind.assistant.tools import OPERATIONS
        from pokemind import batch_public_research, collection, meta
        allowed = {'operation', 'query', 'reference', 'left', 'right', 'topic', 'identity', 'export_text', 'summary', 'sources'}
        limits = {'export_text': 12000, 'summary': 4000}
        if (not isinstance(arguments, dict) or set(arguments) - allowed
                or arguments.get('operation') not in OPERATIONS
                or any(not isinstance(v, str) or len(v) > limits.get(k, 2000) for k,v in arguments.items())):
            return {'error': 'POKEMIND_TOOL_ARGUMENTS_INVALID'}
        if self.cancelled and self.cancelled():
            return {'error': 'DESKTOP_CANCELLED'}
        op, query = arguments['operation'], arguments.get('query', '')
        private = op in {'match', 'reconstruct', 'learning', 'collection', 'annotate'}
        if private and sharing != 'aggregates':
            return {'status': 'PRIVATE_CONTEXT_WITHHELD_BY_PREFERENCE', 'local_data_available': bool(self.report)}
        try:
            if op == 'context':
                return self.context(query, sharing)
            if op == 'match':
                value = self.match()
                return self.match_projection(value) if value else {'status': 'NO_SELECTED_MATCH'}
            if op == 'reconstruct':
                return self.reconstruct()
            if op == 'learning':
                return {'source': 'existing_learning_loop', 'learning': legacy_bridge._display(self.learning),
                        'owner_annotations': self.annotations(), 'causal_effect': 'unknown'}
            if op == 'annotate':
                return self.annotate(query, withdraw=arguments.get('reference') == 'withdraw')
            if op == 'validate_deck':
                return self.validate_deck(arguments.get('export_text', ''))
            if op == 'web_memory':
                from pokemind import web_memory
                return web_memory.search(self.root, query)
            if op == 'remember_web':
                # Public summaries the coach wrote from web pages: a local cache, never personal data.
                from pokemind import web_memory
                return web_memory.remember(self.root, query, arguments.get('summary', ''), arguments.get('sources', ''))
            if op == 'save_deck':
                # Create-only in the owner's own « Mes decks » (never an overwrite): no keyword gate,
                # a misspelt « crée-le » must not block it (owner, 2026-11-02). The chat shows the result.
                return self.save_deck(query, arguments.get('export_text', ''))
            if op == 'legality':
                if not arguments.get('identity'):
                    return {'error': 'IDENTITY_REQUIRED', 'hint': 'legality exige identity = tcgdex_id trouvé par cards (ex. me02-013).'}
                return self.card(arguments['identity'])
            if op == 'cards':
                return self.find_cards(query or arguments.get('identity', ''), batch=True)
            if op == 'decks':
                return self.deck_listing(sharing, query, arguments.get('reference', ''))
            if op in {'compare', 'save_candidate'}:
                options = self.deck_options()
                def option(key):
                    ref = arguments.get(key, '')
                    if not re.fullmatch('[0-9]{1,4}', ref) or int(ref) >= len(options):
                        raise ValueError('DECK_REFERENCE_INVALID')
                    value = options[int(ref)]
                    if personal_kind(value) and sharing != 'aggregates':
                        raise ValueError('PRIVATE_CONTEXT_WITHHELD')
                    return value
                left = {'export': arguments['export_text']} if op == 'save_candidate' and arguments.get('export_text') else option('left')
                if op == 'compare':
                    return self.compare(left, option('right')) | {'played_version_attested': False}
                if not self.candidate_allowed:
                    return {'error': 'CANDIDATE_REQUIRES_OWNER_REQUEST'}
                validation = self.validate_deck(left['export'])
                if validation.get('total_cards') != 60:
                    return {'error': 'CANDIDATE_REQUIRES_EXACT_60'}
                folder, _ = battle_coach._directory(self.root, battle_coach.REPORT_DIR)
                text = left['export']
                name = 'candidate-' + battle_batch.digest(text) + '.txt'
                path = battle_batch.safe_path(self.root, folder / name, exists=False)
                battle_batch._new_file(path, text.encode('utf-8'))
                pointer = folder / 'latest-candidate.json'
                _, stamp = battle_coach._control(self.root, pointer)
                battle_coach._atomic_control(self.root, pointer, {'file': name}, stamp)
                return {'status': 'SAVED_CANDIDATE', 'reference': 'latest_candidate', 'total_cards': 60,
                    'validation': validation, 'legality': 'unknown', 'played_deck_changed': False}
            if op == 'matchups':
                db = batch_public_research.matchup_database(self.root)
                if not db:
                    return {'status':'INSUFFICIENT_DATA', 'reason':'No classified public pairing snapshot available', 'winrate':None}
                if not query:
                    return meta.meta_archetypes(db)
                return meta.meta_matchups(db, query, since=(date.today().replace(day=1).isoformat()))
            if op == 'collection':
                db = battle_batch.safe_path(self.root, self.root / battle_coach.DB)
                return legacy_bridge._display(collection.collection_status(db))
            if op == 'research':
                if not self.research_allowed:
                    return {'error': 'PUBLIC_RESEARCH_REQUIRES_OWNER_REQUEST',
                            'hint': 'The owner selects « Recherche web » under the chat for a bounded public collection.'}
                if self.last_research_receipt is not None:
                    # Preparation already consumed this turn's bounded request.
                    # A provider cannot perform a second collection or overwrite
                    # the positive write receipt with a subsequent cache hit.
                    return research_view(self.last_research_receipt)
                self.last_research_receipt = {'status':'ERROR', 'persisted':None}
                result = batch_public_research.research(self.root, as_of=date.today().isoformat(),
                    topic=arguments.get('topic', 'meta'), identity=arguments.get('identity'), cancelled=self.cancelled)
                self.last_research_receipt = result
                return research_view(result)
        except (ValueError, KeyError, OSError, sqlite3.Error) as error:
            diagnostics.get('coach').warning('Outil %s refusé ou en échec : %s', op, type(error).__name__)
            return {'status': 'UNAVAILABLE_OR_INSUFFICIENT_EVIDENCE', 'operation': op,
                    'error_kind': type(error).__name__, 'detail': str(error)[:300],
                    'legality': 'unknown', 'winrate': None, 'no_private_database_migration': True}
        return {'error': 'POKEMIND_OPERATION_UNAVAILABLE'}

    def _set_aliases(self, path, as_of):
        from pokemind import set_code_aliases
        info = path.stat()
        key = (str(path), info.st_mtime_ns, info.st_size, as_of)
        if not self._aliases or self._aliases[0] != key:
            connection = connect_readonly(path)
            try:
                self._aliases = key, set_code_aliases.build_aliases(connection, as_of=as_of)
            finally:
                connection.close()
        return self._aliases[1]

    def validate_deck(self, export):
        """60-card check of a TCG Live export; problems are listed so the coach can fix them."""
        from pokemind.deck_exports import serialize_deck
        try:
            parsed = decks.parse_deck_export(export)
            serialize_deck(parsed.cards)  # validates the actual 60 and duplicate/printing constraints
        except ValueError as error:
            return {'status': 'INVALID_EXPORT', 'error': str(error)[:500],
                    'expected_format': 'Sections "Pokémon: N", "Trainer: N", "Energy: N"; '
                                       'lignes "<qté> <nom anglais> <CODE> <numéro>".'}
        as_of = date.today().isoformat()
        try:
            path = self._public_db()
        except ValueError:
            return {'total_cards': parsed.total_cards, 'as_of': as_of, 'public_cache': 'unavailable',
                    'legality': {'live': {'status': 'unknown'}, 'in_person': {'status': 'unknown'}},
                    'collection': 'unknown', 'ready_in_live': False}
        entries = [{'ordinal': index, 'card_name': c.name, 'set_code': c.set_code,
                    'collector_number': c.collector_number, 'quantity': c.quantity}
                   for index, c in enumerate(parsed.cards, 1)]
        aliases = self._set_aliases(path, as_of)
        verdicts = {}
        for platform in ('live', 'in_person'):
            try:
                strict = rules.check_deck_entries(path, entries, total_cards=parsed.total_cards,
                    exact_confirmed=parsed.total_cards == 60, format='standard', platform=platform,
                    as_of=as_of, set_aliases=aliases)
            except (ValueError, OSError, sqlite3.Error, TypeError, KeyError):
                diagnostics.get('coach').exception('Validation de deck impossible (%s)', platform)
                verdicts[platform] = {'status': 'unknown'}
                continue
            problems, statuses = [], []
            for card in strict['cards']:
                line = f"{card['quantity']} {card['card_name']} {card['set_code'] or '?'} {card['collector_number'] or '?'}"
                if len(card['tcgdex_ids']) != 1:
                    statuses.append('unknown')
                    problems.append({'line': line, 'problem': 'IMPRESSION_INTROUVABLE_OU_AMBIGUE',
                                     'hint': "Vérifier le code d'extension et le numéro avec l'opération cards."})
                    continue
                presumed = coach_cards.presume_printing(path, card['tcgdex_ids'][0], as_of=as_of,
                    platform=platform, strict=card['verdict'])
                statuses.append(presumed['status'])
                if presumed['status'] not in {'presumed_legal', 'legal'}:
                    problem = {'line': line, 'tcgdex_id': card['tcgdex_ids'][0],
                               'problem': presumed['status'], 'reason': presumed.get('reason')}
                    lead = coach_cards.playable_printing(path, card['card_name'], as_of=as_of, platform=platform)
                    if lead:
                        problem['same_name_playable_printing'] = lead + ' (même nom; vérifier le texte)'
                    problems.append(problem)
            structure = strict['structure_validation']
            # Missing or unverified structure evidence leaves the structure unknown, not violated.
            violations = [code for code in structure['reason_codes'] if code in DECK_VIOLATIONS]
            exceeded = {marker for marker, code, _ in rules.SPECIAL_CARD_LIMITS if code in violations}
            for card in strict['cards']:
                marker = rules.special_card_class(card['structure_identity'].get('rarity'))
                if marker in exceeded:
                    code, hint = SPECIAL_PROBLEMS[marker]
                    problems.append({'line': f"{card['quantity']} {card['card_name']} {card['set_code']} "
                                             f"{card['collector_number']}", 'problem': code, 'hint': hint})
            if parsed.total_cards != 60 or violations or any(s in {'presumed_not_legal', 'not_legal'} for s in statuses):
                overall = 'presumed_not_legal'
            elif statuses and all(s in {'presumed_legal', 'legal'} for s in statuses):
                overall = 'presumed_legal'
            else:
                overall = 'unknown'
            verdicts[platform] = {'status': strict['status'], 'presumed_status': overall,
                                  'structure': structure['status'], 'structure_problems': violations,
                                  'problems': problems[:30]}
        rotation = rules.latest_verified_rotation(path, format='standard', platform='live', as_of=as_of)
        return {'total_cards': parsed.total_cards, 'as_of': as_of, 'legality': verdicts,
                'presumption_basis': rules.presume_mark('?', rotation)['basis'] if rotation else None,
                'collection': 'unknown', 'ready_in_live': False}

    def _annotation_journal(self):
        """Read only the existing Learning Loop snapshot selected by its control."""
        from pokemind import learning_loop
        folder = battle_batch.safe_path(self.root, self.root / battle_coach.REPORT_DIR, exists=False)
        selected, stamp = battle_coach._control(self.root, folder / 'latest-annotations.json') if folder.exists() else (None, None)
        journal = []
        if selected:
            name = selected.get('file', '')
            if not re.fullmatch(r'annotations-[0-9a-f]{64}\.learning\.json', name):
                raise ValueError('ANNOTATION_POINTER_INVALID')
            journal, _ = legacy_bridge._json(self.root, folder / name)
            learning_loop.validate(journal)
            if name != 'annotations-' + battle_batch.digest(journal) + '.learning.json':
                raise ValueError('ANNOTATION_SNAPSHOT_CHANGED')
        return journal, stamp

    def annotations(self, reference=None):
        from pokemind import learning_loop
        journal, _ = self._annotation_journal()
        current = learning_loop.view(journal, as_of=date.today().isoformat())['current']
        return [{k:r[k] for k in ('id','kind','recorded_at','payload')} for r in current
                if r['kind'] != 'observed_game_event' and (not reference or r['payload'].get('match') == reference)]

    def annotate(self, note, *, withdraw=False):
        from pokemind import learning_loop
        if not self.annotation_allowed or not self.match() or not note.strip():
            return {'error': 'ANNOTATION_REQUIRES_OWNER_REQUEST_AND_SELECTED_MATCH'}
        folder, _ = battle_coach._directory(self.root, battle_coach.REPORT_DIR)
        pointer = folder / 'latest-annotations.json'
        journal, stamp = self._annotation_journal()
        reference = self.match()['match']
        current = [r for r in learning_loop.view(journal, as_of=date.today().isoformat())['current']
                   if r['payload'].get('match') == reference]
        parent = current[-1] if current else None
        if withdraw and not parent:
            return {'status': 'NO_ANNOTATION_TO_WITHDRAW'}
        kind = 'withdrawn' if withdraw else 'hypothesis_to_test'
        if parent and parent['kind'] == kind and parent['payload'].get('note') == note[:2000]:
            return {'status':'ALREADY_KNOWN', 'history_preserved':True, 'observed_cards_changed':False}
        if not journal:
            journal = learning_loop.append_record([], record_id='annotation-source', kind='observed_game_event',
                recorded_at=date.today().isoformat(), payload={'provenance':'owner_selected_local_match', 'match':reference},
                refs=['source:owner_selected_local_match'])
        # Source fact is immutable; only prior owner hypotheses can be revised.
        if parent and parent['kind'] == 'observed_game_event':
            parent = None
        journal = learning_loop.append_record(journal, record_id='annotation-' + str(len(journal)), kind=kind,
            recorded_at=date.today().isoformat(), payload={'match':reference,'note':note[:2000],
                'basis':'owner_annotation_not_observed_card_fact', 'reason':'Owner requested correction or withdrawal'},
            refs=[parent['id']] if parent else [journal[0]['id']], revises=parent['id'] if parent else None)
        name = 'annotations-' + battle_batch.digest(journal) + '.learning.json'
        battle_batch._new_file(folder / name, (json.dumps(journal, ensure_ascii=False, indent=2) + '\n').encode())
        battle_coach._atomic_control(self.root, pointer, {'file':name}, stamp)
        return {'status':'WITHDRAWN' if withdraw else 'SAVED_OWNER_HYPOTHESIS',
            'history_preserved':True, 'observed_cards_changed':False}

    def logs_revision(self):
        folder = self.root / battle_coach.LOG_DIR
        if not folder.exists():
            return None
        paths, refused, _ = battle_batch.files_in_folder(self.root, folder)
        return battle_batch.digest([(str(p.relative_to(folder)), p.stat().st_size, p.stat().st_mtime_ns) for p in paths] + [('refused', sorted(refused.items()))])
