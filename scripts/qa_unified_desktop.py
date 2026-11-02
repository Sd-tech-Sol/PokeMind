"""Manual synthetic Windows release QA, reused inside the dedicated portable.

Prepare a fresh fixture with --prepare-release; build with
Build-PokeMindDesktop.ps1 -SyntheticQaRoot <the printed relative root>.
Normal application launches never import or execute this harness.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sqlite3
import sys
import time
import re
import unicodedata
import uuid
from contextlib import closing
from datetime import date
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox
from pokemind import batch_public_research as research
from pokemind.assistant.sessions import Store
from pokemind.battle_batch import safe_path
from pokemind.decks import parse_deck_export
from pokemind.desktop.app import synthetic_release_root
from pokemind.desktop.window import MainWindow
from pokemind.assistant.receipts import public_memory_message, public_memory_record, public_research_message


LOG = ("Reference player: InventedSelf\nTurn # 1 - InventedSelf's Turn\n"
       "InventedSelf played Creature Alpha.\nTurn # 2 - InventedRival's Turn\n"
       "InventedRival played Creature Beta.\nInventedRival wins.\n")


def prepare_release(root):
    """Use existing synthetic builders; never reuse any previous local corpus."""
    from pokemind.synthetic_qa import optional
    context = optional()
    container = context.validate_live() if context else root
    target = safe_path(root, container / ('build/synthetic-release-' + uuid.uuid4().hex), exists=False)
    target.mkdir(parents=True)
    (target / '.orchestrator').mkdir()
    (target / '.orchestrator/SYNTHETIC_QA_ONLY').write_bytes(b'POKEMIND_SYNTHETIC_RELEASE_QA_V1\n')
    (target / '.orchestrator/PROJECT_SPEC.md').write_text('# Entirely invented release QA\n', encoding='utf-8')
    tests = Path(__file__).resolve().parents[1] / 'tests'
    sys.path.insert(0, str(tests))
    try:
        builders = importlib.import_module('test_deck_knowledge')
        public_db, reference_db = builders.enriched(target)
    finally:
        sys.path.remove(str(tests))
    for source, relative in zip((public_db, reference_db), importlib.import_module('pokemind.public_deck_preflight').SCOPED_PUBLIC_CACHES):
        destination = safe_path(target, target / relative, exists=False)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
        # Qualification binds the marker to the destination campaign name and
        # verifies indexed source pages; copying the DB alone is insufficient.
        destination.with_name('PUBLIC_ONLY.json').write_text(json.dumps({
            'kind':'pokemind_public_only_lot_i',
            'campaign':destination.parent.name.removeprefix('lot-i-'),
            'schema_version':1}),encoding='utf-8')
        ledger = source.with_name('requests.json')
        if ledger.is_file():
            destination.with_name('requests.json').write_bytes(ledger.read_bytes())
            pages = destination.parent / 'pages'
            pages.mkdir()
            for entry in json.loads(ledger.read_text(encoding='utf-8'))['requests']:
                name = entry['sha256'] + '.body'
                (pages/name).write_bytes((source.parent/'pages'/name).read_bytes())
    from pokemind.battle_batch import public_context
    index, _, _ = public_context(target,date.today().isoformat())
    assert index and index['references'], 'SYNTHETIC_PUBLIC_FIXTURE_NOT_QUALIFIED'
    db = target / 'data/local/pokemind.sqlite3'
    db.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db)) as con:
        con.executescript((tests / 'fixtures/legacy_schema7.sql').read_text(encoding='utf-8'))
    (target / 'qa-inputs').mkdir()
    deck = (tests / 'fixtures/decks/valid_en.txt').read_text(encoding='utf-8')
    (target / 'qa-inputs/deck60.txt').write_text(deck, encoding='utf-8')
    from pokemind.desktop import ingestion
    from pokemind.desktop.services import Services
    ingestion.ingest(target, LOG.replace('InventedRival wins.', 'InventedSelf wins.'))
    service = Services(target)
    service.candidate_allowed = True
    assert service.tool_call({'operation':'save_candidate','export_text':deck}, 'aggregates')['status'] == 'SAVED_CANDIDATE'
    store = Store(target)
    store.write('preferences.json', store.preferences() | {'cloud_consent':True,'sharing':'aggregates','card_images':False})
    return target


class InventedOfficialResponse:
    status = 200
    def __init__(self, url):
        self.url = url
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def geturl(self): return self.url
    def read(self, maximum):
        return (b'User-agent: *\nAllow: /\n' if self.url.endswith('/robots.txt')
                else (b'<html><head><meta property="article:published_time" content="2025-02-01"></head>'
                      b'<body><article><p>In the Standard format for TCG Live, regulation marks Q, R '
                      b'are allowed starting 2025-03-01.</p></article></body></html>'))[:maximum]


class InventedOfficialOpener:
    def __init__(self): self.calls = 0
    def open(self, request, timeout):
        assert request.full_url.startswith('https://www.pokemon.com/')
        self.calls += 1
        return InventedOfficialResponse(request.full_url)


def memory_consistency_gate(receipt, message, rendered, saved, provider_text=''):
    """Fail closed on a suffix-only response, an unsaved receipt or a known denial.

    Host-only presentation guarantees arbitrary model prose cannot contradict
    the visible result. The additional real-provider denial check is a QA
    tripwire for the demonstrated failure, not a language safety filter.
    """
    record = public_memory_record(receipt)
    canonical = public_memory_message(record)
    normalized = ''.join(c for c in unicodedata.normalize('NFD', provider_text.casefold())
                         if not unicodedata.combining(c))
    denial = re.search(r"rien n['’]a ete memorise|aucune memorisation|aucun(?:e)? .{0,30}(?:memorise|enregistre)|"
                       r"(?:n['’]ai|n['’]a) (?:rien|pas) .{0,35}(?:memorise|enregistre)|"
                       r"(?:nothing|not) (?:was |been |actually )?(?:saved|stored|memorized)", normalized)
    if receipt.get('persisted') and receipt.get('added', 0) > 0 and denial:
        return False
    return (message.get('memory_receipt') == record and message.get('content', '').endswith(canonical)
            and saved == message and all(line in rendered for line in canonical.splitlines()))


def research_answer_gate(receipt, question, message, rendered, saved):
    """Receipt-only answers must fail even when every write count is correct."""
    canonical = public_research_message(receipt, question)
    return (message.get('content') == canonical and saved == message
            and 'Pistes conditionnelles' in canonical
            and all(line in rendered for line in canonical.splitlines()))


def source_depth_gate(receipt, message, rendered, saved):
    """Independent semantic tripwire: metadata-only must fail this QA fixture."""
    expected = ('Q, R', '2025-02-01', '2025-03-01', 'TCG Live',
                'extracted_unverified', 'application courante : unknown',
                'réimpression : unknown', 'disponibilité dans Live : unknown')
    return (saved==message and any(f.get('rule_evidence',{}).get('status')=='extracted_unverified'
            for f in receipt.get('facts',[]))
            and all(s in message.get('content','') and s in rendered for s in expected))


def exercise_release(app, first_window):
    fixture = synthetic_release_root(first_window.root)
    if app.platformName() != 'windows':
        raise ValueError('WINDOWS_NATIVE_PLATFORM_REQUIRED')
    app.setQuitOnLastWindowClosed(False)
    opener = InventedOfficialOpener()
    original_research = research.research
    def invented_research(root, **kwargs):
        assert Path(root).absolute() == fixture and kwargs.get('topic') == 'rules'
        policy = {'mode':'derived_fields_only','license':'synthetic_author_owned',
                  'reference':'invented-qa-license-v1'}
        result = original_research(root, **(kwargs | {'opener':opener,
            'official_policy':{url:policy for url in (
                'https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources',
                'https://www.pokemon.com/us/pokemon-news/2026-pokemon-tcg-standard-format-rotation-announcement')}}))
        state['last_receipt'] = result
        return result
    research.research = invented_research
    original_matchups = research.research_matchups
    def forbidden_matchups(*args, **kwargs):
        raise ValueError('SYNTHETIC_QA_FORBIDS_REAL_PUBLIC_COLLECTION')
    research.research_matchups = forbidden_matchups
    state = {'step':0, 'start':time.monotonic(), 'w':first_window, 'windows':[first_window], 'calls':0,
             'proof':{'native_windows':True,'frozen':bool(getattr(sys,'frozen',False)), 'synthetic_only':True}}
    db_before = (fixture / 'data/local/pokemind.sqlite3').read_bytes()

    def send(text):
        w = state['w']
        w.chat_input.setPlainText(text)
        QTest.mouseClick(w.send_button, Qt.MouseButton.LeftButton)

    def answer_dialog(answer, *, check_default=False):
        def click():
            dialog = QApplication.activeModalWidget()
            assert isinstance(dialog, QMessageBox)
            if check_default:
                state['proof']['consent_default_no'] = dialog.defaultButton() == dialog.button(QMessageBox.StandardButton.No)
            QTest.mouseClick(dialog.button(answer), Qt.MouseButton.LeftButton)
        QTimer.singleShot(40, click)

    def finish(ok, code='OK'):
        state['proof'].update(ok=ok,code=code,real_public_gets=0,invented_source_calls=opener.calls,
            legacy_fixture_unchanged=(fixture/'data/local/pokemind.sqlite3').read_bytes()==db_before)
        (fixture/'reception.json').write_text(json.dumps(state['proof'],indent=2),encoding='utf-8')
        research.research, research.research_matchups = original_research, original_matchups
        for w in state['windows']:
            w.close()
        timer.stop()
        app.exit(0 if ok else 2)

    def step():
        w, p, stage = state['w'], state['proof'], state['step']
        if time.monotonic()-state['start'] > 600:
            if w.chat_busy: w.stop_chat()
            if not w.chat_busy and not w.jobs: finish(False,'QA_TIMEOUT')
            return
        if stage == 0 and not w.jobs:
            p['one_visible_conversation'] = w.isVisible() and w.stack.count()==6 and len(w.findChildren(type(w.chat_input)))==1
            p['standard_risk_visible'] = 'privées accessibles' in w.permission_badge.text()
            adapter = w.get_adapter()
            original = adapter.ask_stream
            def observe(prompt, history, emit, tool=None):
                state['calls'] += 1
                if not adapter.development:
                    assert LOG not in prompt and 'Reference player:' not in prompt and 'InventedRival' not in prompt
                    assert not any('Reference player:' in m['content'] for m in history)
                    p['raw_log_and_identity_excluded'] = True
                def observed_delta(text):
                    if '"public_research":' in prompt:
                        state['memory_provider_text'] = state.get('memory_provider_text','') + text
                    emit(text)
                return original(prompt,history,observed_delta,tool)
            adapter.ask_stream = observe
            send('Explique les Récompenses en une phrase; cite la limite des données disponibles.')
            state['step']=1
        elif stage == 1 and not w.chat_busy:
            p['real_codex_pokemon_answer'] = not w.chat_failed and bool(w.conversation['messages'][-1]['content'])
            send(LOG+'\nPourquoi cette défaite? Reconstruis son deck comme hypothèse et cite tes sources. Réponse brève.')
            state['step']=2
        elif stage == 2 and not w.chat_busy and not w.ingest_busy:
            p['one_send_import_and_answer'] = not w.chat_failed and bool(w.conversation.get('selected_match'))
            reconstruction = w.services.reconstruct()
            p['hypothesis60_sourced_not_certain'] = bool(reconstruction['variants']) and all(
                v['total_cards']==60 and not v['is_exact_opponent_deck'] and v['probability'] is None
                and v['source']['source_urls'] for v in reconstruction['variants'])
            p['match_summary_real_engine'] = w.services.report['coverage']['valid']==2 and bool(w.services.match())
            state['before_status_calls']=state['calls']
            send('/status');state['step']=3
        elif stage == 3 and not w.chat_busy:
            p['official_status_without_inference'] = state['calls']==state['before_status_calls'] and 'Codex App Server' in w.conversation['messages'][-1]['content']
            prior = json.dumps(w.conversation)
            question = 'Crée le fichier ui-proof.txt contenant INVENTED_UI puis teste son contenu avec Python assert; utilise pokemind_project, aucun autre fichier.'
            state['step']='dialog'
            answer_dialog(QMessageBox.StandardButton.No,check_default=True)
            send(question)
            p['consent_refusal_preserves_draft_history'] = w.chat_input.toPlainText()==question and json.dumps(w.conversation)==prior and not w.chat_busy
            answer_dialog(QMessageBox.StandardButton.Yes)
            send(question);state['step']=4
        elif stage == 4 and not w.chat_busy:
            p['real_project_edit_and_test_same_chat'] = (fixture/'ui-proof.txt').read_text(encoding='utf-8').strip()=='INVENTED_UI' and (w.adapter.last_command_result or {}).get('exitCode')==0
            state['id']=w.conversation['id']
            state['step']='dialog'
            # Full mode is only selected in this entirely invented workspace.
            answer_dialog(QMessageBox.StandardButton.Yes)
            w.permission_mode.setCurrentIndex(1)
            p['full_risk_visible'] = 'ACCÈS COMPLET' in w.permission_badge.text() and 'privées accessibles' in w.permission_badge.text()
            answer_dialog(QMessageBox.StandardButton.No)
            p['full_scope_requires_separate_consent'] = not w.acknowledge_development_privacy()
            w.permission_mode.setCurrentIndex(0)
            w.revoke_development_privacy()
            answer_dialog(QMessageBox.StandardButton.No)
            p['revocation_requires_new_consent'] = not w.acknowledge_development_privacy()
            state['research_question'] = 'Cherche les règles pour cette QA fictive puis explique leurs implications; mémorise les sources comme non vérifiées.'
            send(state['research_question'])
            state['step']=5
        elif stage == 5 and not w.chat_busy:
            facts=research.knowledge_view(fixture,as_of=date.today().isoformat(),topic='rules')['facts']
            message = w.conversation['messages'][-1]
            saved = w.store.load(w.conversation['id'])['messages'][-1]
            # Invented/public QA only, retained locally for human semantic
            # inspection as well as the known-denial tripwire. Never published.
            (fixture/'memory-provider-commentary.txt').write_text(state.get('memory_provider_text',''),encoding='utf-8')
            p['memory_response_consistency'] = memory_consistency_gate(state['last_receipt'],message,
                w.transcript.toPlainText(),saved,state.get('memory_provider_text',''))
            if not p['memory_response_consistency']:
                finish(False,'MEMORY_RESPONSE_CONSISTENCY_FAILED')
                return
            p['research_answer_usefulness'] = research_answer_gate(state['last_receipt'],state['research_question'],
                message,w.transcript.toPlainText(),saved)
            if not p['research_answer_usefulness']:
                finish(False,'RESEARCH_ANSWER_USEFULNESS_FAILED')
                return
            p['public_source_depth'] = source_depth_gate(state['last_receipt'],message,
                w.transcript.toPlainText(),saved)
            if not p['public_source_depth']:
                finish(False,'PUBLIC_SOURCE_DEPTH_FAILED')
                return
            p['public_receipt_persisted_not_normative'] = bool(facts) and all(f['validation']=='unverified' for f in facts) and p['memory_response_consistency']
            state['memory_message'] = message
            state['gets_before_restart']=opener.calls
            state['step']=5.5
        elif stage == 5.5:
            # Inspect the memory result itself, after the native paint cycle,
            # instead of relying only on the final unrelated Claude turn.
            cursor = w.transcript.document().find('Réponse PokeMind — règles et implications')
            assert not cursor.isNull(), 'MEMORY_RECEIPT_NOT_RENDERED'
            w.transcript.setTextCursor(cursor)
            w.transcript.ensureCursorVisible()
            w.transcript.viewport().repaint()
            w.grab().save(str(fixture/'research-answer-reception.png'))
            cursor = w.transcript.document().find('Résultat PokeMind — mémoire publique')
            assert not cursor.isNull(), 'MEMORY_RECEIPT_NOT_RENDERED'
            w.transcript.setTextCursor(cursor)
            w.transcript.ensureCursorVisible()
            w.transcript.viewport().repaint()
            w.grab().save(str(fixture/'memory-receipt-reception.png'))
            w.provider.setCurrentIndex(1);state['step']=6
        elif stage == 6 and not w.jobs:
            p['provider_switch_keeps_timeline'] = w.conversation['id']==state['id']
            state['step']='dialog'
            answer_dialog(QMessageBox.StandardButton.No)
            p['claude_scope_requires_consent'] = not w.acknowledge_development_privacy()
            send('Dis uniquement QA fictive Claude; aucun outil ni fichier.');state['step']=7
        elif stage == 7 and not w.chat_busy:
            p['real_claude_answer'] = not w.chat_failed and bool(w.conversation['messages'][-1]['content'])
            w.navigation.setCurrentRow(2);w.copy_export()
            p['clipboard_export60'] = parse_deck_export(app.clipboard().text()).total_cards==60
            w.render_chat()
            p['chat_history_visible'] = w.transcript.isVisible() and bool(w.transcript.toPlainText().strip())
            # Capture on the next event-loop tick, after Qt paints the last turn.
            state['step']=7.5
        elif stage == 7.5:
            w.grab().save(str(fixture/'synthetic-reception.png'))
            w.close();state['step']=8
        elif stage == 8 and not w.isVisible() and not w.jobs:
            w=MainWindow(fixture);w.show();state['w']=w;state['windows'].append(w);state['step']=9
        elif stage == 9 and not w.jobs:
            p['same_history_reopened'] = w.conversation['id']==state['id'] and bool(w.conversation['messages'])
            p['memory_response_reopened_consistent'] = state['memory_message'] in w.conversation['messages'] and all(
                line in w.transcript.toPlainText() for line in state['memory_message']['content'].splitlines())
            receipt=original_research(fixture,as_of=date.today().isoformat(),topic='rules',offline=True,opener=opener)
            p['public_memory_offline_after_restart'] = receipt['gets']==0 and bool(receipt['facts']) and opener.calls==state['gets_before_restart']
            context=w.services.prepare_question('Quelles sources de règles sont déjà mémorisées?', 'aggregates')
            p['offline_memory_in_conversation_context'] = bool(context['public_memory']['facts']) and opener.calls==state['gets_before_restart']
            p['legacy_fixture_unchanged']=(fixture/'data/local/pokemind.sqlite3').read_bytes()==db_before
            finish(all(v for key,v in p.items() if key != 'frozen'))

    def tick():
        try:
            step()
            if state.get('recorded_step') != state['step']:
                (fixture/'qa-progress.json').write_text(json.dumps({'stage':state['step'],
                    'provider':state['w'].provider.currentData(),'busy':state['w'].chat_busy}),encoding='utf-8')
                state['recorded_step']=state['step']
        except Exception:
            import traceback
            (fixture/'qa-local-error.txt').write_text(traceback.format_exc(),encoding='utf-8')
            if state['w'].chat_busy: state['w'].stop_chat()
            else: finish(False,'LOCAL_QA_EXCEPTION')
    timer=QTimer();timer.timeout.connect(tick);timer.start(100)
    return app.exec()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--prepare-release',action='store_true')
    parser.add_argument('--fixture',type=Path)
    args=parser.parse_args()
    if args.prepare_release:
        root=Path.cwd().absolute()
        print(prepare_release(root).relative_to(root).as_posix())
        return 0
    if not args.fixture: parser.error('--fixture or --prepare-release required')
    fixture=synthetic_release_root(args.fixture)
    app=QApplication.instance() or QApplication([])
    w=MainWindow(fixture);w.show()
    return exercise_release(app,w)


if __name__=='__main__':
    raise SystemExit(main())
