"""Wire definitions and local routing for the single PokeMind conversation."""
from __future__ import annotations

import json
import re
import sqlite3
import time

OPERATIONS = ('context', 'match', 'reconstruct', 'decks', 'compare', 'learning',
              'cards', 'legality', 'matchups', 'collection', 'research', 'save_candidate', 'validate_deck', 'annotate', 'save_deck')
READ_TOOL = {'type': 'function', 'name': 'pokemind_read',
    'description': 'Consulter les services PokeMind en lecture seule, avec sources et date. Aucun chemin ou SQL.',
    'inputSchema': {'type': 'object', 'properties': {'query': {'type': 'string', 'maxLength': 2000}},
                    'required': ['query'], 'additionalProperties': False}}
TOOL = {'type': 'function', 'name': 'pokemind_tool',
    'description': ('Consulter le cerveau PokeMind existant. cards : chercher des cartes par nom FR/EN, '
        'plusieurs noms séparés par ";" dans query (jusqu\'à 15 par appel; impressions jouables d\'abord, '
        'avec ligne d\'export TCG Live); legality : fiche et légalité datée '
        '(identity = tcgdex_id); validate_deck : vérifier une liste TCG Live de 60 cartes (export_text). '
        'Les références de partie/deck proviennent '
        'des résultats précédents. Research conserve des observations publiques avec reçu local et statut de validation distinct; save_candidate '
        'conserve une proposition60 locale distincte du deck joué, seulement sur demande utilisateur. '
        'save_deck : enregistre une liste de 60 cartes dans « Mes decks » de PokeMind (query = nom du deck, '
        'export_text = liste TCG Live), quand le propriétaire demande de créer ou d\'enregistrer un deck ou colle un journal.'),
    'inputSchema': {'type': 'object', 'properties': {
        'operation': {'type': 'string', 'enum': list(OPERATIONS)},
        'query': {'type': 'string', 'maxLength': 2000},
        'reference': {'type': 'string', 'maxLength': 160},
        'left': {'type': 'string', 'maxLength': 160},
        'right': {'type': 'string', 'maxLength': 160},
        'topic': {'type': 'string', 'enum': ['meta', 'rules', 'card']},
        'identity': {'type': 'string', 'maxLength': 90},
        'export_text': {'type': 'string', 'maxLength': 12000}},
        'required': ['operation'], 'additionalProperties': False}}
# Every engine (Codex, Claude, a local model) receives exactly these tools.
COACH_TOOLS = (READ_TOOL, TOOL)
MAX_TOOL_BYTES = 24000


def run_tool(name, arguments, handler):
    """Execute a coach tool call identically for every engine; returns (value, success).

    Each call is journaled (tool, operation, outcome, size), never its query
    or result, so a failing tool is visible in « Copier le diagnostic ».
    """
    from pokemind import diagnostics
    started, operation = time.monotonic(), '?'
    if name not in {tool['name'] for tool in COACH_TOOLS} or handler is None:
        value = {'error': 'UNKNOWN_TOOL'}
    else:
        try:
            if isinstance(arguments, str):
                arguments = json.loads(arguments or '{}')
            arguments = arguments if isinstance(arguments, dict) else {}
            operation = str(arguments.get('operation', 'query'))[:40]
            value = handler(arguments)
            if len(json.dumps(value, ensure_ascii=False).encode()) > MAX_TOOL_BYTES:
                value = {'error': 'CONTEXT_SIZE_CAP',
                         'hint': 'Réponse trop longue; préciser la requête (nom exact, une opération à la fois).'}
        except (ValueError, OSError, TypeError, KeyError, sqlite3.Error) as error:
            diagnostics.get('coach').warning('Outil %s/%s en échec : %s', name, operation, type(error).__name__)
            value = {'error': 'READ_SERVICE_UNAVAILABLE', 'error_kind': type(error).__name__}
    success = not (isinstance(value, dict) and 'error' in value)
    outcome = 'ok' if success else value.get('error')
    if isinstance(value, dict) and value.get('status') in {'UNAVAILABLE_OR_INSUFFICIENT_EVIDENCE', 'INVALID_EXPORT'}:
        outcome = value['status']
    diagnostics.get('coach').info('Outil %s/%s · %s · %d o · %.2f s', name, operation, outcome,
                                  len(json.dumps(value, ensure_ascii=False).encode()), time.monotonic() - started)
    return value, success


# Starters that only make sense with a bounded public collection: picking one selects « Recherche web ».
RESEARCH_STARTERS = ('Cherche les changements récents de la méta et mémorise-les.',)
STARTERS = (
    'Analyse mon dernier combat.', 'Reconstruis le deck de mon dernier adversaire.',
    'Pourquoi je perds contre Dragapult?', 'Quelles sont mes erreurs récurrentes?',
    'Compare mon deck aux meilleures listes actuelles.',
    'Propose trois modifications pour contrer ce deck.',
    'Quel deck devrais-je jouer selon ma collection?', 'Prépare-moi un deck 60/60 prêt à copier.',
    'Entraîne-moi à gérer mon Banc et mes Énergies.',
    *RESEARCH_STARTERS,
    'Quelle est la prochaine amélioration utile de PokeMind?', 'Affiche mon statut Codex.')


def slash(question):
    text = question.strip()
    if re.fullmatch(r'(?:affiche\s+)?(?:mon\s+)?statut\s+codex[.!?]?', text, re.I):
        return 'status'
    if not text.startswith('/'):
        return None
    return text.split(maxsplit=1)[0][1:].lower()
