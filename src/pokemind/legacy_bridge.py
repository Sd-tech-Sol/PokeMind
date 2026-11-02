"""Read-only saved-report access and schema diagnostics; no migration entry point."""
from __future__ import annotations

import copy
import html
import json
import math
import os
import re
import sqlite3
import time
import unicodedata
from collections import Counter
from contextlib import closing
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from pokemind import battle_batch, learning_loop
from pokemind.database import SCHEMA_VERSION

MAX_REPORT_BYTES = 32 * 1024 * 1024
MAX_DB_BYTES = 2 * 1024 ** 3


class BridgeError(ValueError):
    """Only fixed, non-sensitive codes cross the CLI boundary."""


def _selected(root, path, *, report=False, learning=False):
    try:
        root, path = Path(root).absolute(), Path(path).absolute()
    except (TypeError, ValueError, OSError):
        raise BridgeError('BRIDGE_EXPLICIT_PATH_REQUIRED') from None
    if report:
        if (path.parent != root / 'data/local/battle-intelligence' or path.suffix != '.json'
                or path.name.endswith('.learning.json') != learning):
            raise BridgeError('BRIDGE_REPORT_PATH_REFUSED')
    elif path != root / 'data/local/pokemind.sqlite3':
        raise BridgeError('BRIDGE_DB_PATH_REFUSED')
    try:
        return battle_batch.safe_path(root, path)
    except (ValueError, OSError):
        raise BridgeError('BRIDGE_UNSAFE_OR_MISSING_FILE') from None


def _stamp(path):
    info = path.stat()
    if not path.is_file() or info.st_nlink != 1:
        raise BridgeError('BRIDGE_UNSAFE_FILE')
    return tuple(getattr(info, key) for key in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns'))


def _bytes(root, path, *, maximum, header=False):
    before = _stamp(path)
    if before[2] > maximum:
        raise BridgeError('BRIDGE_SIZE_CAP')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        if opened.st_nlink != 1 or before != tuple(getattr(opened, k) for k in ('st_dev','st_ino','st_size','st_mtime_ns')):
            raise BridgeError('BRIDGE_SOURCE_CHANGED')
        raw = stream.read(100 if header else maximum + 1)
    battle_batch.safe_path(root, path)
    if before != _stamp(path):
        raise BridgeError('BRIDGE_SOURCE_CHANGED')
    return raw, before


def _json(root, path):
    raw, stamp = _bytes(root, path, maximum=MAX_REPORT_BYTES)
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise BridgeError('BRIDGE_DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    def constant(_):
        raise BridgeError('BRIDGE_NONFINITE_JSON')
    try:
        value = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs, parse_constant=constant)
        pending, nodes = [(value, 0)], 0
        while pending:
            item, depth = pending.pop()
            nodes += 1
            if depth > 48 or nodes > 750_000:
                raise BridgeError('BRIDGE_JSON_COMPLEXITY_CAP')
            if isinstance(item, (list, dict)):
                pending.extend((v, depth + 1) for v in (item.values() if isinstance(item, dict) else item))
            elif isinstance(item, str) and len(item) > 2_000_000:
                raise BridgeError('BRIDGE_JSON_STRING_CAP')
            elif isinstance(item, float) and not math.isfinite(item):
                raise BridgeError('BRIDGE_NONFINITE_JSON')
        return value, stamp
    except (UnicodeError, ValueError, RecursionError) as error:
        if isinstance(error, BridgeError):
            raise
        raise BridgeError('BRIDGE_INVALID_JSON') from None


def _display(value, trail=()):
    """A display projection, not a replacement immutable source journal."""
    hidden = {'semantic_identity','source_relative','source_segment','source_name','reference_player',
              'opponent_name','actor','deck_id','previous','digest','memory','encoding'}
    if isinstance(value, dict):
        return {_display(key): _display(v, (*trail, key)) for key, v in value.items()
                if key not in hidden and 'sha256' not in key.casefold()}
    if isinstance(value, list):
        return [_display(v, trail) for v in value]
    if isinstance(value, str):
        multiline = 'export' in trail
        value = ''.join(c if not unicodedata.category(c).startswith('C') else
                        ('\n' if c == '\n' and multiline else f'\\u{ord(c):04x}') for c in value)
        value = re.sub(r'(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/]|\\\\)[^\s<>]+', '[chemin masqué]', value)
        if value.startswith('/'):
            value = '[chemin masqué]'
        if trail and (trail[-1].endswith('url') or trail[-1] == 'url'):
            parsed = urlsplit(value)
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
                value = '[source non HTTPS masquée]'
        return html.escape(value, quote=False)
    return value


def _snapshot(value):
    try:
        if (not isinstance(value, dict) or value['scope'] != 'OWNER_SELECTED_FOLDER_LOCAL_ONLY'
                or value['model_version'] not in {'battle-batch-v1','battle-batch-v2','battle-batch-v3','battle-batch-v4'}
                or date.fromisoformat(value['as_of']).isoformat() != value['as_of']):
            raise ValueError
        result = copy.deepcopy(value)
        result.setdefault('published_same_family_variants', [])
        result['coverage'].setdefault('signature_only_archetype', 'unknown')
        for key in ('files_seen','valid','duplicate','refused_or_malformed','unknown_archetype'):
            if type(result['coverage'][key]) is not int or not 0 <= result['coverage'][key] <= 100_000:
                raise ValueError
        matches = result['matches']
        if not isinstance(matches, list) or len(matches) != result['coverage']['valid']:
            raise ValueError
        by_id = {}
        counts = Counter()
        for match in matches:
            if (not re.fullmatch(r'M[0-9]{4,8}', match['match']) or match['match'] in by_id
                    or match['outcome'] not in {'wins','losses','unknown'}):
                raise ValueError
            by_id[match['match']] = match
            counts[match['outcome']] += 1
        if (any(type(result['outcomes'][key]) is not int for key in ('wins','losses','unknown'))
                or result['outcomes'] != {key: counts[key] for key in ('wins','losses','unknown')}):
            raise ValueError
        grouped = []
        for group in result['groups']:
            refs = group['matches']
            selected = [by_id[ref] for ref in refs]
            if (any((m['opponent']['label'] or 'unknown') != group['archetype'] for m in selected)
                    or any(type(group[k]) is not int or group[k] != sum(m['outcome'] == k for m in selected)
                           for k in ('wins','losses','unknown'))
                    or type(group['n']) is not int or group['n'] != group['wins'] + group['losses']):
                raise ValueError
            grouped.extend(refs)
        if sorted(grouped) != sorted(by_id):
            raise ValueError
        exports, differences = [], []
        for variant in result['published_same_family_variants']:
            exports.append(variant['export']['text'])
            differences.append(variant['diff'])
        for recommendation in result['recommendations']:
            if recommendation.get('plan'):
                exports.extend(option['export']['text'] for option in recommendation['plan']['alternatives'])
                differences.extend(change['diff'] for change in recommendation['personal_swaps'].get('changes', []))
        exports.extend(fact['export'] for fact in result['fresh_public_decks'])
        if any(battle_batch.competitive.parse_deck_export(text).total_cards != 60 for text in exports):
            raise ValueError
        for difference in differences:
            counts = difference['counts']
            if (any(type(counts[k]) is not int or counts[k] < 0 for k in ('shared','removed','added'))
                    or counts['shared'] + counts['removed'] != 60
                    or counts['shared'] + counts['added'] != 60):
                raise ValueError
            for kind in ('shared','removed','added'):
                if any(type(card['quantity']) is not int or not 1 <= card['quantity'] <= 60 for card in difference[kind]):
                    raise ValueError
                if sum(card['quantity'] for card in difference[kind]) != counts[kind]:
                    raise ValueError
        # Reuse the existing renderer for the remaining nested shape contract.
        battle_batch.human_report(result)
        return result
    except (ValueError, KeyError, TypeError, AttributeError, IndexError, OverflowError, RecursionError):
        raise BridgeError('BRIDGE_INVALID_SNAPSHOT_SCHEMA') from None


def saved_report(root, *, report, learning=None):
    """Open only explicitly selected immutable values. Never discover a latest file."""
    try:
        path = _selected(root, report, report=True)
        original, stamp = _json(root, path)
        canonical = re.fullmatch(r'analysis-([0-9a-f]{64})\.json', path.name)
        if path.name.startswith('analysis-') and not canonical:
            raise BridgeError('BRIDGE_CANONICAL_NAME_INVALID')
        if canonical and battle_batch.digest(original) != canonical[1]:
            raise BridgeError('BRIDGE_SNAPSHOT_DIGEST_MISMATCH')
        value = _snapshot(original)
        selected = {k: value[k] for k in ('model_version','as_of','scope','coverage','outcomes','own_decks',
            'groups','matches','recommendations','public_reference','public_refresh','fresh_public_decks',
            'published_same_family_variants','persistence','release_status','limits')}
        selected['registered_deck_references'] = [{'version': r['version'], 'scope': r['scope']}
                                                 for r in value['registered_deck_references']]
        if value.get('revision_of'):
            selected['revision_of'] = {'model_version': value['revision_of']['model_version']}
        projection = _display(selected)
        rendered = battle_batch.human_report(projection).replace('analyse réelle locale', 'analyse conservée')
        blocked = value['persistence'].get('schema_version') == 7
        result = {'status': 'READ_ONLY_SAVED_REPORT', 'snapshot_selection': 'EXPLICIT_CANONICAL' if canonical
                  else 'EXPLICIT_NAMED_SNAPSHOT_NOT_LATEST', 'stored_as_of': value['as_of'],
                  'db_import_status': 'DB_IMPORT_BLOCKED_SCHEMA_7' if blocked else 'STORED_STATUS_NOT_RECHECKED',
                  'report': projection, 'learning': None, 'reanalysis_performed': False,
                  'database_opened': False, 'network_used': False, 'writes_performed': False}
        if learning is not None:
            learning_path = _selected(root, learning, report=True, learning=True)
            if canonical and learning_path.name != path.stem + '.learning.json':
                raise BridgeError('BRIDGE_LEARNING_SNAPSHOT_PAIR_MISMATCH')
            journal, learning_stamp = _json(root, learning_path)
            observed = next((r for r in journal if r.get('id') == 'batch-observations'), None)
            if (not observed or observed['payload'].get('version') != value['model_version']
                    or observed['payload'].get('matches') != [{k: v for k, v in m.items() if k not in {
                        'opponent','opponent_hypothesis','own_deck_hypothesis','causal_loss_reason'}} for m in value['matches']]):
                raise BridgeError('BRIDGE_LEARNING_SNAPSHOT_PAIR_MISMATCH')
            result['learning'] = _display(learning_loop.view(journal, as_of=value['as_of']))
            if _stamp(learning_path) != learning_stamp:
                raise BridgeError('BRIDGE_SOURCE_CHANGED')
        if _stamp(path) != stamp:
            raise BridgeError('BRIDGE_SOURCE_CHANGED')
        result['text'] = ('PokeMind — consultation seule; aucune nouvelle analyse ni actualisation.\n'
            + result['db_import_status'] + '\nInstantané explicite, aucune recherche du plus récent; '
            'la lecture ne prouve pas un import SQLite ou une légalité actuelle.\n' + rendered)
        return result
    except (OSError, ValueError, KeyError, TypeError, AttributeError, IndexError, RecursionError) as error:
        if isinstance(error, BridgeError):
            raise
        raise BridgeError('BRIDGE_REPORT_UNAVAILABLE_OR_INVALID') from None


MIGRATION_STEPS = (
    (8, '_migrate_attestation_schema', 'battle_version_attestations',
     'Attestations manuelles, historique/révocation et unicité de la confirmation active.'),
    (9, '_migrate_lot_a_schema', 'official_deck_structure_rules', 'Règles datées de construction.'),
    (10, '_migrate_lot_b_schema', 'collection_snapshots collection_items credit_snapshots battle_lessons deck_candidates deck_candidate_cards',
     'Collection/crédits volontaires, leçons et candidats; aucune donnée inventée.'),
    (11, '_migrate_lot_c_schema', 'training_sessions training_observations', 'Mémoire textuelle des entraînements.'),
    (12, '_migrate_lot_c_schema + _migrate_lot_d_schema', 'knowledge_update_cycles knowledge_update_source_runs public_source_observations knowledge_update_alerts',
     'Actualisations publiques; retirer l’ancienne unicité globale des observations si elle existe.'),
    (13, '_migrate_lot_f_schema', '', 'Autoriser local_vision : reconstruction de training_observations si nécessaire.'),
)


def legacy_plan(root, *, db):
    """Bounded read-only diagnostics, NOT a migration or permission to migrate."""
    if SCHEMA_VERSION != 13:
        raise BridgeError('BRIDGE_SCHEMA_CONTRACT_UPDATE_REQUIRED')
    path = _selected(root, db)
    try:
        for suffix in ('-wal','-shm','-journal'):
            if path.with_name(path.name + suffix).exists():
                raise BridgeError('BRIDGE_SIDECAR_REFUSED')
        header, before = _bytes(root, path, maximum=MAX_DB_BYTES, header=True)
        if len(header) != 100 or header[:16] != b'SQLite format 3\0':
            raise BridgeError('BRIDGE_INVALID_SQLITE_HEADER')
        if header[18:20] != b'\x01\x01':
            raise BridgeError('BRIDGE_WAL_OR_UNSUPPORTED_JOURNAL_MODE')
        deadline = time.monotonic() + 3
        with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=0.1)) as con:
            con.execute('PRAGMA query_only=ON')
            con.execute('PRAGMA trusted_schema=OFF')
            con.execute('PRAGMA foreign_keys=ON')
            con.set_progress_handler(lambda: int(time.monotonic() > deadline), 10_000)
            version = con.execute('PRAGMA user_version').fetchone()[0]
            integrity = con.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
            foreign_keys = not con.execute('PRAGMA foreign_key_check').fetchmany(1)
            contract = TABLE_COLUMNS_7 if version == 7 else TABLE_COLUMNS_13
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            missing = sorted(contract.keys() - tables)
            columns = {t: [r[1] for r in con.execute('PRAGMA table_info(' + t + ')')] for t in contract if t in tables}
            wrong_columns = sorted(t for t in columns if columns[t] != contract[t].split())
            fks = {t: {(r[3],r[2],r[4],r[6]) for r in con.execute('PRAGMA foreign_key_list(' + t + ')')}
                   for t in ('battle_logs','battle_events','card_observations','deck_version_cards','battle_deck_versions','battle_version_attestations') if t in tables}
            required_fks = {'battle_logs': {('deck_id','observed_decks','deck_id','NO ACTION')},
                'battle_events': {('battle_id','battle_logs','id','CASCADE')},
                'card_observations': {('battle_id','battle_logs','id','CASCADE'),('event_id','battle_events','id','CASCADE')},
                'deck_version_cards': {('deck_version_id','deck_versions','id','CASCADE')},
                'battle_deck_versions': {('battle_id','battle_logs','id','CASCADE'),('deck_version_id','deck_versions','id','RESTRICT')}}
            if version == SCHEMA_VERSION:
                required_fks['battle_version_attestations'] = {('battle_id','battle_logs','id','CASCADE'),('deck_version_id','deck_versions','id','RESTRICT')}
            wrong_fks = sorted(t for t, required in required_fks.items() if fks.get(t) != required)
            idx = con.execute("SELECT sql FROM sqlite_master WHERE type='index' AND name='battle_version_attestations_one_active'").fetchone()
            active_index = bool(idx and re.search(r"ON\s+battle_version_attestations\s*\(battle_id\)\s+WHERE\s+status\s*=\s*'active'\s*;?\s*$", idx[0], re.I)
                                and re.search(r'UNIQUE\s+INDEX',idx[0],re.I))
            ready_shape = not missing and not wrong_columns and not wrong_fks
            exact = con.execute('SELECT COUNT(*) FROM deck_versions v WHERE exact_confirmed=1 AND total_cards=60 '
                'AND (SELECT SUM(quantity) FROM deck_version_cards c WHERE c.deck_version_id=v.id)=60').fetchone()[0] if ready_shape else None
            legacy_links = con.execute('SELECT COUNT(*) FROM battle_deck_versions').fetchone()[0] if ready_shape else None
            training = con.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='training_observations'").fetchone()
            training_ready = bool(training and 'local_vision' in training[0]
                                  and not re.search(r'UNIQUE\s*\(session_id,\s*turn_number,\s*state_sha256\)',training[0],re.I))
        battle_batch.safe_path(root, path)
        if before != _stamp(path) or any(path.with_name(path.name + s).exists() for s in ('-wal','-shm','-journal')):
            raise BridgeError('BRIDGE_SOURCE_CHANGED')
        healthy = integrity and foreign_keys and ready_shape
        status = ('LEGACY_UPGRADE_REQUIRED' if version == 7 and healthy and not (TABLE_COLUMNS_13.keys()-TABLE_COLUMNS_7.keys()) & tables
                  else 'CURRENT_BATTLE_SCHEMA_COMPATIBLE' if version == SCHEMA_VERSION and healthy and active_index and training_ready
                  else 'BLOCKED_SCHEMA_OR_INTEGRITY')
        return {'model_version':'legacy-plan-v1','status':status,'schema_version':version,'expected_schema':SCHEMA_VERSION,
            'db_import_status':'DB_IMPORT_BLOCKED_SCHEMA_7' if version == 7 else 'SCHEMA_CHECK_ONLY_NO_IMPORT',
            'integrity_ok':integrity,'foreign_keys_ok':foreign_keys,'missing_tables':missing,
            'column_contract_mismatches':wrong_columns,'foreign_key_contract_mismatches':wrong_fks,
            'owner_attestation_index_present':active_index,'training_contract_current':training_ready,
            'post7_missing_tables':sorted(TABLE_COLUMNS_13.keys()-tables),
            'registered_exact60_count':exact,'legacy_links_not_owner_attestations':legacy_links,
            'played_version':'unknown; confirmation explicite du couple partie/version requise',
            'future_steps':[{'version':v,'existing_function':fn,'missing_tables':sorted(set(names.split())-tables),'purpose':purpose}
                            for v,fn,names,purpose in MIGRATION_STEPS],
            'risks':['initialize_schema déclenche sauvegarde/DDL et valide des étapes séparées; ne jamais l’appeler pour diagnostiquer.',
                'Les tables d’entraînement peuvent être reconstruites avec foreign_keys temporairement OFF; rollback par étape ≠ retour global.',
                'Aucune nouvelle sauvegarde autorisée. Les preuves de récupération existantes et l’accès exclusif exigent une revue distincte.',
                'Ne pas hausser user_version seul ni déduire une version jouée par date ou recouvrement de cartes.',
                'Les qualificatifs d’ambiguïté sont conservés au parsing; confiance SQL low selon le CHECK high/medium/low existant.'],
            'migration_executed':False,'backup_created':False,'import_performed':False,'network_used':False,'writes_performed':False}
    except (OSError, sqlite3.DatabaseError, ValueError) as error:
        if isinstance(error, BridgeError):
            raise
        raise BridgeError('BRIDGE_DATABASE_UNAVAILABLE_OR_INVALID') from None


def human_legacy_plan(result):
    return ('PokeMind — diagnostic seul; aucune migration, sauvegarde ou écriture.\n'
        + result['status'] + '\n' + result['db_import_status']
        + f"\nSchéma {result['schema_version']} → {result['expected_schema']}; intégrité={result['integrity_ok']}; FK={result['foreign_keys_ok']}.\n"
        + 'Tables manquantes vers13 : ' + ', '.join(result['post7_missing_tables']) + '\n'
        + 'Contrats de colonnes incompatibles : ' + ', '.join(result['column_contract_mismatches']) + '\n'
        + 'Contrats de FK incompatibles : ' + ', '.join(result['foreign_key_contract_mismatches']) + '\n'
        + f"Index d’attestation active : {result['owner_attestation_index_present']}; contrat d’entraînement13 : {result['training_contract_current']}.\n"
        + '\n'.join(f"  {s['version']} : {s['purpose']}" for s in result['future_steps'])
        + f"\nRéférences exactes60 : {result['registered_exact60_count']}; version jouée inconnue, confirmation propriétaire distincte requise.\n"
        + '\n'.join('Précaution : '+r for r in result['risks'])
        + '\nAucune autorisation de migration personnelle. V1 NOT_RELEASE_READY.\n')

# Contracts derived from tracked schema DDL; FTS internal tables excluded.
TABLE_COLUMNS_7 = {
    'battle_deck_versions': 'battle_id deck_version_id effective_from approved_at',
    'battle_events': 'id battle_id sequence turn_number actor actor_role event_type card_name evidence confidence',
    'battle_logs': 'id source_sha256 imported_at parser_version source_kind source_name reference_player opponent_name outcome winner valid deck_id max_turn recognized_events warnings_json',
    'card_observations': 'id battle_id event_id owner_role card_name observation_type turn_number confidence',
    'catalog_printings': 'tcgdex_id set_id local_id category hp stage regulation_mark rarity illustrator types_json variants_json brief_sha256_en brief_sha256_fr detail_stale_en detail_stale_fr discovered_at updated_at brief_source_url brief_retrieved_at',
    'catalog_refresh_state': 'scope next_page in_progress end_candidate_page head_probe_done cycle_started_at last_completed_at requests_total pages_scanned_current items_seen_current new_items_current changed_items_current last_success_at last_failure_at last_error updated_at',
    'catalog_sets': 'tcgdex_id name_en name_fr series_id release_date card_count_total card_count_official tcg_online_code abbreviation_official abbreviation_localized discovered_at updated_at source_url_en source_url_fr retrieved_at_en retrieved_at_fr detail_status_en detail_status_fr content_sha256_en content_sha256_fr brief_sha256_en brief_sha256_fr detail_stale_en detail_stale_fr last_error_en last_error_fr',
    'catalog_sync_state': 'scope next_page completed requests_total end_candidate_page started_at completed_at last_success_at last_failure_at last_error updated_at',
    'catalog_translations': 'id printing_id language status name category description effect trainer_type energy_type abilities_json attacks_json weaknesses_json resistances_json retreat source_url retrieved_at payload_sha256 last_error',
    'deck_version_cards': 'id deck_version_id ordinal source_line card_type quantity card_name set_code collector_number normalized_line',
    'deck_versions': 'id deck_id version_number imported_at approved_at effective_from parser_version source_kind source_name source_encoding export_sha256 list_sha256 total_cards entry_count exact_confirmed sections_json coverage_json raw_stored',
    'documents': 'id document_key title path source_date content_sha256 imported_at',
    'meta_games': 'game_id name metagame formats_json platforms_json source_url fetched_at payload_sha256',
    'meta_matches': 'tournament_id match_key phase round table_number match_label participant1_ref participant2_ref outcome eligible exclusion_reason',
    'meta_phases': 'tournament_id phase phase_type rounds mode',
    'meta_placements': 'tournament_id participant_ref placing wins losses ties dropped_round archetype_id archetype_name archetype_published',
    'meta_sync_state': 'scope source_url state fetched_at payload_sha256 requests_total last_error updated_at',
    'meta_tournaments': 'tournament_id name date_utc game format platform is_online is_public provider_status participant_count decklists_enabled special_rules_json banned_cards_count source_url fetched_at payload_sha256 snapshot_status',
    'metadata': 'key value',
    'observed_decks': 'deck_id status created_at last_seen_at',
    'official_rule_assertions': 'assertion_id source_id assertion_kind format platform effective_from effective_to subject_id payload_json validation_status confidence captured_at',
    'official_rule_sources': 'source_id source_type url title language published_date consulted_at captured_at content_sha256 validation_status effective_from effective_to rights_note notes',
    'sections': 'id document_id ordinal heading heading_path heading_level start_line end_line char_start char_end content content_sha256',
}

TABLE_COLUMNS_13 = {
    'battle_deck_versions': 'battle_id deck_version_id effective_from approved_at',
    'battle_events': 'id battle_id sequence turn_number actor actor_role event_type card_name evidence confidence',
    'battle_lessons': 'id battle_id deck_id created_at lesson_kind note_text confidence provenance evidence_ref public_source_url public_source_date dedup_key status',
    'battle_logs': 'id source_sha256 imported_at parser_version source_kind source_name reference_player opponent_name outcome winner valid deck_id max_turn recognized_events warnings_json',
    'battle_version_attestations': 'id battle_id deck_version_id confirmed_at actor provenance asserted_battle_date battle_date_source battle_date_reliability status revoked_at reason revocation_reason',
    'card_observations': 'id battle_id event_id owner_role card_name observation_type turn_number confidence',
    'catalog_printings': 'tcgdex_id set_id local_id category hp stage regulation_mark rarity illustrator types_json variants_json brief_sha256_en brief_sha256_fr detail_stale_en detail_stale_fr discovered_at updated_at brief_source_url brief_retrieved_at',
    'catalog_refresh_state': 'scope next_page in_progress end_candidate_page head_probe_done cycle_started_at last_completed_at requests_total pages_scanned_current items_seen_current new_items_current changed_items_current last_success_at last_failure_at last_error updated_at',
    'catalog_sets': 'tcgdex_id name_en name_fr series_id release_date card_count_total card_count_official tcg_online_code abbreviation_official abbreviation_localized discovered_at updated_at source_url_en source_url_fr retrieved_at_en retrieved_at_fr detail_status_en detail_status_fr content_sha256_en content_sha256_fr brief_sha256_en brief_sha256_fr detail_stale_en detail_stale_fr last_error_en last_error_fr',
    'catalog_sync_state': 'scope next_page completed requests_total end_candidate_page started_at completed_at last_success_at last_failure_at last_error updated_at',
    'catalog_translations': 'id printing_id language status name category description effect trainer_type energy_type abilities_json attacks_json weaknesses_json resistances_json retreat source_url retrieved_at payload_sha256 last_error',
    'collection_items': 'id snapshot_id ordinal supplied_tcgdex_id resolved_tcgdex_id card_name set_code collector_number variant quantity ownership_status resolution_status resolution_reason',
    'collection_snapshots': 'id recorded_at as_of source_kind source_name content_sha256 status supersedes_id rollback_of_id entry_count total_quantity resolved_count ambiguous_count unknown_count',
    'credit_snapshots': 'id recorded_at as_of amount source_kind status supersedes_id rollback_of_id',
    'deck_candidate_cards': 'id candidate_id ordinal card_type quantity card_name set_code collector_number tcgdex_id identity_status',
    'deck_candidates': 'id name created_at base_deck_id base_version_id format platform as_of source_kind change_sha256 list_sha256 validation_status validation_json lifecycle_status exported_at export_text_path export_report_path',
    'deck_version_cards': 'id deck_version_id ordinal source_line card_type quantity card_name set_code collector_number normalized_line',
    'deck_versions': 'id deck_id version_number imported_at approved_at effective_from parser_version source_kind source_name source_encoding export_sha256 list_sha256 total_cards entry_count exact_confirmed sections_json coverage_json raw_stored',
    'documents': 'id document_key title path source_date content_sha256 imported_at',
    'knowledge_update_alerts': 'id cycle_id created_at source severity code message status',
    'knowledge_update_cycles': 'cycle_id mode scope_json scheduled_local_date started_at_utc started_at_local completed_at_utc status timezone request_budget requests_attempted report_json error_code config_sha256',
    'knowledge_update_source_runs': 'id cycle_id source state started_at_utc completed_at_utc request_budget requests_attempted new_count changed_count missing_count unknown_count source_url captured_at validation_status reason_code detail_json',
    'meta_games': 'game_id name metagame formats_json platforms_json source_url fetched_at payload_sha256',
    'meta_matches': 'tournament_id match_key phase round table_number match_label participant1_ref participant2_ref outcome eligible exclusion_reason',
    'meta_phases': 'tournament_id phase phase_type rounds mode',
    'meta_placements': 'tournament_id participant_ref placing wins losses ties dropped_round archetype_id archetype_name archetype_published',
    'meta_sync_state': 'scope source_url state fetched_at payload_sha256 requests_total last_error updated_at',
    'meta_tournaments': 'tournament_id name date_utc game format platform is_online is_public provider_status participant_count decklists_enabled special_rules_json banned_cards_count source_url fetched_at payload_sha256 snapshot_status',
    'metadata': 'key value',
    'observed_decks': 'deck_id status created_at last_seen_at',
    'official_deck_structure_rules': 'rule_id source_id format platform effective_from effective_to payload_json validation_status confidence captured_at',
    'official_rule_assertions': 'assertion_id source_id assertion_kind format platform effective_from effective_to subject_id payload_json validation_status confidence captured_at',
    'official_rule_sources': 'source_id source_type url title language published_date consulted_at captured_at content_sha256 validation_status effective_from effective_to rights_note notes',
    'public_source_observations': 'id source_id source_url observed_at http_status content_type content_length etag last_modified content_sha256 truncated observation_state validation_status',
    'sections': 'id document_id ordinal heading heading_path heading_level start_line end_line char_start char_end content content_sha256',
    'training_observations': 'id session_id turn_number recorded_at source_kind confidence state_json state_sha256 status revision_of_id',
    'training_sessions': 'session_id created_at closed_at status mode format platform context_date image_storage assistance_scope',
}
