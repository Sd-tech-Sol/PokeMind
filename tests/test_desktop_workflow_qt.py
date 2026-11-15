"""Desktop regression journeys. Every combat/person/image here is invented."""
import json
import threading
from pathlib import Path

import pytest
import shiboken6
pytest.importorskip('PySide6')
from PySide6.QtCore import Qt, QMimeData, QUrl, QTimer, QBuffer, QIODevice
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QStyleOptionViewItem

from test_desktop_qt import app, ui, wait_until, dispose_window, Fake
from test_desktop_ingestion import text
from pokemind.desktop import window, ingestion
from pokemind.assistant.sessions import Store


@pytest.fixture
def selected_history(ui, app, monkeypatch):
    from test_desktop_qt import install_selected_history, REAL_DECK_OPTIONS
    from test_opponent_auto_deck import public_index
    from pokemind import battle_batch, deck_public_stats
    report = install_selected_history(ui, app)
    monkeypatch.setattr(battle_batch, 'public_context', lambda *a: (public_index(), [], {}))
    monkeypatch.setattr(deck_public_stats, 'refresh_state', lambda *a, **k: {'automatic_due': False})
    monkeypatch.setattr(ui.services, 'deck_options', lambda: REAL_DECK_OPTIONS(ui.services))
    monkeypatch.setattr(ui, 'get_adapter', lambda: pytest.fail('recovery must not contact an AI provider'))
    monkeypatch.setattr(window.Services, 'played_reference', lambda *a: pytest.fail('recovery must not read old raw logs'))
    calls = []
    original = ui.services.save_public_opponent
    def record(value, **options):
        calls.append(value['match'])
        return original(value, **options)
    monkeypatch.setattr(ui.services, 'save_public_opponent', record)
    return report, calls


def request_selected_recovery(ui, app):
    ui.chat_input.setPlainText('Reconstruis le deck adverse de cette partie')
    QTest.mouseClick(ui.send_button, Qt.MouseButton.LeftButton)
    wait_until(app, lambda: not ui.chat_busy and not ui.jobs, timeout=15000)
    return ui.conversation['messages'][-1]['content']


def test_014_actual_battles_choice_not_latest_match_saves_once_and_refreshes_deck_lab(ui, app, selected_history):
    from test_desktop_qt import select_historical_game
    from test_opponent_auto_deck import files
    _, calls = selected_history
    select_historical_game(ui, app, 'OLD-A2')
    assert ui.conversation['selected_match'] == 'OLD-A2'
    assert 'Deck adverse ajouté' in request_selected_recovery(ui, app)
    assert calls == ['OLD-A2'] and len(files(ui.root)) == len(ui.deck_rows) == 1
    assert 'Déjà dans Deck Lab' in request_selected_recovery(ui, app)
    assert calls == ['OLD-A2', 'OLD-A2'] and len(files(ui.root)) == 1
    assert not ui.cloud_consent.isChecked() and all(m['local_only'] for m in ui.conversation['messages'])


def test_014_automatic_first_row_and_family_change_are_not_explicit_game_choices(ui, app, selected_history):
    from test_desktop_qt import select_historical_game
    _, calls = selected_history
    ui.navigation.setCurrentRow(1)
    ui.matchups.selectRow(0)  # family list populates its first game; no game activation
    app.processEvents()
    assert ui.games.currentData()
    assert 'aucune partie sélectionnée' in request_selected_recovery(ui, app)
    assert calls == []
    select_historical_game(ui, app, 'OLD-A2')
    row = next(i for i in range(ui.matchups.rowCount()) if ui.matchups.item(i, 0).text() == 'Invented Beta')
    QTest.mouseClick(ui.matchups.viewport(), Qt.MouseButton.LeftButton,
                     pos=ui.matchups.visualItemRect(ui.matchups.item(row, 0)).center())
    assert ui.games.currentData()['match'] == 'RECENT-B'
    assert ui.conversation['selected_match'] == 'OLD-A2'  # population never overwrites saved context
    assert 'aucune partie sélectionnée' in request_selected_recovery(ui, app)
    assert calls == []
    select_historical_game(ui, app, 'RECENT-B')  # explicit activation of the already displayed row
    assert 'preuves insuffisantes' in request_selected_recovery(ui, app)
    assert calls == ['RECENT-B']


def test_014_resume_conversation_revalidates_its_reference_instead_of_other_visible_game(ui, app, selected_history):
    from test_desktop_qt import select_historical_game, select_combo_item
    _, calls = selected_history
    select_historical_game(ui, app, 'OLD-A2')
    first = ui.conversation['id']
    QTest.mouseClick(ui.new_button, Qt.MouseButton.LeftButton)
    assert 'aucune partie sélectionnée' in request_selected_recovery(ui, app)
    select_historical_game(ui, app, 'RECENT-B')
    second = ui.conversation['id']
    assert first != second
    ui.refresh_history()
    select_combo_item(app, ui.history_picker, ui.history_picker.findData(first))
    assert ui.conversation['id'] == first and ui.games.currentData()['match'] == 'RECENT-B'
    assert 'Deck adverse ajouté' in request_selected_recovery(ui, app)
    assert calls == ['OLD-A2']
    # A historical discussion may refer to a match removed from the current canonical report.
    stale = ui.store.new('codex')
    stale.update(title='Invented stale history', selected_match='MISSING-MATCH')
    ui.store.save(stale)
    ui.preferences['conversations'].append({'id': stale['id'], 'title': stale['title'], 'provider': 'codex'})
    ui.refresh_history()
    select_combo_item(app, ui.history_picker, ui.history_picker.findData(stale['id']))
    assert ui.conversation['id'] == stale['id']
    assert 'aucune partie sélectionnée' in request_selected_recovery(ui, app)
    assert calls == ['OLD-A2']


def test_014_restart_recovers_saved_discussion_reference_without_auto_saving(ui, app, selected_history, monkeypatch):
    from copy import deepcopy
    from test_desktop_qt import select_historical_game
    from test_opponent_auto_deck import files
    report, _ = selected_history
    select_historical_game(ui, app, 'OLD-A2')
    identity = ui.conversation['id']
    ui.close()
    assert not ui.isVisible() and not files(ui.root)
    def load(services, *a, **k):
        services.full_report = services.report = deepcopy(report)
        return {'report': services.report, 'learning': None}
    monkeypatch.setattr(window.Services, 'load', load)
    fresh = window.MainWindow(ui.root)
    try:
        fresh.show()
        wait_until(app, lambda: fresh.metrics[0].text() == '3' and not fresh.jobs)
        assert fresh.conversation['id'] == identity and not files(ui.root)
        calls = []
        original = fresh.services.save_public_opponent
        def record(value, **options):
            calls.append(value['match'])
            return original(value, **options)
        monkeypatch.setattr(fresh.services, 'save_public_opponent', record)
        monkeypatch.setattr(fresh, 'get_adapter', lambda: pytest.fail('restart recovery must remain local'))
        assert 'Deck adverse ajouté' in request_selected_recovery(fresh, app)
        assert calls == ['OLD-A2'] and len(files(ui.root)) == 1
    finally:
        dispose_window(fresh, app)


def test_014_new_local_import_without_cloud_is_selected_before_any_llm_followup(ui, app, selected_history, monkeypatch):
    from test_desktop_qt import select_historical_game
    from pokemind import battle_batch
    # No catalog/counter-deck database accompanies this tiny parser fixture; use the real offline refusal.
    monkeypatch.setattr(battle_batch, 'public_context', lambda *a: (None, [], {'status': 'BLOCKED_PUBLIC_REFERENCE'}))
    _, calls = selected_history
    select_historical_game(ui, app, 'OLD-A2')
    ui.chat_input.setPlainText(text())
    QTest.mouseClick(ui.send_button, Qt.MouseButton.LeftButton)
    wait_until(app, lambda: not ui.ingest_busy and not ui.jobs, timeout=15000)
    reference = ui.last_import['match']['match']
    assert reference != 'OLD-A2' and ui.conversation['selected_match'] == reference
    assert not ui.cloud_consent.isChecked() and not ui.chat_busy
    assert 'preuves insuffisantes' in request_selected_recovery(ui, app)
    assert calls == [reference]
    QTest.mouseClick(ui.view_import_button, Qt.MouseButton.LeftButton)
    assert ui.games.currentData()['match'] == ui.conversation['selected_match'] == reference


@pytest.mark.parametrize('cancelled', [False, True])
def test_014_late_worker_keeps_original_game_snapshot_when_family_changes(ui, app, selected_history, monkeypatch, cancelled):
    from test_desktop_qt import select_historical_game
    from test_opponent_auto_deck import files
    _, calls = selected_history
    select_historical_game(ui, app, 'OLD-A2')
    started, release = threading.Event(), threading.Event()
    original = ui.services.save_public_opponent
    def slow(value, **options):
        started.set()
        assert release.wait(10)
        return original(value, **options)
    monkeypatch.setattr(ui.services, 'save_public_opponent', slow)
    ui.chat_input.setPlainText('Reconstruis le deck adverse de cette partie')
    QTest.mouseClick(ui.send_button, Qt.MouseButton.LeftButton)
    wait_until(app, started.is_set)
    assert not ui.new_button.isEnabled() and not ui.history_picker.isEnabled()
    select_historical_game(ui, app, 'RECENT-B')
    if cancelled:
        QTest.mouseClick(ui.stop_button, Qt.MouseButton.LeftButton)
    release.set()
    wait_until(app, lambda: not ui.chat_busy and not ui.jobs)
    assert calls == ['OLD-A2'] and len(files(ui.root)) == (0 if cancelled else 1)
    assert ui.conversation['selected_match'] == 'RECENT-B'
    assert ('annulé' if cancelled else 'Deck adverse ajouté') in ui.conversation['messages'][-1]['content']


def choose(window_under_test, mode):
    """The message mode is picked under the chat, never inferred from the words (audit A-8)."""
    index = window_under_test.chat_mode.findData(mode)
    assert index >= 0
    window_under_test.chat_mode.setCurrentIndex(index)


def test_unified_log_question_automatically_chains_without_raw_provider_context(ui, app, monkeypatch):
    captured = []
    class Capture(Fake):
        def ask_stream(self, prompt, history, emit, tool=None):
            captured.append((prompt, history))
            super().ask_stream(prompt, history, emit, tool)
    monkeypatch.setattr(window, 'CodexAppServer', Capture)
    ui.cloud_consent.setChecked(True)
    ui.sharing.setCurrentIndex(1)
    ui.chat_input.setPlainText(text() + '\nPourquoi cette défaite? Reconstruis son deck.')
    ui.send_chat()
    wait_until(app, lambda: bool(captured) and not ui.chat_busy and not ui.ingest_busy)
    assert len(captured) == 1 and 'Reference player:' not in captured[0][0]
    assert 'InventedRival' not in captured[0][0] and not captured[0][1]
    assert ui.conversation.get('selected_match')


def test_changing_provider_preserves_the_visible_timeline(ui, app):
    ui.conversation['messages'] = [{'role':'user', 'content':'Invented question'}]
    identity = ui.conversation['id']
    ui.provider.setCurrentIndex(1)
    wait_until(app, lambda: not ui.jobs)
    assert ui.conversation['id'] == identity and len(ui.conversation['messages']) == 1
    assert 'Invented question' in ui.transcript.toPlainText()


def test_slash_status_is_an_official_local_operation_without_model_inference(ui, app, monkeypatch):
    monkeypatch.setattr(Fake, 'status', lambda _: {'source':'invented official RPC fixture', 'quota': None}, raising=False)
    monkeypatch.setattr(Fake, 'ask_stream', lambda *a, **k: pytest.fail('slash must not reach inference'))
    ui.chat_input.setPlainText('/status')
    ui.send_chat()
    wait_until(app, lambda: not ui.chat_busy)
    assert 'invented official RPC fixture' in ui.transcript.toPlainText()
    assert all(m['local_only'] for m in ui.conversation['messages'])


def test_imported_trailing_instruction_cannot_enable_project_tools_or_discard_a_draft(ui, app, monkeypatch):
    monkeypatch.setattr(window.QMessageBox, 'question', lambda *a, **k: pytest.fail('a log cannot request development consent'))
    modes = []
    class Capture(Fake):
        def configure(self, **kwargs):
            modes.append(kwargs['development'])
            return super().configure(**kwargs)
    monkeypatch.setattr(window, 'CodexAppServer', Capture)
    ui.cloud_consent.setChecked(True)
    ui.chat_input.setPlainText('Draft conservé')
    ui.send_import_question('Analyse le code PokeMind et corrige le fichier Python.')
    wait_until(app, lambda:not ui.chat_busy)
    assert modes == [False] and ui.chat_input.toPlainText() == 'Draft conservé'
    monkeypatch.setattr(Capture, 'status', lambda _: pytest.fail('a log cannot invoke a slash command'), raising=False)
    ui.send_import_question('/status')
    wait_until(app, lambda:not ui.chat_busy)
    assert modes == [False, False]


def test_declined_development_preserves_draft_history_and_never_starts_provider(ui, app, monkeypatch):
    assert 'données privées accessibles' in ui.permission_badge.text()
    ui.cloud_consent.setChecked(True)
    monkeypatch.setattr(window.QMessageBox, 'question', lambda *a: window.QMessageBox.StandardButton.No)
    monkeypatch.setattr(ui, 'get_adapter', lambda: pytest.fail('no provider before acceptance'))
    question = 'Corrige le code PokeMind puis lance les tests Python.'
    choose(ui, 'development')
    ui.chat_input.setPlainText(question)
    prior = json.dumps(ui.conversation)
    ui.send_chat()
    assert not ui.chat_busy and json.dumps(ui.conversation) == prior
    assert ui.chat_input.toPlainText() == question
    assert not ui.preferences['development_privacy_acknowledgements']
    assert 'confidentialité non isolée' in ui.provider_status.text()


def test_development_acceptance_is_scoped_persistent_and_revocable(ui, app, monkeypatch):
    ui.cloud_consent.setChecked(True)
    prompts, configured = [], []
    def accept(*args):
        prompts.append(args[2])
        return window.QMessageBox.StandardButton.Yes
    class Capture(Fake):
        def configure(self, **kwargs):
            configured.append(kwargs)
            return super().configure(**kwargs)
    monkeypatch.setattr(window.QMessageBox, 'question', accept)
    monkeypatch.setattr(window, 'CodexAppServer', Capture)
    monkeypatch.setattr(ui.services, 'load', lambda *a, **k: pytest.fail('development must not load the personal coach report'))
    choose(ui, 'development')
    ui.chat_input.setPlainText('Corrige le code PokeMind puis lance les tests Python.')
    identity = ui.conversation['id']
    ui.send_chat()
    wait_until(app, lambda:not ui.chat_busy)
    assert configured[0]['development'] and configured[0]['privacy_acknowledged'] is True
    assert ui.conversation['id'] == identity and len(prompts) == 1
    assert 'historique cloud' in prompts[0] and 'data/local' in prompts[0]
    assert Store(ui.root).preferences()['development_privacy_acknowledgements']
    assert ui.acknowledge_development_privacy() and len(prompts) == 1
    ui.preferences['permission_mode'] = 'full'
    assert ui.acknowledge_development_privacy() and len(prompts) == 2
    ui.preferences['permission_mode'] = 'workspace'
    child = ui.root / 'invented-code'
    child.mkdir()
    ui.preferences['project_relative'] = 'invented-code'
    assert ui.acknowledge_development_privacy() and len(prompts) == 3
    ui.provider.setCurrentIndex(1)
    wait_until(app, lambda:not ui.jobs)
    assert ui.acknowledge_development_privacy() and len(prompts) == 4
    ui.revoke_development_privacy()
    assert Store(ui.root).preferences()['development_privacy_acknowledgements'] == []
    assert ui.acknowledge_development_privacy() and len(prompts) == 5


def test_consent_storage_failure_cannot_start_development(ui, app, monkeypatch):
    ui.cloud_consent.setChecked(True)
    monkeypatch.setattr(window.QMessageBox, 'question', lambda *a: window.QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(ui.store, 'write', lambda *a: (_ for _ in ()).throw(OSError('invented failure')))
    monkeypatch.setattr(ui, 'get_adapter', lambda: pytest.fail('no provider after consent storage failure'))
    choose(ui, 'development')
    ui.chat_input.setPlainText('Corrige le code PokeMind avec Codex.')
    ui.send_chat()
    assert not ui.chat_busy and not ui.preferences['development_privacy_acknowledgements']
    assert 'Consentement non enregistré' in ui.provider_status.text()
    assert ui.chat_input.toPlainText() and not ui.conversation['messages']


def test_successful_persistence_receipt_is_visible_as_soon_as_the_answer_finishes(ui, app):
    ui.conversation['messages'] = [{'role':'assistant','content':'Réponse inventée.'}]
    ui.services.last_research_receipt = {'persisted':True, 'added':2, 'updated':1,
        'already_known':3, 'unverified':1, 'status':'PARTIAL'}
    ui.chat_done(None)
    assert '2 faits ajoutés' in ui.transcript.toPlainText() and 'État : PARTIAL' in ui.transcript.toPlainText()
    assert ui.services.last_research_receipt is None


@pytest.mark.parametrize('provider', ['codex', 'claude'])
@pytest.mark.parametrize('topic,question,expected', [
    ('rules', 'Cherche les règles puis explique leurs implications.', 'Texte des règles non extrait'),
    ('meta', 'Quelles tendances méta récentes et pourquoi?', 'Famille Boréale')])
def test_research_answers_subject_with_citations_and_limits_not_only_write_counts(
        ui, app, monkeypatch, provider, topic, question, expected):
    from pokemind import batch_public_research as research
    prompts = []
    class FalseClaims(Fake):
        def ask_stream(self, prompt, history, emit, tool=None):
            prompts.append(prompt)
            emit("Rien n'a été enregistré et cette carte est 100% légale.")
    url = ('https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources'
           if topic == 'rules' else 'https://www.limitlesstcg.com/decks')
    fact = {'kind':'official_document' if topic == 'rules' else 'public_archetype_directory',
        'source_url':url,'retrieved_at':'2026-10-27T12:00:00+00:00','version':'a'*64,
        'validation':'unverified','entries':[{'archetype':'Famille Boréale','path':'/decks/1'}]}
    receipt = {'status':'SAVED','persisted':True,'added':1,'updated':0,'already_known':0,
        'unverified':1,'facts':[fact],'sources':[url]}
    calls = []
    monkeypatch.setattr(research, 'research', lambda *a, **k: calls.append(k) or receipt)
    monkeypatch.setattr(research, 'research_matchups', lambda *a, **k: {'gets':0})
    monkeypatch.setattr(research, 'matchup_database', lambda *a: None)
    monkeypatch.setattr(window, 'CodexAppServer', FalseClaims)
    monkeypatch.setattr(window, 'ClaudeCode', FalseClaims)
    ui.provider.setCurrentIndex(ui.provider.findData(provider))
    wait_until(app, lambda:not ui.jobs)
    ui.cloud_consent.setChecked(True)
    choose(ui, 'research')
    ui.chat_input.setPlainText(question)
    identity = ui.conversation['id']
    ui.send_chat();wait_until(app, lambda:not ui.chat_busy)
    saved = ui.store.load(identity)['messages'][-1]
    # The collected facts reach the model, which answers the subject itself (owner, 2026-11-03); the host
    # receipt under its answer keeps the real write counts.
    assert url in prompts[0] and 'MODE RECHERCHE WEB' in prompts[0] and (topic == 'rules' or expected in prompts[0])
    for content in (saved['content'], ui.transcript.toPlainText()):
        assert content.index("Rien n'a été enregistré") < content.index('Reçu PokeMind')
        assert '1 faits ajoutés' in content
    assert len(calls) == 1 and ui.stack.count() == 7 and ui.conversation['id'] == identity
    assert len(ui.conversation['messages']) == 2


@pytest.mark.parametrize('provider', ['codex', 'claude'])
@pytest.mark.parametrize('topic', ['rules','meta'])
def test_deeper_public_fields_render_save_and_reopen_without_provider_certainty(ui,app,monkeypatch,provider,topic):
    from pokemind import batch_public_research as research, meta
    from pokemind.assistant.receipts import public_research_message
    from test_public_source_depth import collect, DAY, meta_fixture
    if topic=='rules':
        collect(ui.root)
        receipt=research.research(ui.root,as_of=DAY,topic='rules',offline=True)
        expected=('Q, R','2031-04-01','2031-05-01','réimpression : unknown')
    else:
        db=meta_fixture(ui.root)
        evidence=meta.meta_window_comparison(db,since='2031-05-01',split='2031-05-15',until='2031-05-31',as_of=DAY)
        receipt={'as_of':DAY,'facts':[],'meta_evidence':evidence,'status':'CACHE_FRESH',
            'persisted':True,'added':0,'updated':0,'already_known':0,'unverified':0,'sources':[]}
        expected=('Variation descriptive','2031-05-01','20/20 placements','causalité : unknown')
    class FalseClaims(Fake):
        def ask_stream(self,prompt,history,emit,tool=None):
            emit("Rien n'a été mémorisé; 100% légale, amélioration garantie.")
    calls=[]
    monkeypatch.setattr(research,'research',lambda *a,**k:calls.append(k) or receipt)
    monkeypatch.setattr(research,'research_matchups',lambda *a,**k:{'gets':0})
    monkeypatch.setattr(research,'matchup_database',lambda *a:None)
    monkeypatch.setattr(window,'CodexAppServer',FalseClaims)
    monkeypatch.setattr(window,'ClaudeCode',FalseClaims)
    ui.provider.setCurrentIndex(ui.provider.findData(provider))
    wait_until(app,lambda:not ui.jobs)
    ui.cloud_consent.setChecked(True)
    question='Cherche les règles et leurs implications' if topic=='rules' else 'Cherche les tendances méta et pourquoi'
    choose(ui,'research')
    ui.chat_input.setPlainText(question);ui.send_chat();wait_until(app,lambda:not ui.chat_busy)
    identity=ui.conversation['id']
    saved=ui.store.load(identity)['messages'][-1]
    # The model answers (owner, 2026-11-03); the host receipt under it keeps the write counts.
    assert saved['content'].startswith("Rien n'a été mémorisé; 100% légale")
    assert 'Reçu PokeMind · collecte publique bornée — État : ' + receipt['status'] in saved['content']
    assert 'Validation sur la source : non attestée.' in saved['content']
    assert saved['memory_receipt']['status']==receipt['status']
    assert saved['content']!=public_research_message(receipt,question)
    assert 'Reçu PokeMind' in ui.transcript.toPlainText()
    assert len(calls)==1 and ui.stack.count()==7
    expected=('Reçu PokeMind',)
    from pokemind.desktop.window import MainWindow
    from test_desktop_qt import dispose_window
    reopened=MainWindow(ui.root)
    try:
        wait_until(app,lambda:not reopened.jobs)
        assert reopened.conversation['id']==identity and saved in reopened.conversation['messages']
        assert all(part in reopened.transcript.toPlainText() for part in expected)
    finally:
        dispose_window(reopened,app)


@pytest.mark.parametrize('provider', ['codex', 'claude'])
def test_model_denial_cannot_contradict_the_saved_and_rendered_receipt(ui, app, monkeypatch, provider):
    from pokemind import batch_public_research
    class Denial(Fake):
        def ask_stream(self, prompt, history, emit, tool=None):
            emit("Rien n'a été mémorisé.")
    receipt = {'persisted':True, 'added':2, 'updated':0, 'already_known':0,
        'unverified':2, 'status':'SAVED', 'gets':3, 'facts':[],
        'sources':['https://www.pokemon.com/invented-qa']}
    calls = []
    def research(*args, **kwargs):
        calls.append(kwargs)
        return receipt
    monkeypatch.setattr(batch_public_research, 'research', research)
    monkeypatch.setattr(window, 'CodexAppServer', Denial)
    monkeypatch.setattr(window, 'ClaudeCode', Denial)
    ui.provider.setCurrentIndex(ui.provider.findData(provider))
    wait_until(app, lambda:not ui.jobs)
    ui.cloud_consent.setChecked(True)
    choose(ui, 'research')
    ui.chat_input.setPlainText('Recherche les règles et mémorise les sources.')
    ui.send_chat()
    wait_until(app, lambda:not ui.chat_busy)
    saved = ui.store.load(ui.conversation['id'])['messages'][-1]['content']
    for text in (ui.transcript.toPlainText(), saved):
        # The model's sentence is shown as its own; the host receipt states the real counts after it.
        assert text.index("Rien n'a été mémorisé") < text.index('Reçu PokeMind')
        assert '2 faits ajoutés' in text and '2 non vérifiés' in text
    assert len(calls) == 1


@pytest.mark.parametrize('status,persisted,added,known,facts', [
    ('SAVED',True,2,0,2), ('SAVED',True,0,2,2),
    ('PARTIAL',True,2,0,2), ('PARTIAL',True,0,0,0),
    ('CACHE_FRESH',True,0,2,2), ('OFFLINE_STALE_OR_EMPTY',True,0,2,2),
    ('OFFLINE_STALE_OR_EMPTY',True,0,0,0), ('SOURCE_COOLDOWN',True,0,2,2),
    ('SAVED',False,2,0,0), ('ERROR',None,0,0,0), ('INTERRUPTED',None,0,0,0),
    ('CACHE_FRESH',True,2,0,2), ('SAVED',True,True,0,2)])
def test_all_receipt_outcomes_control_rendered_and_saved_response(ui, app, status, persisted, added, known, facts):
    receipt = {'status':status, 'persisted':persisted, 'added':added, 'updated':0,
        'already_known':known, 'unverified':facts, 'facts':[{'validation':'unverified'}]*facts,
        'sources':['https://www.pokemon.com/invented-receipt']}
    ui.conversation['messages'] = [{'role':'assistant','content':''}]
    ui.services.last_research_receipt = receipt
    ui.chat_delta("Réponse inventée du modèle.")
    ui.render_chat()
    assert 'Réponse inventée du modèle.' in ui.transcript.toPlainText()  # streamed like any answer
    ui.chat_done(None)
    saved = ui.store.load(ui.conversation['id'])['messages'][-1]
    assert saved == ui.conversation['messages'][-1]
    confirmed = (persisted is True and type(added) is int
                 and status in {'SAVED','PARTIAL','CACHE_FRESH','OFFLINE_STALE_OR_EMPTY','SOURCE_COOLDOWN'})
    for text in (saved['content'], ui.transcript.toPlainText()):
        assert text.startswith('Réponse inventée du modèle.') or 'Réponse inventée du modèle.' in text
        assert 'État : ' + status in text and 'Validation sur la source : non attestée' in text
        assert ('faits ajoutés' in text) == confirmed
        assert ('enregistrement local non confirmé' in text) != confirmed
    assert saved['memory_receipt']['offline_fact_count'] == facts
    assert ui.services.last_research_receipt is None


def test_research_without_model_answer_keeps_the_full_host_receipt(ui, app):
    receipt = {'status':'SAVED', 'persisted':True, 'added':1, 'updated':0, 'already_known':0, 'unverified':1,
        'facts':[{'validation':'unverified'}], 'sources':['https://www.pokemon.com/invented-receipt']}
    ui.conversation['messages'] = [{'role':'user','content':'Cherche les règles.'}, {'role':'assistant','content':''}]
    ui.services.last_research_receipt = receipt
    ui.chat_failed = True
    ui.chat_done(None)
    text = ui.conversation['messages'][-1]['content']
    assert 'Résultat PokeMind — mémoire publique' in text and 'le reçu local est conservé' in text
    ui.chat_failed = False


@pytest.mark.parametrize('code', ['INVENTED_PROVIDER_ERROR', 'DESKTOP_CANCELLED'])
def test_provider_failure_or_interruption_preserves_completed_write_receipt(ui, app, monkeypatch, code):
    from pokemind import batch_public_research
    from pokemind.assistant.provider import ProviderError
    class Failure(Fake):
        def ask_stream(self, prompt, history, emit, tool=None):
            emit("Rien n'a été mémorisé.")
            raise ProviderError(code)
    monkeypatch.setattr(window, 'CodexAppServer', Failure)
    monkeypatch.setattr(batch_public_research, 'research', lambda *a, **k:{
        'status':'PARTIAL', 'persisted':True, 'added':2, 'updated':0,
        'already_known':0, 'unverified':2, 'facts':[]})
    ui.cloud_consent.setChecked(True)
    choose(ui, 'research')
    ui.chat_input.setPlainText('Recherche les règles et mémorise les sources.')
    ui.send_chat();wait_until(app, lambda:not ui.chat_busy)
    message = ui.store.load(ui.conversation['id'])['messages'][-1]
    assert message['memory_receipt']['added'] == 2
    assert '2 faits ajoutés' in message['content']
    # A failed engine leaves only the host receipt; an interrupted one keeps its partial answer above it.
    assert ("Rien n'a été mémorisé" in message['content']) == (not ui.chat_failed)
    assert '2 faits ajoutés' in ui.transcript.toPlainText()
    assert ('indisponible' if ui.chat_failed else 'interrompu') in message['content']


def test_collection_failure_cannot_claim_success_and_next_normal_response_is_unchanged(ui, app, monkeypatch):
    from pokemind import batch_public_research
    calls = []
    def fail(*args, **kwargs):
        calls.append(1)
        raise OSError('invented storage failure')
    monkeypatch.setattr(batch_public_research, 'research', fail)
    ui.cloud_consent.setChecked(True)
    choose(ui, 'research')
    ui.chat_input.setPlainText('Recherche les règles et mémorise les sources.')
    ui.send_chat();wait_until(app, lambda:not ui.chat_busy)
    saved = ui.store.load(ui.conversation['id'])['messages'][-1]
    assert 'Enregistrement local non confirmé' in saved['content']
    assert 'faits ajoutés' not in saved['content'] and 'faits ajoutés' not in ui.transcript.toPlainText()
    ui.provider.setCurrentIndex(1);wait_until(app, lambda:not ui.jobs)
    ui.chat_input.setPlainText('Question inventée ordinaire')
    ui.send_chat();wait_until(app, lambda:not ui.chat_busy)
    normal = ui.store.load(ui.conversation['id'])['messages'][-1]
    assert normal['content'] == 'Réponse inventée → avec source PokeMind.'
    assert 'memory_receipt' not in normal and len(calls) == 1


def test_receipt_history_reopens_in_the_same_thread_after_window_close(ui, app):
    ui.conversation['messages'] = [{'role':'assistant','content':"Rien n'a été mémorisé."}]
    ui.services.last_research_receipt = {'status':'SAVED','persisted':True,'added':2,
        'updated':0,'already_known':0,'unverified':2,'facts':[], 'sources':[]}
    ui.chat_done(None)
    identity, expected = ui.conversation['id'], ui.conversation['messages'][-1]
    ui.close()
    reopened = window.MainWindow(ui.root)
    reopened.show()
    try:
        wait_until(app, lambda:not reopened.jobs)
        assert reopened.conversation['id'] == identity
        assert reopened.conversation['messages'][-1] == expected
        painted = reopened.transcript.toPlainText()
        assert '2 faits ajoutés' in painted and painted.index("Rien n'a été mémorisé") < painted.index('Reçu PokeMind')
        reopened.provider.setCurrentIndex(1);wait_until(app, lambda:not reopened.jobs)
        assert reopened.conversation['id'] == identity and reopened.conversation['messages'][-1] == expected
    finally:
        dispose_window(reopened, app)


def test_replacing_a_long_answer_keeps_the_receipt_inside_the_painted_viewport(ui, app):
    ui.conversation['messages'] = [{'role':'assistant','content':'Ligne inventée.\n'*160}]
    ui.render_chat()
    app.processEvents()
    ui.conversation['messages'][-1]['content'] = 'Résultat PokeMind\n2 faits ajoutés · 2 non vérifiés.'
    ui.render_chat()
    painted = ui.transcript.viewport().grab().toImage()
    # A saved string alone did not expose the blank viewport found in frozen QA.
    # Glyphs must actually be painted in the text colour. Counting antialiasing
    # shades fails on Qt's offscreen platform (CI), which paints unsmoothed text.
    from PySide6.QtGui import QColor
    from pokemind.desktop.theme import colors
    text_colour = QColor(colors(ui.preferences['theme'])['text'])
    def near_text(pixel):
        value = QColor.fromRgb(pixel)
        return sum(abs(a - b) for a, b in zip(value.getRgb()[:3], text_colour.getRgb()[:3])) < 60
    glyphs = sum(near_text(painted.pixel(x, y)) for x in range(painted.width()) for y in range(painted.height()))
    assert glyphs > 300


def test_enter_sends_and_shift_enter_only_adds_a_line(ui,app):
    ui.cloud_consent.setChecked(True)
    mime=QMimeData();mime.setUrls([QUrl('https://example.invalid/card')])
    mime.setText('Question inventée https://example.invalid/card')
    ui.chat_input.insertFromMimeData(mime)
    assert 'https://example.invalid/card' in ui.chat_input.toPlainText() and not ui.ingest_busy
    QTest.keyClick(ui.chat_input,Qt.Key.Key_Return,Qt.KeyboardModifier.ShiftModifier)
    assert '\n' in ui.chat_input.toPlainText() and not ui.conversation['messages']
    QTest.keyClick(ui.chat_input,Qt.Key.Key_Return)
    wait_until(app,lambda:not ui.chat_busy)
    assert len(ui.conversation['messages'])==2 and 'Réponse inventée' in ui.transcript.toPlainText()
    assert not ui.activity.timer.isActive() and 'Terminé' in ui.activity.label.text()


def test_paste_is_local_then_normal_question_never_resends_import_history(ui,app,monkeypatch):
    captured=[]
    class Capture(Fake):
        def ask_stream(self,prompt,history,emit,tool=None):
            captured.append((prompt,history))
            super().ask_stream(prompt,history,emit,tool)
    monkeypatch.setattr(window,'CodexAppServer',Capture)
    ui.chat_input.setPlainText(text())
    QTest.keyClick(ui.chat_input,Qt.Key.Key_Return)
    wait_until(app,lambda:not ui.ingest_busy)
    assert captured==[] and ui.metrics[0].text()=='1'
    # Corpus totals sit in the status bar; the chat says how to let the coach find the opponent's deck.
    assert 'Partie enregistrée' in ui.transcript.toPlainText() and 'Statistiques actualisées' not in ui.transcript.toPlainText()
    assert 'Statistiques actualisées' in ui.statusBar().currentMessage() and 'coche l’envoi cloud' in ui.transcript.toPlainText()
    assert ui.view_import_button.isVisible()
    QTest.mouseClick(ui.view_import_button,Qt.MouseButton.LeftButton)
    assert ui.stack.currentIndex()==1 and ui.games.currentData()['match']==ui.last_import['match']['match']
    assert all(m['local_only'] for m in ui.conversation['messages'])
    assert 'Reference player:' not in json.dumps(ui.store.load(ui.conversation['id']))
    ui.cloud_consent.setChecked(True)
    ui.chat_input.setPlainText('Question inventée normale')
    ui.send_chat();wait_until(app,lambda:not ui.chat_busy)
    assert len(captured)==1 and not captured[0][1]
    assert 'InventedRival' not in captured[0][0] and 'Reference player:' not in captured[0][0]


def test_pasted_defeat_alone_is_followed_and_never_saves_the_opponent_deck(ui,app,monkeypatch):
    # PM-COACH-LOSS-PRIORITY-001: a lost game opens the loss follow-up; the opponent's deck is not saved by itself.
    captured=[]
    export='Pokémon: 20\n20 Invented Alpha INV 1\nTrainer: 20\n20 Invented Beta INV 2\nEnergy: 20\n20 Basic Invented Energy INV 3'
    class Capture(Fake):
        def ask_stream(self,prompt,history,emit,tool=None):
            captured.append(prompt)
            captured.append(tool({'operation':'save_deck','query':'Deck adverse inventé','export_text':export}))
            super().ask_stream(prompt,history,emit,tool)
    monkeypatch.setattr(window,'CodexAppServer',Capture)
    ui.cloud_consent.setChecked(True);ui.sharing.setCurrentIndex(1)
    ui.chat_input.setPlainText(text())
    QTest.keyClick(ui.chat_input,Qt.Key.Key_Return)
    wait_until(app,lambda:len(captured)==2 and not ui.chat_busy and not ui.ingest_busy)
    assert captured[0].startswith('Question : '+window.LOG_QUESTIONS['loss'])
    assert '"log_followup"' in captured[0] and '"loss_watch"' in captured[0] and '"opponent_reconstruction"' in captured[0]
    assert 'InventedRival' not in captured[0] and 'Reference player:' not in captured[0]
    assert captured[1]['error']=='DECK_SAVE_REQUIRES_OWNER_REQUEST' and ui.services.my_decks()==[]
    assert 'Défaite ajoutée au suivi des matchups difficiles' in ui.transcript.toPlainText()
    assert 'Deck ajouté à Mes decks' not in ui.statusBar().currentMessage()
    assert 'Statistiques actualisées' not in ui.transcript.toPlainText()


def test_pasted_win_counts_and_the_coach_gets_a_short_review_without_deck(ui,app,monkeypatch):
    captured=[]
    class Capture(Fake):
        def ask_stream(self,prompt,history,emit,tool=None):
            captured.append(prompt)
            captured.append(tool({'operation':'save_deck','query':'Gagné inventé','export_text':'x'}))
            super().ask_stream(prompt,history,emit,tool)
    monkeypatch.setattr(window,'CodexAppServer',Capture)
    ui.cloud_consent.setChecked(True);ui.sharing.setCurrentIndex(1)
    ui.chat_input.setPlainText(text('InventedSelf'))
    QTest.keyClick(ui.chat_input,Qt.Key.Key_Return)
    wait_until(app,lambda:len(captured)==2 and not ui.chat_busy and not ui.ingest_busy)
    assert captured[0].startswith('Question : '+window.LOG_QUESTIONS['win'])
    assert '"opponent_reconstruction"' not in captured[0] and '"outcome": "win"' in captured[0]
    assert captured[1]['error']=='DECK_SAVE_REQUIRES_OWNER_REQUEST' and ui.services.my_decks()==[]
    assert 'Victoire comptée dans tes statistiques.' in ui.transcript.toPlainText()
    assert 'Non créé' in ui.transcript.toPlainText()
    from pokemind.desktop.services import SAVE_REQUEST
    assert not any(SAVE_REQUEST.search(q) for q in window.LOG_QUESTIONS.values())


def test_owner_text_around_a_pasted_log_is_kept_as_the_question(ui,app,monkeypatch):
    captured=[]
    class Capture(Fake):
        def ask_stream(self,prompt,history,emit,tool=None):
            captured.append(prompt);super().ask_stream(prompt,history,emit,tool)
    monkeypatch.setattr(window,'CodexAppServer',Capture)
    ui.cloud_consent.setChecked(True);ui.sharing.setCurrentIndex(1)
    ui.chat_input.setPlainText('c’est quel deck qui m’a battu? ajoute-le à mes decks\n\n'+text())
    ui.send_chat();wait_until(app,lambda:bool(captured) and not ui.chat_busy and not ui.ingest_busy)
    assert captured[0].startswith('Question : c’est quel deck qui m’a battu? ajoute-le à mes decks')
    assert ui.services.candidate_allowed


def test_save_deck_refuses_a_list_that_breaks_a_deck_rule(local_tmp, monkeypatch):
    services=window.Services(local_tmp)
    export='Pokémon: 20\n20 Invented Alpha INV 1\nTrainer: 20\n20 Invented Beta INV 2\nEnergy: 20\n20 Basic Invented Energy INV 3'
    monkeypatch.setattr(services,'validate_deck',lambda text:{'total_cards':60,
        'legality':{'live':{'structure_problems':['DECK_ACE_SPEC_LIMIT_EXCEEDED']},'in_person':{'structure_problems':[]}}})
    refused=services.tool_call({'operation':'save_deck','query':'Deux AS','export_text':export})
    assert refused['error']=='DECK_RULES_VIOLATED' and refused['structure_problems']==['DECK_ACE_SPEC_LIMIT_EXCEEDED']
    assert services.my_decks()==[] and services.saved_deck is None


def test_save_deck_needs_a_name_and_exactly_60_and_never_overwrites(local_tmp):
    services=window.Services(local_tmp)
    export='Pokémon: 20\n20 Invented Alpha INV 1\nTrainer: 20\n20 Invented Beta INV 2\nEnergy: 20\n20 Basic Invented Energy INV 3'
    # No keyword gate: a misspelt request (« creck-le dans mes deck ») still saves, create-only.
    services.candidate_allowed=False
    assert services.tool_call({'operation':'save_deck','query':'  ','export_text':export})['error']=='DECK_NAME_REQUIRED'
    assert services.tool_call({'operation':'save_deck','query':'Court','export_text':export.replace('20 Basic','19 Basic')})['error']=='DECK_REQUIRES_EXACT_60'
    assert services.tool_call({'operation':'save_deck','query':'Premier nom','export_text':export})['status']=='SAVED_DECK'
    again=services.tool_call({'operation':'save_deck','query':'Autre nom','export_text':export})
    assert again=={'status':'ALREADY_SAVED','name':'Premier nom','total_cards':60}
    assert [d['name'] for d in services.my_decks()]==['Premier nom']
    assert services.deck_options()[0]['label']=='Premier nom' and 'personnelle' in services.deck_options()[0]['kind']
    from pokemind.desktop.locale_text import set_current_language
    set_current_language('en')
    try:
        # Public-only sharing never lists a personal deck, whatever the display language.
        assert 'Premier nom' not in [d['label'] for d in services.tool_call({'operation':'decks'},'public')['decks']]
    finally:
        set_current_language('fr')


def test_paste_duplicate_does_not_increment_counts(ui,app):
    for _ in range(2):
        ui.chat_input.setPlainText(text())
        ui.send_chat();wait_until(app,lambda:not ui.ingest_busy)
    assert ui.metrics[0].text()=='1' and 'Doublon détecté' in ui.transcript.toPlainText()
    assert 'Nouvelles parties uniques dans le corpus : 0' in ui.statusBar().currentMessage()


def test_incomplete_and_ambiguous_pastes_are_refused_without_provider(ui,app):
    for value in [text().replace('InventedRival wins.',''),
                  'InventedSelf played Something.\nInventedRival drew a card.']:
        ui.chat_input.setPlainText(value)
        ui.send_chat();wait_until(app,lambda:not ui.ingest_busy)
        assert 'Importation refusée' in ui.conversation['messages'][-1]['content']
    assert 'Collage ambigu' in ui.conversation['messages'][-1]['content']
    assert ui.adapter is None and ui.metrics[0].text()=='6'


def test_large_paste_bypasses_ordinary_cloud_message_limit(ui,app):
    value=text().replace('InventedRival wins.','Note inventée.\n'*2000+'InventedRival wins.')
    ui.chat_input.setPlainText(value)
    ui.send_chat();wait_until(app,lambda:not ui.ingest_busy)
    assert ui.metrics[0].text()=='1' and 'Partie enregistrée' in ui.transcript.toPlainText()
    assert ui.adapter is None and 'Note inventée' not in ui.transcript.toPlainText()


def test_file_mime_attachment_is_parsed_locally_and_source_is_preserved(ui,app,local_tmp):
    path=local_tmp/'invented-attached.log';path.write_text(text())
    mime=QMimeData();mime.setUrls([QUrl.fromLocalFile(str(path))])
    ui.chat_input.insertFromMimeData(mime)
    wait_until(app,lambda:not ui.ingest_busy)
    assert ui.metrics[0].text()=='1' and path.read_text()==text() and ui.adapter is None


def test_personal_question_with_public_preference_returns_actual_local_answer(ui,app):
    ui.chat_input.setPlainText('Combien de défaites dans mes combats?')
    ui.send_chat();wait_until(app,lambda:not ui.chat_busy)
    assert ui.adapter is None and '6 parties uniques' in ui.transcript.toPlainText()
    assert '4 défaites' in ui.transcript.toPlainText() and 'taux de victoire global inconnu' in ui.transcript.toPlainText()
    assert not ui.cloud_consent.isChecked() and ui.sharing.currentData()=='public'


def test_deck_request_with_a_pronoun_reaches_the_coach_and_keeps_stats_local(ui,app,monkeypatch):
    # « fais-moi » used to look personal: the owner got a stats dump instead of a deck.
    calls,stages=[],[]
    class Capture(Fake):
        def ask_stream(self,prompt,history,emit,tool=None):
            calls.append(prompt)
            self.on_event({'method':'item/completed','params':{'item':{'type':'dynamicToolCall','tool':'pokemind_tool','status':'completed'}}})
            tool({'query':'Pikachu'})
            super().ask_stream(prompt,history,emit,tool)
    monkeypatch.setattr(window,'CodexAppServer',Capture)
    monkeypatch.setattr(ui.activity,'set_stage',lambda text:stages.append(str(text)))
    ui.cloud_consent.setChecked(True)
    assert ui.sharing.currentData()=='public'
    ui.chat_input.setPlainText('Fais-moi le meilleur deck avec Pikachu, je suis en français')
    ui.send_chat();wait_until(app,lambda:not ui.chat_busy)
    assert len(calls)==1 and not ui.chat_local_only and '6 parties uniques' not in ui.transcript.toPlainText()
    assert '"outcomes"' not in calls[0] and '"valid_games"' not in calls[0]
    # Lookups show as a counter in the activity bar, never as lines in the answer.
    assert '[Outil' not in ui.conversation['messages'][-1]['content'] and 'Outils PokeMind · consultation 1' in stages
    ui.chat_input.setPlainText('Combien de défaites dans mes combats?')
    ui.send_chat();wait_until(app,lambda:not ui.chat_busy)
    assert len(calls)==1 and '4 défaites' in ui.transcript.toPlainText() and 'Ajouter statistiques' in ui.transcript.toPlainText()


def test_question_during_background_analysis_is_answered_and_only_imports_wait(ui,app,monkeypatch):
    # The owner's startup analysis sat at « 68 / 69 fichiers » for minutes and held every question.
    calls,loads=[],[]
    class Capture(Fake):
        def ask_stream(self,prompt,history,emit,tool=None):
            calls.append(prompt);super().ask_stream(prompt,history,emit,tool)
    monkeypatch.setattr(window,'CodexAppServer',Capture)
    monkeypatch.setattr(window.Services,'load',lambda services,update=False,**kwargs:loads.append(update))
    ui.cloud_consent.setChecked(True)
    ui.data_busy=True  # background analysis of the combats still running
    ui.chat_input.setPlainText('Question publique inventée pendant l’analyse')
    QTest.keyClick(ui.chat_input,Qt.Key.Key_Return)
    wait_until(app,lambda:len(calls)==1 and not ui.chat_busy)
    assert 'pendant l’analyse' in calls[0] and not loads and not ui.queued_send.isActive()
    ui.ingest_busy=True  # a pasted log is being imported: the next message waits for it
    ui.chat_input.setPlainText('Deuxième question inventée')
    QTest.keyClick(ui.chat_input,Qt.Key.Key_Return)
    QTest.qWait(700)
    assert len(calls)==1 and 'partira tout seul' in ui.provider_status.text()
    assert ui.chat_input.toPlainText()=='Deuxième question inventée'
    ui.data_busy,ui.ingest_busy=False,False
    wait_until(app,lambda:len(calls)==2 and not ui.chat_busy)
    assert not ui.queued_send.isActive()


def test_history_list_opens_wide_with_the_title_first(ui,app):
    ui.preferences['conversations']=[{'id':'0'*32,'title':'Crée-moi un deck puissant avec Dracaufeu inventé','provider':'codex'}]
    ui.refresh_history()
    assert ui.history_picker.itemText(1).startswith('Crée-moi un deck puissant') and ui.history_picker.itemText(1).endswith(' · codex')
    assert ui.history_picker.view().minimumWidth()>=420
    assert ui.history_picker.view().textElideMode()==Qt.TextElideMode.ElideNone
    for combo in (ui.history_picker,ui.starters):
        view=combo.view();delegate=combo.itemDelegate()
        option=QStyleOptionViewItem();option.initFrom(view);option.fontMetrics=view.fontMetrics()
        long_title=combo.model().index(1,0)
        line=view.fontMetrics().height()
        # the open list wraps a long entry over several lines instead of cutting it with '…'
        combo.setItemText(1,'Une question inventée très longue '*6)
        assert delegate.sizeHint(option,long_title).height()>2*line


def test_chat_header_is_light_and_the_work_is_visible_near_the_message_box(ui,app):
    assert not hasattr(ui,'chat_sources') and not hasattr(ui,'sidebar_footer')
    assert ui.context_status.isHidden() and 'données privées' in ui.permission_badge.text()
    assert len(ui.permission_badge.text())<50 and ui.permission_badge.toolTip()
    body=ui.chat_dock.widget().layout()
    order=[body.itemAt(i).widget() for i in range(body.count())]
    assert order.index(ui.activity)<order.index(ui.provider_status)<order.index(ui.chat_input)
    ready=threading.Event()
    class Slow(Fake):
        def ask_stream(self,prompt,history,emit,tool=None):
            self.session='invented-thread';ready.set();self.stopped.wait(4)
    ui.adapter=Slow(ui.store.sandbox)
    ui.cloud_consent.setChecked(True)
    ui.chat_input.setPlainText('Question inventée lente')
    ui.send_chat();wait_until(app,ready.is_set)
    assert ui.activity.property('busy') and ui.activity.spinner.isVisibleTo(ui.activity)
    ui.chat_input.setPlainText('Deuxième question inventée')
    QTest.keyClick(ui.chat_input,Qt.Key.Key_Return)
    assert ui.chat_input.toPlainText()=='Deuxième question inventée' and 'répond encore' in ui.provider_status.text()
    QTest.mouseClick(ui.stop_button,Qt.MouseButton.LeftButton)
    wait_until(app,lambda:not ui.chat_busy)
    assert not ui.activity.property('busy') and ui.activity.spinner.isHidden()


def test_chat_opens_in_a_large_floating_window_and_comes_back(ui,app):
    ui.show();app.processEvents()
    QTest.mouseClick(ui.chat_expand,Qt.MouseButton.LeftButton);app.processEvents()
    screen=ui.screen().availableGeometry()
    assert ui.chat_dock.isFloating() and ui.chat_dock.width()>=min(720,screen.width())
    assert 'droite' in ui.chat_expand.toolTip()
    QTest.mouseClick(ui.chat_expand,Qt.MouseButton.LeftButton);app.processEvents()
    assert not ui.chat_dock.isFloating() and 'Agrandir' in ui.chat_expand.toolTip()
    ui.hide()


def test_terminal_click_opens_the_chat_engine_once(ui,app,monkeypatch):
    opened=[]
    monkeypatch.setattr(ui,'open_terminal',opened.append)
    monkeypatch.setattr(window.terminal,'available',lambda:True)
    engine=['claude']
    monkeypatch.setattr(ui.provider,'currentData',lambda:engine[0])
    ui.navigation_clicked(ui.navigation.item(6));app.processEvents();QTest.qWait(10)
    assert opened==['claude']
    ui.navigation_clicked(ui.navigation.item(5));app.processEvents();QTest.qWait(10)
    assert opened==['claude']
    engine[0]='ollama'
    ui.navigation_clicked(ui.navigation.item(6));app.processEvents();QTest.qWait(10)
    assert opened==['claude','powershell']


def test_activity_waiting_elapsed_and_stop_are_real_and_responsive(ui,app):
    ready=threading.Event()
    class Slow(Fake):
        def ask_stream(self,prompt,history,emit,tool=None):
            self.session='invented-thread';ready.set();self.stopped.wait(4)
    ui.adapter=Slow(ui.store.sandbox)
    ui.cloud_consent.setChecked(True)
    ui.chat_input.setPlainText('Question inventée lente')
    ui.send_chat();wait_until(app,ready.is_set)
    QTest.qWait(150);app.processEvents()
    assert ui.activity.timer.isActive() and ui.activity.elapsed.elapsed()>=100
    assert ui.activity.animation.maximum()==ui.activity.animation.minimum()==0
    assert 'attente du moteur' in ui.activity.label.text()
    QTest.mouseClick(ui.stop_button,Qt.MouseButton.LeftButton)
    wait_until(app,lambda:not ui.chat_busy)
    assert 'Interrompu' in ui.activity.label.text() and not ui.activity.timer.isActive()


def test_sharing_change_does_not_reintroduce_private_prior_messages(ui,app,monkeypatch):
    calls=[]
    class Capture(Fake):
        def ask_stream(self,prompt,history,emit,tool=None):
            calls.append((prompt,history));super().ask_stream(prompt,history,emit,tool)
    monkeypatch.setattr(window,'CodexAppServer',Capture)
    ui.cloud_consent.setChecked(True);ui.sharing.setCurrentIndex(1)
    ui.chat_input.setPlainText('Mes statistiques');ui.send_chat();wait_until(app,lambda:not ui.chat_busy)
    assert '"valid_games": 6' in calls[0][0]
    ui.sharing.setCurrentIndex(0)
    ui.chat_input.setPlainText('Question publique inventée');ui.send_chat();wait_until(app,lambda:not ui.chat_busy)
    assert not calls[1][1] and '"outcomes"' not in calls[1][0]


def test_old_unmarked_log_history_is_never_resent_or_resumed(ui,app,monkeypatch):
    calls=[]
    class Capture(Fake):
        def start(self,session=None):
            calls.append(('start',session));super().start(session)
        def ask_stream(self,prompt,history,emit,tool=None):
            calls.append(('history',history));super().ask_stream(prompt,history,emit,tool)
    monkeypatch.setattr(window,'CodexAppServer',Capture)
    ui.conversation.update(session='invented-old-session',messages=[
        {'role':'user','content':text()}, {'role':'assistant','content':'Ancienne réponse liée au journal privé.'}])
    ui.cloud_consent.setChecked(True)
    ui.chat_input.setPlainText('Question publique inventée')
    ui.send_chat();wait_until(app,lambda:not ui.chat_busy)
    assert ('start',None) in calls and ('history',[]) in calls
    assert ui.conversation['messages'][0]['content']==text()
    ui.chat_input.setPlainText('Deuxième question publique inventée')
    ui.send_chat();wait_until(app,lambda:not ui.chat_busy)
    assert sum(c[0]=='start' for c in calls)==1
    assert len([c for c in calls if c[0]=='history'][-1][1])==2


def test_startup_refresh_reopens_and_really_processes_new_file(local_tmp,app):
    ingestion.ingest(local_tmp,text())
    store=Store(local_tmp);prefs=store.preferences();prefs['startup_refresh']=True
    store.write('preferences.json',prefs)
    (local_tmp/'data/local/battle_logs/new-win.txt').write_text(text('InventedSelf'))
    widget=window.MainWindow(local_tmp);widget.show()
    try:
        wait_until(app,lambda:widget.metrics[0].text()=='2' and not widget.data_busy,10000)
        assert widget.metrics[1].text()==widget.metrics[2].text()=='1'
        assert '1 nouvelles parties uniques' in widget.statusBar().currentMessage()
    finally:
        dispose_window(widget,app)


def test_watch_debounces_until_stable_and_does_not_repeat_same_revision(ui,app,monkeypatch):
    called=[]
    monkeypatch.setattr(ui.services,'logs_revision',lambda:'invented-revision')
    monkeypatch.setattr(ui,'reload',lambda update,auto=False:called.append((update,auto)))
    ui.watch_logs.setChecked(True)
    ui.check_log_folder();wait_until(app,lambda:not ui._watch_busy)
    assert not called
    ui._watch_since-=11
    ui.check_log_folder();wait_until(app,lambda:not ui._watch_busy)
    ui.check_log_folder();wait_until(app,lambda:not ui._watch_busy)
    assert called==[(True,True)]


def test_gallery_grouped_exact60_thumbnail_and_enlargement_keep_list(ui,app,monkeypatch):
    image=QImage(50,70,QImage.Format.Format_RGB32);image.fill(Qt.GlobalColor.blue)
    buffer=QBuffer();buffer.open(QIODevice.OpenModeFlag.WriteOnly);image.save(buffer,'PNG');raw=bytes(buffer.data())
    cards=[{'name':'Invented Creature','quantity':1,'category':'pokemon','printing':'SYN 1','identity':'invented-1'},
           {'name':'Invented Trainer','quantity':1,'category':'trainer','printing':'SYN 2','identity':None},
           {'name':'Invented Energy','quantity':58,'category':'energy','printing':'SYN 3','identity':None}]
    monkeypatch.setattr(ui.services,'gallery_cards',lambda value:cards)
    monkeypatch.setattr(ui.images,'fetch',lambda *a,**k:{'data':raw,'source_url':'https://example.invalid/invented-card.png'})
    export='Pokémon: 1\n1 Invented Creature SYN 1\nTrainer: 1\n1 Invented Trainer SYN 2\nEnergy: 58\n58 Invented Energy SYN 3\nTotal Cards: 60\n'
    ui.loaded_decks([{'label':'Invented','selector':'invented','total':60,'export':export,'kind':'Fixture','legality':'unknown','source':{}}])
    wait_until(app,lambda:len(ui.gallery.tiles)==3 and not ui.gallery.tiles[0].picture.isNull())
    assert sum(t.card['quantity'] for t in ui.gallery.tiles)==60 and ui.deck_text.toPlainText()==export
    assert ui.gallery.tiles[1].picture.isNull() and 'Image indisponible' in ui.gallery.tiles[1].art.text()
    ui.card_images.setChecked(False)
    assert all(t.picture.isNull() for t in ui.gallery.tiles)
    ui.card_images.setChecked(True)
    wait_until(app,lambda:len(ui.gallery.tiles)==3 and not ui.gallery.tiles[0].picture.isNull())
    observed=[]
    def close_dialog():
        dialog=QApplication.activeModalWidget();observed.append(dialog is not None)
        if dialog:dialog.accept()
    QTimer.singleShot(100,close_dialog)
    QTest.mouseClick(ui.gallery.tiles[0].art,Qt.MouseButton.LeftButton)
    assert observed==[True]


def test_streaming_refresh_replaces_only_the_last_bubble_like_a_full_render(ui, app):
    ui.conversation['messages'] = [{'role':'user','content':'Question inventée'},
                                   {'role':'assistant','content':'Début **inventé**'}]
    ui.render_chat()
    for word in ('un', 'deux', 'trois'):
        ui.conversation['messages'][-1]['content'] += ' ' + word
        ui.render_stream()
    streamed = ui.transcript.toPlainText()
    assert streamed.count('POKEMIND') == 1 and 'Début **inventé** un deux trois' in streamed
    ui.render_chat()
    assert 'Début inventé un deux trois' in ui.transcript.toPlainText()
    assert '**' not in ui.transcript.toPlainText()
    ui.conversation['messages'].append({'role':'user','content':'Suite inventée'})
    ui.render_stream()  # structural change: full render fallback
    assert ui.transcript.toPlainText().count('Suite inventée') == 1
    ui.transcript._retranslate()  # language re-render invalidates the streaming tail
    ui.conversation['messages'][-1]['content'] += ' encore'
    ui.render_stream()
    assert ui.transcript.toPlainText().count('Suite inventée encore') == 1


def test_settings_move_and_revert_the_data_folder_for_this_project_only(ui,app,monkeypatch):
    from pokemind import data_location
    assert 'Dans le dossier du projet' in ui.data_folder.text() and ui.data_move.text()=='Sortir mes données du projet…'
    assert ui.data_path.isReadOnly() and ui.data_path.text()==str(Path(ui.root)/'data'/'local')
    ui.data_move.click()
    assert data_location.entry(ui.project_root)['status']=='offer' and not ui.data_move.isEnabled()
    assert 'Ferme et rouvre PokeMind' in ui.statusBar().currentMessage()
    ui.data_state='outside'
    monkeypatch.setattr(window.QMessageBox,'question',lambda *a,**k:window.QMessageBox.StandardButton.No)
    ui.change_data_folder()
    assert data_location.entry(ui.project_root)['status']=='offer'
    monkeypatch.setattr(window.QMessageBox,'question',lambda *a,**k:window.QMessageBox.StandardButton.Yes)
    ui.change_data_folder()
    assert data_location.entry(ui.project_root)=={**data_location.entry(ui.project_root),'status':'project','reason':'reverted'}


def test_development_runs_in_the_project_folder_when_data_lives_elsewhere(ui,local_tmp):
    code=local_tmp/'projet-invente'
    (code/'src').mkdir(parents=True)
    ui.project_root=code
    assert ui.development_workspace()==code.resolve() or ui.development_workspace()==code
    ui.preferences['project_relative']='data'
    (code/'data').mkdir()
    assert ui.development_workspace() is None  # the project's old data folder is still refused


def test_launch_offer_copies_the_data_out_with_progress_or_records_a_refusal(app,local_tmp,monkeypatch):
    from pokemind.desktop import app as desktop_app
    from pokemind import data_location
    root=local_tmp/'projet'
    (root/'data/local/battle_logs').mkdir(parents=True)
    (root/'data/local/battle_logs/partie-inventee.txt').write_text('Tour 1 inventé\n',encoding='utf-8')
    shown=[]
    monkeypatch.setattr(window.QMessageBox,'information',lambda *a,**k:shown.append(a[2]))
    monkeypatch.setattr(window.QMessageBox,'question',lambda *a,**k:window.QMessageBox.StandardButton.No)
    assert desktop_app.offer_move(root)==(root,'project','copie refusée par le propriétaire') and data_location.resolve(root)[1]=='project'
    data_location.request_copy(root)
    monkeypatch.setattr(window.QMessageBox,'question',lambda *a,**k:window.QMessageBox.StandardButton.Yes)
    target,state,outcome=desktop_app.offer_move(root)
    assert outcome=='données copiées hors du projet · 1 fichiers vérifiés'
    assert state=='outside' and (target/'data/local/battle_logs/partie-inventee.txt').read_text(encoding='utf-8')=='Tour 1 inventé\n'
    assert (root/'data/local/battle_logs/partie-inventee.txt').is_file() and 'Copie vérifiée : 1 fichiers' in shown[-1]
    assert data_location.resolve(root)==(target,'outside')


def project_chat(ui, monkeypatch):
    configured, asked = [], []
    class Capture(Fake):
        def configure(self, **kwargs):
            configured.append(kwargs)
            return super().configure(**kwargs)
        def ask_stream(self, prompt, history, emit, tool=None):
            asked.append((prompt, tool({'invented': 1}) if tool else None))
            return super().ask_stream(prompt, history, emit, tool)
    monkeypatch.setattr(window, 'CodexAppServer', Capture)
    monkeypatch.setattr(window.QMessageBox, 'question', lambda *a, **k: window.QMessageBox.StandardButton.Yes)
    ui.chat_project.setChecked(True)
    ui.cloud_consent.setChecked(True)
    return configured, asked


def test_default_chat_works_in_the_project_folder_with_its_rules_and_the_coach_tools(ui, app, monkeypatch):
    from pokemind.assistant import sessions
    assert "'chat_project': True" in Path(sessions.__file__).read_text(encoding='utf-8')  # shipped default
    configured, asked = project_chat(ui, monkeypatch)
    assert window.Store(ui.root).preferences()['chat_project'] is True
    ui.chat_input.setPlainText('Quel deck jouer contre Invented Family?')
    ui.send_chat()
    wait_until(app, lambda: not ui.chat_busy)
    assert configured[-1]['development'] and configured[-1]['coach_tools'] is True
    assert configured[-1]['privacy_acknowledged'] is True and configured[-1]['cwd'] == Path(ui.project_root).resolve()
    prompt, tool_result = asked[-1]
    assert prompt.startswith('Question : Quel deck') and 'DONNÉES POKEMIND PRIORITAIRES' in prompt
    assert tool_result == {'error': 'READ_ONLY_QUERY_REQUIRED'}  # the coach tools answer, not the development stub
    assert ui.conversation['channel'] == 'project:workspace'
    choose(ui, 'development')
    ui.chat_input.setPlainText('Corrige le code PokeMind puis lance les tests Python.')
    ui.send_chat()
    wait_until(app, lambda: not ui.chat_busy)
    assert asked[-1][0].startswith('Corrige le code PokeMind') and 'DONNÉES POKEMIND' not in asked[-1][0]
    assert configured[-1]['coach_tools'] is True and ui.conversation['channel'] == 'project:workspace'


def test_a_pasted_log_never_reaches_the_project_engine_even_by_default(ui, app, monkeypatch):
    configured, asked = project_chat(ui, monkeypatch)
    ui.send_import_question('Analyse le code PokeMind et corrige le fichier Python.')
    wait_until(app, lambda: not ui.chat_busy)
    assert [c['development'] for c in configured] == [False] and ui.conversation['channel'] == 'coach'
    assert configured[0]['cwd'] == ui.store.sandbox


def test_unchecking_the_project_folder_brings_back_the_isolated_coach(ui, app, monkeypatch):
    configured, asked = project_chat(ui, monkeypatch)
    ui.chat_project.setChecked(False)
    assert window.Store(ui.root).preferences()['chat_project'] is False
    ui.chat_input.setPlainText('Quel deck jouer contre Invented Family?')
    ui.send_chat()
    wait_until(app, lambda: not ui.chat_busy)
    assert configured[-1]['development'] is False and configured[-1]['cwd'] == ui.store.sandbox


def test_logo_is_the_approved_pokemind_card_and_the_exe_icon_holds_every_size(app):
    import hashlib, importlib.util, struct
    from PySide6.QtGui import QImage
    from pokemind.desktop import theme
    from pokemind.desktop.theme import BRAND_CARD, card_pixmap, card_width, logo_pixmap, logo_icon_sizes
    root=Path(__file__).resolve().parents[1]
    spec=importlib.util.spec_from_file_location('make_icon',root/'scripts/make_icon.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    original=root/'assets/branding/pokemind-tcg-coach-original.png'
    assert hashlib.sha256(original.read_bytes()).hexdigest()==module.ORIGINAL_SHA256=='30824d84f594be0e1fe33b3e9531f487e497252e17d7a16ff57763b787d7f0f5'
    assert not hasattr(theme,'brain_path')                                      # the drawn two-card logo is gone
    packaged,fresh=QImage(str(BRAND_CARD)),module.card_image(original)           # reproducible from the original
    assert (packaged.width(),packaged.height())==(fresh.width(),fresh.height())==(530,742)
    for x,y in ((265,371),(265,120),(265,650),(40,400),(500,40),(3,3)):
        a,b=packaged.pixelColor(x,y),fresh.pixelColor(x,y)
        assert max(abs(a.red()-b.red()),abs(a.green()-b.green()),abs(a.blue()-b.blue()),abs(a.alpha()-b.alpha()))<=2
    source=QImage(str(original))
    for x,y in ((265,371),(265,120),(400,600)):                                  # half size: the original's own pixels
        a,b=packaged.pixelColor(x,y),source.pixelColor(2*x,2*y)
        assert max(abs(a.red()-b.red()),abs(a.green()-b.green()),abs(a.blue()-b.blue()))<=40
    assert packaged.pixelColor(0,0).alpha()==packaged.pixelColor(529,741).alpha()==0  # page outside the corners only
    assert packaged.pixelColor(0,371).alpha()==packaged.pixelColor(265,0).alpha()==255
    picture=logo_pixmap(256,1.0).toImage()
    assert (picture.width(),picture.height())==(256,256)
    side=(256-card_width(256))//2
    assert picture.pixelColor(side//2,128).alpha()==0 and picture.pixelColor(255-side//2,128).alpha()==0  # never stretched
    ball,brain=picture.pixelColor(128,128),picture.pixelColor(128,95)
    assert min(ball.red(),ball.green(),ball.blue())>180                          # the Poke Ball button
    assert brain.red()>180 and brain.green()<110                                 # the red brain
    whole=card_pixmap(150,1.0)
    assert whole.height()==150 and whole.width()==card_width(150)==107
    hidpi=card_pixmap(104,2.0)
    assert (hidpi.height(),hidpi.devicePixelRatio())==(208,2.0)
    data=module.ico_bytes(logo_icon_sizes())
    reserved,kind,count=struct.unpack_from('<HHH',data)
    assert (reserved,kind,count)==(0,1,len(logo_icon_sizes()))
    for index in range(count):
        side,_,_,_,_,_,length,offset=struct.unpack_from('<BBBBHHII',data,6+16*index)
        assert data[offset:offset+8]==b'\x89PNG\r\n\x1a\n' and offset+length<=len(data)
    large=module.bitmap(164,314,'#07142F')
    assert (large.width(),large.height())==(164,314) and large.pixelColor(82,2).name()=='#07142f'


def test_brand_card_reaches_every_brand_spot_and_the_windows_build(ui,app):
    from pokemind.desktop.binder import BinderCover
    root=Path(__file__).resolve().parents[1]
    ui.show()
    wait_until(app,lambda:not ui.stack.transition.isVisible())
    assert (ui.hero_emblem.width(),ui.hero_emblem.height())==(110,124)
    banner=ui.hero_emblem.grab().toImage()
    middle=banner.pixelColor(55,62)                                               # the card's Poke Ball, mid-banner
    assert min(middle.red(),middle.green(),middle.blue())>150
    assert not ui.windowIcon().isNull() and ui.navigation.item(0).icon().availableSizes()
    cover=BinderCover();cover.resize(420,560)
    centre=cover.grab().toImage().pixelColor(210,280)
    assert min(centre.red(),centre.green(),centre.blue())>150
    build=(root/'scripts/Build-PokeMindDesktop.ps1').read_text(encoding='utf-8')
    assert "pokemind/desktop/branding" in build and '@brandingArguments' in build and '--icon $icon' in build
    installer=(root/'scripts/Build-PokeMindInstaller.ps1').read_text(encoding='utf-8')
    setup=(root/'packaging/PokeMind.iss').read_text(encoding='utf-8')
    assert 'make_icon.py $icon' in installer and '/DLargeImage=' in installer
    assert 'SetupIconFile={#IconFile}' in setup and 'WizardImageFile={#LargeImage}' in setup


def test_settings_are_short_rows_in_categories_with_details_on_demand(ui,app):
    ui.show();ui.navigation.setCurrentRow(5)
    wait_until(app,lambda:not ui.stack.transition.isVisible())
    assert list(ui.settings_tabs)==['general','coach','battles','data','updates','about']
    assert ui.settings_tabs['general'].isChecked() and ui.theme.isVisibleTo(ui) and not ui.cloud_consent.isVisibleTo(ui)
    QTest.mouseClick(ui.settings_tabs['coach'],Qt.MouseButton.LeftButton)
    assert ui.cloud_consent.isVisibleTo(ui) and not ui.theme.isVisibleTo(ui)
    assert len(ui.chat_project.text())<60 and 'AGENTS.md' in ui.chat_project.parentWidget().toolTip()
    assert ui.security_details.isHidden() and 'isolation externe' in ui.security_details.text()
    QTest.mouseClick(ui.security_toggle,Qt.MouseButton.LeftButton)
    assert ui.security_details.isVisibleTo(ui) and 'Masquer' in ui.security_toggle.text()
    QTest.mouseClick(ui.settings_tabs['data'],Qt.MouseButton.LeftButton)
    assert ui.data_path.isVisibleTo(ui) and ui.copy_diagnostic.isVisibleTo(ui)
    ui.resize(1200,760);app.processEvents()
    assert ui.stack.currentWidget().horizontalScrollBar().maximum()==0
    ui.hide()


def test_battles_page_shows_summary_tiles_and_a_record_bar_sorted_by_losses(ui,app):
    groups=[{'archetype':'Famille inventée douce','wins':3,'losses':1,'unknown':0,'n':4},
            {'archetype':'Famille inventée coriace','wins':0,'losses':5,'unknown':1,'n':6}]
    ui.services.report={**ui.services.report,'groups':groups}
    ui.filter_matchups()
    assert [ui.battle_tiles[k].text() for k in ('games','wins','losses')]==['10','3','6']
    assert ui.battle_tiles['rival'].text().startswith('Famille inventée coriace')
    assert ui.matchups.item(0,0).text()=='Famille inventée coriace'
    delegate=ui.matchups.itemDelegateForColumn(4)
    assert isinstance(delegate,window.RecordBarDelegate)
    ui.navigation.setCurrentRow(1);wait_until(app,lambda:not ui.stack.transition.isVisible())
    ui.matchups.clearSelection();app.processEvents()
    picture=ui.matchups.viewport().grab().toImage()
    rect=ui.matchups.visualRect(ui.matchups.model().index(0,4))
    from PySide6.QtGui import QColor
    from pokemind.desktop.theme import colors
    loss=QColor(colors(ui.preferences['theme'])['red'])  # losses keep the theme's red
    reds=sum(1 for x in range(rect.left(),rect.right(),3)
             if (lambda c:sum(abs(a-b) for a,b in zip(c.getRgb()[:3],loss.getRgb()[:3]))<40)(picture.pixelColor(x,rect.center().y())))
    assert reds>5
    ui.matchup_filter.setText('douce')
    assert ui.matchups.rowCount()==1 and ui.battle_tiles['games'].text()=='10'
    ui.matchup_filter.clear()


def test_learning_page_reads_as_tiles_bars_and_plans_without_internal_names():
    from pokemind.desktop.insights import learning_view
    from pokemind.desktop.theme import colors
    learning={'current':[
        {'kind':'observed_game_event','recorded_at':'2026-11-01T10:00:00','payload':{'matches':['M1','M2','M3']}},
        {'kind':'derived_statistic','recorded_at':'2026-10-31T10:00:00','payload':{'groups':[{'archetype':'Famille inventée','wins':1,'losses':2,'n':3}]}},
        {'kind':'test_plan','recorded_at':'2026-10-31T10:00:00','payload':{'recommendations':[
            {'archetype':'Famille inventée','loss_match_refs':['M2'],'plan':{'alternatives':[{'archetypes':['Base inventée']}]}}]}}],
        'history':[{'recorded_at':'2026-10-30T09:00:00','revises':'derived_statistic'}]}
    tiles,text=learning_view(learning,colors('dark'))
    assert tiles=={'games':'3','opponents':'1','plans':'1','updated':'2026-11-01'}
    text=str(text)
    assert 'Famille inventée' in text and '1V · 2D · n=3' in text and 'Base inventée' in text
    assert 'pokemind://page/2' in text and 'Bilans par adversaire' in text
    assert 'derived_statistic' not in text and 'observed_game_event' not in text
    empty_tiles,empty=learning_view(None,colors('dark'))
    assert set(empty_tiles.values())=={'—'} and 'absent' in str(empty)


def test_cards_page_opens_the_binder_with_cards_turns_pages_and_shows_a_card(ui,app,monkeypatch):
    calls,shown=[],[]
    def browse(language='fr',offset=0,limit=18):
        calls.append((language,offset,limit))
        cards=[{'tcgdex_id':'inv-%d'%i,'language':language,'name':'Carte inventée %d'%i,'category':'pokemon',
                'set_id':'inv','local_id':str(i)} for i in range(offset,min(offset+limit,30))]
        return {'language':language,'offset':offset,'total':30,'cards':cards}
    def card(identity,language):
        shown.append((identity,language))
        return {'tcgdex_id':identity,'language':language,'name':'Carte inventée','category':'pokemon','hp':60,
                'dated_legality':{'in_person':{'status':'unknown'},'live':{'status':'unknown'}},'provenance':{}}
    monkeypatch.setattr(ui.services,'browse_cards',browse)
    monkeypatch.setattr(ui.services,'card',card)
    ui.preferences['card_images']=False
    ui.navigation.setCurrentRow(3)
    wait_until(app,lambda:ui.binder.slots[0].card is not None)
    per=ui.binder.per_spread()
    assert calls[0]==('fr',0,per) and ui.binder.slots[0].card['name']=='Carte inventée 0'
    assert '30' in ui.binder.page_label.text() and not ui.binder.previous.isEnabled() and ui.binder.next.isEnabled()
    ui.binder.next.click()
    wait_until(app,lambda:ui.binder.offset==per)
    assert calls[-1]==('fr',per,per) and ui.binder.slots[0].card['name']=='Carte inventée %d'%per
    ui.binder.slots[1].activated.emit(ui.binder.slots[1].card)
    wait_until(app,lambda:bool(shown) and not ui.jobs)
    assert ui.card_panel.isVisibleTo(ui) and shown[0]==('inv-%d'%(per+1),'fr')
    monkeypatch.setattr(ui.services,'search_cards',lambda query,language:[
        {'tcgdex_id':'inv-a','language':'fr','name':'Trouvée A','category':'trainer'},
        {'tcgdex_id':'inv-b','language':'en','name':'Found B','category':'energy'}])
    ui.card_query.setText('trouvée');ui.search_cards()
    wait_until(app,lambda:ui.binder.total==2)
    assert [s.card['name'] for s in ui.binder.slots[:2]]==['Trouvée A','Found B'] and ui.binder.slots[2].card is None
    assert ui.binder_reset.isVisibleTo(ui) and ui.card_results.rowCount()==2
    ui.binder_reset.click()
    wait_until(app,lambda:ui.binder.total==30)
    assert ui.binder.title.text()=='Classeur'


def test_welcome_assistant_detects_engines_switches_language_and_saves_once(app,local_tmp,monkeypatch):
    from pokemind.desktop import welcome, app as desktop_app
    from pokemind.desktop.i18n import set_language
    from pokemind.assistant.sessions import Store
    wizard=welcome.WelcomeWizard({'language':'fr','provider':'codex','card_images':True},detect=lambda c:c=='claude')
    assert wizard.engine()=='claude'                                   # codex is missing: the installed engine is offered
    assert wizard.windowTitle()=='Bienvenue dans PokeMind'
    wizard.language.setCurrentIndex(wizard.language.findData('en'))
    assert wizard.windowTitle()=='Welcome to PokeMind' and wizard.next.text()=='Next'
    for _ in range(3):
        wizard.next.click()
    assert wizard.next.text()=='Start' and 'Claude Code' in wizard.summary.text()
    wizard.cloud.setChecked(True);wizard.watch.setChecked(True)
    assert wizard.choices()=={'language':'en','provider':'claude','cloud_consent':True,'watch_logs':True,
                              'startup_refresh':False,'card_images':True}
    set_language('fr')
    shown=[]
    def accept(self):
        shown.append(True);self.engine_buttons['ollama'].setChecked(True);return 1
    monkeypatch.setattr(welcome.WelcomeWizard,'exec',accept)
    assert desktop_app.first_run(local_tmp)==('accepted',True)              # no catalogue yet: offered, ticked
    saved=Store(local_tmp).preferences()
    assert saved['provider']=='ollama' and saved['language']=='fr' and 'catalog' not in saved
    assert desktop_app.first_run(local_tmp)==('known',False) and len(shown)==1
    set_language('fr')


def test_installed_copy_needs_no_project_folder_and_downloads_the_card_catalogue_once(local_tmp, monkeypatch, app, ui):
    from pokemind import data_location, catalog_download
    monkeypatch.setenv('POKEMIND_DATA_ROOT', str(local_tmp / 'appdata'))
    root, workspace = data_location.standalone()
    assert root == local_tmp / 'appdata' and workspace == root / 'workspace' and workspace.is_dir()
    calls = []  # the ui fixture already replaced the battle report, the decks and the engines
    def download(target, *, progress, cancelled, latest=False):
        assert latest  # the newest TCGdex cards first, the tested ones as fallback
        calls.append(target)
        progress('download', 5_000_000, 14_700_000)
        progress('import', 0, 6)
        folder = catalog_download.campaign_folder(target)
        folder.mkdir(parents=True)
        (folder / 'public.sqlite3').write_bytes(b'')
        return {'status': 'COMPLETE', 'printings': 23864}
    monkeypatch.setattr(catalog_download, 'download', download)
    widget = window.MainWindow(root, project_root=workspace, data_state='standalone')
    try:
        widget.show()
        wait_until(app, lambda: widget.metrics[0].text() == '6' and not widget.jobs)
        assert widget.standalone and widget.development_workspace() == workspace
        assert widget.chat_mode.findData('development') == -1  # no PokeMind code to develop in an installed copy
        assert widget.chat_project.parentWidget().isHidden() and widget.project_relative.parentWidget().isHidden()
        assert widget.data_move.isHidden() and widget.data_folder.text() == 'Sur ce PC, dans le dossier de l’application.'
        assert not widget.catalog_button.isHidden() and '25 Mo' in widget.catalog_status.text()
        widget.binder_unavailable('LOCAL_SERVICE_UNAVAILABLE')
        assert not widget.binder.download.isHidden() and 'hors ligne' in widget.binder.empty_text.text()
        widget.binder.download.click()
        wait_until(app, lambda: not widget.catalog_busy)
        assert calls == [root] and 'Catalogue de cartes prêt : 23864 cartes.' in widget.statusBar().currentMessage()
        assert widget.catalog_button.isHidden() and widget.catalog_status.text().startswith('Sur ce PC, hors ligne')
        widget.download_catalog()
        assert calls == [root]  # present: never fetched again
    finally:
        dispose_window(widget, app)


def test_catalogue_failure_keeps_the_offer_and_the_welcome_assistant_asks_for_it(monkeypatch, app, ui):
    from pokemind import catalog_download
    from pokemind.desktop import welcome
    monkeypatch.setattr(catalog_download, 'download',
                        lambda target, **kwargs: {'status': 'STOPPED', 'error': 'CATALOG_DOWNLOAD_BLOB_MISMATCH'})
    ui.download_catalog()
    wait_until(app, lambda: not ui.catalog_busy)
    assert 'CATALOG_DOWNLOAD_BLOB_MISMATCH' in ui.catalog_status.text() and ui.catalog_button.isEnabled()
    assert not ui.binder.download.isHidden() and 'Rien n’a été remplacé' in ui.binder.empty_text.text()
    wizard = welcome.WelcomeWizard({'language': 'fr', 'provider': 'codex'}, detect=lambda c: True, catalog_missing=True)
    for _ in range(3):
        wizard.next.click()
    assert wizard.wants_catalog() and 'Catalogue des cartes : téléchargé à l’ouverture' in wizard.summary.text()
    wizard.catalog.setChecked(False)
    assert not wizard.wants_catalog()
    assert not welcome.WelcomeWizard({}, detect=lambda c: True).wants_catalog()


def test_release_qa_never_opens_a_real_application_folder(local_tmp, monkeypatch, app):
    from pokemind.desktop import app as desktop_app
    from pokemind.desktop.i18n import set_language
    monkeypatch.setenv('POKEMIND_STANDALONE', '1')
    monkeypatch.setenv('POKEMIND_DESKTOP_SMOKE', '1')
    monkeypatch.delenv('POKEMIND_DATA_ROOT', raising=False)
    try:
        assert desktop_app.launch(local_tmp / 'no-project-here') == 2  # before any folder or window
    finally:
        set_language('fr')


def test_launch_applies_a_requested_reset_before_the_welcome_assistant(local_tmp, monkeypatch, app):
    from pokemind import data_reset, diagnostics
    from pokemind.desktop import app as desktop_app
    from pokemind.desktop.i18n import set_language
    root = local_tmp / 'standalone'
    (root / 'data/local/chat').mkdir(parents=True)
    (root / 'data/local/chat/preferences.json').write_text('{}', encoding='utf-8')
    (root / 'data/local/web_memory.sqlite3').write_bytes(b'invented')
    data_reset.request(root, True)
    monkeypatch.setenv('POKEMIND_STANDALONE', '1')
    monkeypatch.setenv('POKEMIND_DATA_ROOT', str(root))
    monkeypatch.delenv('POKEMIND_DESKTOP_SMOKE', raising=False)
    monkeypatch.setattr(diagnostics, 'setup', lambda selected: None)
    seen = []
    monkeypatch.setattr(desktop_app, 'reset_notice', lambda reset: seen.append(
        ('notice', reset['status'], Path(reset['kept_copy']).parent)))
    def first_run(selected):
        seen.append(('welcome', (selected / 'data/local/chat/preferences.json').exists()))
        return 'accepted', False
    monkeypatch.setattr(desktop_app, 'first_run', first_run)
    class Window:
        def __init__(self, selected, **kwargs):
            seen.append(('window', selected))
        def show(self):
            pass
    monkeypatch.setattr(window, 'MainWindow', Window)
    monkeypatch.setattr(app, 'exec', lambda: 0)
    try:
        assert desktop_app.launch(local_tmp / 'no-project-here') == 0
    finally:
        set_language('fr')
    assert seen == [('notice', 'RESET', root / 'data/local'), ('welcome', False), ('window', root)]


def test_reset_notice_names_the_kinds_removed_and_where_the_copy_is(monkeypatch, app):
    from pokemind.desktop import app as desktop_app
    from pokemind.desktop.i18n import QMessageBox
    shown = []
    monkeypatch.setattr(QMessageBox, 'information', lambda parent, title, text: shown.append(str(text)))
    monkeypatch.setattr(QMessageBox, 'warning', lambda parent, title, text: shown.append('!' + str(text)))
    desktop_app.reset_notice({'status': 'RESET', 'full': False, 'categories': ['games', 'chats'],
                              'kept_copy': 'dossier-inventé'})
    desktop_app.reset_notice({'status': 'RESET', 'full': True, 'categories': [], 'kept_copy': None})
    desktop_app.reset_notice({'status': 'FAILED', 'kept_copy': None})
    assert shown[0].startswith('Données retirées : Parties et statistiques, Discussions.') and 'dossier-inventé' in shown[0]
    assert shown[1].startswith('PokeMind a été réinitialisé.') and 'effacées' in shown[1]
    assert shown[2].startswith('!La réinitialisation n’a pas pu se faire') and 'Rien n’a été effacé' in shown[2]


def test_words_never_choose_research_or_development_only_the_mode_under_the_chat_does(ui, app, monkeypatch):
    from pokemind import batch_public_research as research
    from pokemind.assistant.tools import RESEARCH_STARTERS, STARTERS
    collected, configured = [], []
    class Capture(Fake):
        def configure(self, **kwargs):
            configured.append(kwargs['development'])
            return super().configure(**kwargs)
    monkeypatch.setattr(research, 'research', lambda *a, **k: collected.append(k) or {
        'status':'SAVED','persisted':True,'added':0,'updated':0,'already_known':0,'unverified':0,'facts':[],'sources':[]})
    monkeypatch.setattr(research, 'research_matchups', lambda *a, **k: {'gets':0})
    monkeypatch.setattr(research, 'matchup_database', lambda *a: None)
    monkeypatch.setattr(window, 'CodexAppServer', Capture)
    monkeypatch.setattr(window.QMessageBox, 'question', lambda *a, **k: window.QMessageBox.StandardButton.Yes)
    ui.chat_project.setChecked(False)
    ui.cloud_consent.setChecked(True)
    assert [ui.chat_mode.itemData(i) for i in range(ui.chat_mode.count())] == ['coach', 'research', 'development']
    ui.chat_input.setPlainText('Cherche sur le web la méta actuelle, puis corrige le code Python de PokeMind et lance les tests.')
    ui.send_chat();wait_until(app, lambda: not ui.chat_busy)
    assert collected == [] and configured == [False] and ui.conversation['channel'] == 'coach'
    choose(ui, 'research')
    ui.chat_input.setPlainText('Quoi de neuf?')
    ui.send_chat()
    assert ui.chat_mode.currentData() == 'coach'  # one collection per choice
    wait_until(app, lambda: not ui.chat_busy)
    assert len(collected) == 1 and configured == [False, False]
    choose(ui, 'development')
    ui.chat_input.setPlainText('Quel deck jouer?')
    ui.send_chat();wait_until(app, lambda: not ui.chat_busy)
    assert configured[-1] is True and ui.chat_mode.currentData() == 'development' and len(collected) == 1
    choose(ui, 'coach')
    ui.pick_starter(STARTERS.index(RESEARCH_STARTERS[0]) + 1)
    assert ui.chat_mode.currentData() == 'research' and ui.chat_input.toPlainText() == RESEARCH_STARTERS[0]


def test_a_follow_up_in_the_same_engine_session_pastes_only_the_data_that_changed(ui, app, monkeypatch):
    from pokemind.assistant.provider import ProviderError
    prompts, fail = [], []
    class Capture(Fake):
        def ask_stream(self, prompt, history, emit, tool=None):
            prompts.append(prompt)
            if fail:
                raise ProviderError('INVENTED_PROVIDER_ERROR')
            return super().ask_stream(prompt, history, emit, tool)
    monkeypatch.setattr(window, 'CodexAppServer', Capture)
    monkeypatch.setattr(window, 'ClaudeCode', Capture)
    ui.chat_project.setChecked(False)
    ui.cloud_consent.setChecked(True)
    def ask(question):
        ui.chat_input.setPlainText(question)
        ui.send_chat()
        wait_until(app, lambda: not ui.chat_busy)
    full = lambda prompt: 'Rapport personnel local et Learning Loop' in prompt and 'unchanged_since' not in prompt
    ask('Quel deck jouer contre Invented Family?')
    ask('Et au deuxième tour?')
    assert full(prompts[0]) and 'Rapport personnel local et Learning Loop' not in prompts[1]
    assert '"unchanged_since_previous_message": [' in prompts[1] and '"source_priority"' in prompts[1]
    assert len(prompts[1]) < len(prompts[0])
    fail.append(True)
    ask('Une question qui échoue')
    fail.clear()
    ask('Et maintenant?')  # after a failed turn, the engine gets everything again
    assert full(prompts[3])
    ui.new_conversation()
    ask('Nouvelle discussion')
    assert full(prompts[4])


def test_new_install_allows_the_cloud_coach_with_anonymous_statistics_by_default(local_tmp,app):
    # Owner, 2026-11-06 (D-287): no opt-in to tick before a pasted log reaches the coach; still switchable.
    from pokemind.desktop import welcome
    preferences=window.Store(local_tmp).preferences()
    assert preferences['cloud_consent'] is True and preferences['sharing']=='aggregates'
    wizard=welcome.WelcomeWizard(preferences,detect=lambda c:True)
    assert wizard.cloud.isChecked() and wizard.choices()['cloud_consent'] is True
    wizard.cloud.setChecked(False)
    assert wizard.choices()['cloud_consent'] is False
    window.Store(local_tmp).write('preferences.json',{'cloud_consent':False,'sharing':'public'})
    kept=window.Store(local_tmp).preferences()
    assert kept['cloud_consent'] is False and kept['sharing']=='public'      # an explicit choice stays
    shiboken6.delete(wizard)                                                   # while the Qt application lives


DECK_60='Pokémon: 20\n20 Invented Alpha INV 1\nTrainer: 20\n20 Invented Beta INV 2\nEnergy: 20\n20 Basic Invented Energy INV 3'


def test_owner_enters_a_deck_and_marks_it_main_for_the_overview_and_the_coach(ui,app,monkeypatch):
    # Owner, 2026-11-06 (D-288): « que je puisse rentrer moi-même des decks… ça c'est mon deck principal ».
    from pokemind.desktop.deck_entry import DeckEntryDialog
    from pokemind.desktop.insights import favorite_key
    monkeypatch.setattr(window.Services,'deck_options',lambda s:[{'label':d['name'],'selector':'mon deck','export':d['export'],
        'source':{},'kind':'Mon deck · référence personnelle entrée par moi','legality':'inconnue','total':60} for d in s.my_decks()])
    dialog=DeckEntryDialog(ui.services,ui)
    dialog.name.setText('Mon deck inventé');dialog.export.setPlainText(DECK_60.replace('20 Basic','19 Basic'))
    dialog.save()
    assert dialog.result is None and '60 cartes' in dialog.message.text() and ui.services.my_decks()==[]
    dialog.export.setPlainText(DECK_60)
    dialog.save()
    assert dialog.result['status']=='SAVED_DECK' and dialog.result['main'] is True
    record=ui.services.my_decks()[0]
    assert record['source']=='owner' and record['name']=='Mon deck inventé'
    ui.deck_added(dialog.result)
    key=favorite_key({'export':DECK_60})
    wait_until(app,lambda:ui.preferences['main_deck']==key and ui.deck_rows)
    assert window.Store(ui.root).preferences()['main_deck']==key                 # kept after a restart
    assert '· ♛ Mon deck inventé' in ui.deck_picker.currentText() and ui.main_button.isChecked()
    assert any('Deck principal : Mon deck inventé' in w.text() for w in ui.findChildren(window.QPushButton) if w.isVisibleTo(ui) or True)
    assert ui.services.prepare_question('Quel est mon deck?','aggregates')['owner_main_deck']['export']==DECK_60
    assert 'owner_main_deck' not in ui.services.prepare_question('Quel est mon deck?','public')   # personal: never public-only
    ui.toggle_main()
    assert ui.preferences['main_deck']=='' and not ui.main_button.isChecked()
    assert 'owner_main_deck' not in ui.services.prepare_question('Quel est mon deck?','aggregates')
    shiboken6.delete(dialog)                                                   # while the Qt application lives


def test_owner_entered_decks_are_labelled_and_main_deck_preference_is_validated(local_tmp):
    services=window.Services(local_tmp)
    assert services.save_deck('Mien',DECK_60,source='owner')['status']=='SAVED_DECK'
    assert services.save_deck('Autre',DECK_60,source='intrus')=={'error':'DECK_SOURCE_INVALID'}
    option=services.deck_options()[0]
    assert option['owner_entered'] is True and 'entrée par moi' in option['kind'] and 'personnelle' in option['kind']
    store=window.Store(local_tmp)
    store.write('preferences.json',{'main_deck':'pas-un-hash'})
    with pytest.raises(ValueError,match='CHAT_PREFERENCES_INVALID'):
        store.preferences()


# Deck Lab › Statistiques (PM-DECKLAB-PUBLIC-STATS-001): invented public tournaments, the real collector and engines.
from test_deck_public_stats import server, PRIVATE_DECK, A, X  # noqa: E402,F401  (server is a pytest fixture)


def _public_rows():
    other=PRIVATE_DECK.replace('3 Betadrake INV 3','3 Alphamon ex INV 9')
    return [{'label':'Gammaroo secret','selector':'mon deck','export':PRIVATE_DECK,'source':{},'total':60,
             'kind':'Mon deck · référence personnelle entrée par moi','legality':'inconnue'},
            {'label':'Autre deck inventé','selector':'mon deck','export':other,'source':{},'total':60,
             'kind':'Mon deck · référence personnelle entrée par moi','legality':'inconnue'}]


def _settled(ui):
    return not ui.jobs and not ui.public_stats_busy


def test_013_selector_daily_refresh_reranks_preserves_selection_gallery_and_favorites(ui, app, server, monkeypatch):
    from pokemind import deck_public_stats
    from pokemind.desktop.insights import favorite_key
    web = server(['t-bo1'])
    rows = _public_rows()
    ui.navigation.setCurrentRow(2)
    # Pause the shared collector: offline unknown labels appear immediately and remain selectable.
    entered, release = threading.Event(), threading.Event()
    refresh = deck_public_stats.refresh
    def delayed(*a, **k):
        entered.set()
        assert release.wait(5)
        return refresh(*a, **k)
    monkeypatch.setattr(deck_public_stats, 'refresh', delayed)
    ui.loaded_decks(ui.services.rank_decks(rows))
    wait_until(app, entered.is_set)
    ui.deck_picker.setCurrentIndex(1)
    wait_until(app, lambda: len(ui.gallery.tiles) > 0)
    key = favorite_key(ui.deck_rows[1])
    ui.favorite_button.click()
    ui.main_button.click()
    wait_until(app, lambda: len(ui.jobs) == 1)  # only the paused collector remains, both gallery jobs settled
    generation = ui.gallery.generation
    ui.compare_picker.setCurrentIndex(0)
    compare = favorite_key(ui.deck_rows[0])
    release.set()
    wait_until(app, lambda: _settled(ui))
    assert len(web.urls) == 5
    rates = [r['public_ranking']['fraction'] for r in ui.deck_rows if r['public_ranking']['fraction'] is not None]
    assert rates == sorted(rates, reverse=True) and rates
    assert favorite_key(ui.deck_rows[ui.deck_picker.currentIndex()]) == key
    assert favorite_key(ui.deck_rows[ui.compare_picker.currentIndex()]) == compare
    assert ui.gallery.generation == generation
    assert key in ui.preferences['favorite_decks'] and ui.preferences['main_deck'] == key
    assert ui.favorite_button.isChecked() and ui.main_button.isChecked()
    for i in range(ui.deck_picker.count()):
        label = ui.deck_picker.itemText(i)
        tip = ui.deck_picker.itemData(i, Qt.ItemDataRole.ToolTipRole)
        if ui.deck_rows[i]['public_ranking']['fraction'] is not None:
            assert label.startswith('#') and '% · ' in label
            assert '% PUBLIC BO1' in tip and 'n=' in tip and 'Limitless' in tip
            assert 'https://' in tip and 'Instantané' in tip
    ui.deck_picker.setFocus()
    QTest.keyClick(ui.deck_picker, Qt.Key.Key_Home)
    assert ui.deck_picker.currentIndex() == 0
    ui.rerank_decks()
    wait_until(app, lambda: _settled(ui))
    assert len(web.urls) == 5  # relabeling does not collect or loop


def test_013_selector_late_worker_cannot_replace_a_newer_result(ui, app, monkeypatch):
    rows = _public_rows()
    entered, release = threading.Event(), threading.Event()
    calls = []
    def load():
        calls.append(1)
        if len(calls) == 1:
            entered.set()
            assert release.wait(5)
            return rows[:1]
        return rows[1:]
    monkeypatch.setattr(ui.services, 'deck_options', load)
    ui.reload_decks()
    wait_until(app, entered.is_set)
    ui.reload_decks()
    wait_until(app, lambda: ui.deck_rows and ui.deck_rows[0]['label'] == rows[1]['label'])
    release.set()
    wait_until(app, lambda: _settled(ui))
    assert ui.deck_rows[0]['label'] == rows[1]['label']


@pytest.mark.parametrize('width', [1100, 1500])
def test_013_selector_full_rate_accessibility_at_narrow_width(ui, app, width):
    from datetime import date
    from pathlib import Path
    rows = _public_rows()
    for row in rows:
        row['public_ranking'] = {'fraction': .625, 'n': 40, 'mode': 'BO1',
            'window': {'since': '2026-10-16', 'until': date.today().isoformat()},
            'source_url': 'https://play.limitlesstcg.com/api/tournaments', 'last_success_at': '2026-11-12',
            'refresh': {'automatic_due': False}}
    ui.navigation.setCurrentRow(2)
    ui.resize(width, 970)
    ui.loaded_decks(rows)
    wait_until(app, lambda: _settled(ui))
    assert ui.deck_picker.currentText().startswith('#1 · 62,5 % · ') and 'n=40' in ui.deck_picker.toolTip()
    assert ui.deck_picker.accessibleName() == ui.deck_picker.currentText()
    assert ui.deck_picker.width() <= ui.stack.width()
    assert ui.gallery.horizontalScrollBar().maximum() == 0
    output = Path(__file__).resolve().parents[1] / 'build/qa-013'
    output.mkdir(parents=True, exist_ok=True)
    ui.grab().save(str(output / f'selector-{width}-{ui.devicePixelRatioF():g}.png'))


def test_deck_lab_statistics_tab_one_daily_refresh_no_mixing_languages_and_themes(ui,app,server):
    from pokemind.desktop.insights import favorite_key
    from pokemind.desktop.i18n import set_language
    web=server(['t-bo1'])
    ui.navigation.setCurrentRow(2)
    rows=_public_rows()
    ui.loaded_decks(rows)
    assert ui.deck_views.count()==4 and ui.deck_views.tabText(2)=='Statistiques'
    assert ui.deck_views.tabText(0).startswith('Galerie') and ui.deck_views.tabText(1)=='Liste texte'
    wait_until(app,lambda:_settled(ui))
    assert web.urls==[]                                                 # no request while the tab is not shown
    ui.deck_views.setCurrentIndex(2)
    wait_until(app,lambda:_settled(ui) and ui.public_stats.view and ui.public_stats.view.get('archetype'))
    view=ui.public_stats.view
    assert view['identity']['archetype_id']==A[0] and view['deck_key']==favorite_key(rows[0])
    assert len(web.urls)==5 and all('/api/' in url for url in web.urls)
    assert 'Alphamon Betadrake' in ui.public_stats.identity.text() and 'pas de tes 60 cartes exactes' in ui.public_stats.identity_detail.text()
    assert 'Taux de victoire BO1' in ui.public_stats.summary.text() and 'n=' in ui.public_stats.summary.text()
    assert 'Limitless' in ui.public_stats.source.text() and 'pas date des matchs' in ui.public_stats.source.text()
    assert ui.public_stats.matchups.rows and 'n=' in ui.public_stats.matchups.accessibleDescription()
    assert ui.public_stats.meta.rows and ui.public_stats.mode.count()==1 and not ui.public_stats.mode.isEnabled()
    ui.public_stats.matchups.setFocus()
    QTest.keyClick(ui.public_stats.matchups,Qt.Key.Key_Down)
    assert ui.public_stats.matchups.hovered==0 and 'n=' in ui.public_stats.matchups.toolTip()   # keyboard reading
    sent=len(web.urls)
    ui.deck_picker.setCurrentIndex(1)                                   # another deck the same day: zero request
    wait_until(app,lambda:_settled(ui) and ui.public_stats.view['deck_key']==favorite_key(rows[1]))
    assert ui.public_stats.view['identity']['archetype_id']==X[0] and len(web.urls)==sent
    ui.deck_picker.setCurrentIndex(0);ui.deck_picker.setCurrentIndex(1);ui.deck_picker.setCurrentIndex(0)
    wait_until(app,lambda:_settled(ui))
    assert ui.public_stats.view['deck_key']==favorite_key(rows[0])   # quick selections: the last deck wins, unmixed
    assert ui.public_stats.view['identity']['archetype_id']==A[0]
    ui.deck_views.setCurrentIndex(0);ui.deck_views.setCurrentIndex(2)
    wait_until(app,lambda:_settled(ui))
    assert len(web.urls)==sent                                          # tab changes: no request
    QTest.mouseClick(ui.public_stats.refresh_button,Qt.MouseButton.LeftButton)   # « Actualiser » right after: bounded
    wait_until(app,lambda:_settled(ui) and 'trop rapprochée' in ui.public_stats.status.text())
    assert len(web.urls)==sent and ui.public_stats.refresh_button.isEnabled()
    ui.theme.setCurrentIndex(ui.theme.findData('light'))
    assert ui.public_stats.theme=='light' and ui.public_stats.matchups.theme=='light'
    ui.theme.setCurrentIndex(ui.theme.findData('dark'))
    try:
        ui.language.setCurrentIndex(ui.language.findData('en'));app.processEvents()
        assert ui.deck_views.tabText(2)=='Statistics' and ui.public_stats.refresh_button.text()=='Refresh'
        assert 'Public archetype' in ui.public_stats.identity.text() and 'Win rate BO1' in ui.public_stats.summary.text()
        assert 'retrieval date, not match date' in ui.public_stats.source.text()
    finally:
        ui.language.setCurrentIndex(ui.language.findData('fr'));app.processEvents()
        set_language('fr')
    assert 'Archétype public' in ui.public_stats.identity.text() and len(web.urls)==sent


def test_deck_lab_statistics_without_snapshot_and_a_refused_source_stay_honest(ui,app,server):
    web=server(['t-bo1'],failure='429')
    ui.navigation.setCurrentRow(2)
    ui.loaded_decks(_public_rows())
    ui.deck_views.setCurrentIndex(2)
    wait_until(app,lambda:_settled(ui) and ui.public_stats.view and ui.public_stats.view['refresh']['last_outcome'])
    assert len(web.urls)==1                                             # stopped at the first refusal
    assert ui.public_stats.view['status']=='NO_SNAPSHOT' and ui.public_stats.view['archetype'] is None
    assert 'Aucun instantané public' in ui.public_stats.identity.text()
    assert 'dernier instantané valide conservé' in ui.public_stats.source.text()
    assert ui.public_stats.matchups.rows==[] and ui.public_stats.summary.text()==''
    ui.deck_picker.setCurrentIndex(1)
    wait_until(app,lambda:_settled(ui))
    assert len(web.urls)==1                                             # no retry loop the same day


# 016: presentation-only fixtures; the statistical engines keep their own independent oracle tests.
def ranking_016():
    from copy import deepcopy
    from datetime import date
    rows = []
    for i, fraction in enumerate((57 / 117, .42, None, None, None)):
        rows.append({'label': f'Invented deck {i} ' + 'very long invented title ' * 5,
            'selector': f'invented-{i}', 'export': PRIVATE_DECK.replace('Invented Trainer', f'Invented Trainer {i}'),
            'kind': 'Invented reference', 'legality': 'Unknown', 'source': {}, 'total': 60,
            'public_ranking': {'fraction': fraction, 'n': 117 if i == 0 else 100 if i == 1 else 0,
                'mode': 'BO1', 'window': {'since': '2026-10-18', 'until': date.today().isoformat()},
                'source_url': 'https://play.limitlesstcg.com/api/tournaments',
                'last_success_at': date.today().isoformat(), 'refresh': {'automatic_due': False}}})
    return deepcopy(rows)


def public_view_016():
    from copy import deepcopy
    data = {'n': 117, 'wins': 57, 'losses': 59, 'ties': 1, 'win_fraction': 57 / 117,
            'wilson_95': (.39, .58), 'mirror_matches': 3,
            'matchups': [{'opponent': 'Invented Beta', 'wins': 57, 'losses': 59, 'ties': 1,
                'n': 117, 'win_fraction': 57 / 117, 'wilson_95': (.39, .58)}]}
    return {'status': 'OK', 'identity': {'status': 'IDENTIFIED', 'archetype_name': 'Invented Alpha',
            'evidence': 'pokemon_in_list'}, 'archetype': {'modes': {'BO1': data,
                'BO3': deepcopy(data) | {'n': 40, 'wins': 12, 'losses': 28, 'ties': 0, 'win_fraction': .3}},
                'excluded_all_archetypes': {'bye_or_automatic_loss': 2}},
            'window': {'since': '2026-10-18', 'until': '2026-11-14'},
            'source': 'Limitless', 'docs_url': 'https://docs.limitlesstcg.com/developer/tournaments',
            'last_success_at': '2026-11-14T12:00:00Z', 'refresh': {'automatic_due': False}, 'meta': {}}


def test_016_selector_prefix_and_explicit_ranking(ui, app):
    ui.navigation.setCurrentRow(2)
    rows = ranking_016()
    ui.loaded_decks(rows)
    wait_until(app, lambda: _settled(ui))
    assert ui.deck_picker.currentText().startswith('#1 · 48,7 % · ')
    assert ui.deck_picker.itemText(1).startswith('#2 · 42,0 % · ')
    assert all(ui.deck_picker.itemText(i).startswith('— · ') for i in (2, 3, 4))
    assert ui.deck_views.count() == 4 and ui.deck_views.tabText(3) == 'Classement'
    assert [ui.ranking_table.item(i, 0).text() for i in range(5)] == ['#1', '#2', '—', '—', '—']
    assert 'PUBLIC BO1' in ui.deck_picker.toolTip() and '117' in ui.deck_picker.accessibleDescription()


def test_016_stats_details_closed_and_short_legend(ui, app, monkeypatch):
    panel = ui.public_stats
    ui.navigation.setCurrentRow(2)
    ui.deck_views.setCurrentIndex(2)
    wait_until(app, lambda: _settled(ui))
    panel.set_view(public_view_016())
    QTest.qWait(300)
    assert hasattr(panel, 'details_toggle'), 'Long methodology must be behind a native disclosure'
    assert not panel.details.isVisible()
    assert 'n ≥' not in panel.legend.text()
    assert '48,7' in panel.value.text() and '117' in panel.sample.text()
    QTest.mouseClick(panel.details_toggle, Qt.MouseButton.LeftButton)
    assert panel.details.isVisible()
    assert 'miroirs exclus' in panel.summary.text() and 'Limitless' in panel.source.text()


def test_016_stats_kpi_unknown_and_mode_separation(ui, app):
    panel = ui.public_stats
    view = public_view_016()
    panel.set_view(view)
    assert hasattr(panel, 'value'), 'Public headline needs a distinct visual value'
    assert panel.value.text() == '48,7 %'
    panel.mode.setCurrentIndex(panel.mode.findData('BO3'))
    assert panel.value.text() == '30,0 %' and 'BO3' in panel.rate_title.text()
    view['archetype']['modes'] = {'BO3': view['archetype']['modes']['BO3'] | {'win_fraction': None, 'n': 7}}
    panel.set_view(view)
    assert panel.value.text() == '—' and 'BO3' in panel.rate_title.text()
    assert 'Données insuffisantes' in panel.availability.text() and '7' in panel.sample.text()



def test_016_ranking_mouse_keyboard_refresh_preserves_deck_and_readonly_selection(ui, app, monkeypatch):
    from copy import deepcopy
    from pokemind.desktop.insights import favorite_key
    rows = ranking_016()
    ui.navigation.setCurrentRow(2)
    ui.loaded_decks(rows)
    wait_until(app, lambda: _settled(ui))
    ui.deck_views.setCurrentIndex(3)
    QTest.qWait(300)
    writes = []
    save = ui.save_preferences
    monkeypatch.setattr(ui, 'save_preferences', lambda: writes.append(True))
    table = ui.ranking_table
    table.setFocus()
    QTest.keyClick(table, Qt.Key.Key_Down)
    wait_until(app, lambda: _settled(ui))
    assert ui.deck_picker.currentIndex() == 1 and not writes
    point = table.visualItemRect(table.item(4, 1)).center()
    QTest.mouseClick(table.viewport(), Qt.MouseButton.LeftButton, pos=point)
    wait_until(app, lambda: _settled(ui))
    assert ui.deck_picker.currentIndex() == 4 and not writes
    assert table.editTriggers() == table.EditTrigger.NoEditTriggers
    monkeypatch.setattr(ui, 'save_preferences', save)
    ui.deck_picker.setCurrentIndex(1)
    wait_until(app, lambda: _settled(ui))
    ui.favorite_button.click(); ui.main_button.click()
    key = favorite_key(rows[1])
    ui.compare_picker.setCurrentIndex(4)
    compared = favorite_key(rows[4])
    generation = ui.gallery.generation
    ui.gallery.verticalScrollBar().setValue(25)
    scroll = ui.gallery.verticalScrollBar().value()
    changed = deepcopy(rows)
    changed[1]['public_ranking']['fraction'] = .7
    changed = [changed[1], changed[0], *changed[2:]]  # worker's new descending order
    ui.loaded_decks(changed)
    assert ui.deck_picker.currentIndex() == 0 and ui.ranking_table.currentRow() == 0
    assert ui.deck_picker.currentText().startswith('#1 · 70,0 % · ♛ ')
    assert favorite_key(ui.deck_rows[ui.compare_picker.currentIndex()]) == compared
    assert key in ui.preferences['favorite_decks'] and ui.preferences['main_deck'] == key
    assert ui.gallery.generation == generation and ui.gallery.verticalScrollBar().value() == scroll
    changed[1]['public_ranking']['fraction'] = .7
    ui.loaded_decks(changed)
    assert [ui.ranking_table.item(i, 0).text() for i in (0, 1)] == ['#1', '#2']
    assert ui.deck_rows[0]['selector'] == changed[0]['selector']  # stable ties, no extra UI sort
    for row in changed: row['public_ranking']['fraction'] = None
    ui.loaded_decks(changed)
    assert all(ui.ranking_table.item(i, 0).text() == '—' for i in range(5))
    assert all('Données insuffisantes' in ui.ranking_table.item(i, 2).text() for i in range(5))
    ui.loaded_decks([])
    assert table.rowCount() == 0 and ui.deck_picker.count() == 0


@pytest.mark.parametrize('identity', ['AMBIGUOUS', 'UNIDENTIFIED'])
def test_016_stats_unidentified_error_and_details_copy_are_honest(ui, app, identity):
    from copy import deepcopy
    from pokemind.desktop.i18n import display
    from pokemind.desktop.insights import project_public_stats
    view = public_view_016()
    view.update(archetype=None, identity={'status': identity, 'candidates': ['Invented A', 'Invented B']},
                refresh={'last_outcome': {'status': 'ERROR'}, 'last_attempt_at': '2026-11-14T12:01:00Z'})
    before = deepcopy(view)
    panel = ui.public_stats
    panel.set_view(view)
    assert panel.value.text() == '—' and not panel.details_toggle.isChecked()
    assert 'échec' in panel.status.text() and 'instantané' in panel.status.text()
    assert 'non identifié' in panel.identity.text() and '0 %' not in panel.value.text()
    model = project_public_stats(view)
    assert panel.source.text() == display(model['source']) and view == before
    assert panel.source.textInteractionFlags() & Qt.TextInteractionFlag.TextSelectableByKeyboard
    panel.set_busy(False, 'Statistiques publiques indisponibles · INVENTED_QA_ERROR')
    panel.set_theme('light')
    assert 'INVENTED_QA_ERROR' in panel.status.text()
    panel.details_toggle.setChecked(True)
    panel.set_view(public_view_016())
    assert not panel.details_toggle.isChecked()  # deck change resets disclosure


@pytest.mark.parametrize('width,docked', [(1100, True), (1500, True), (1500, False)])
@pytest.mark.parametrize('theme', ['dark', 'light'])
@pytest.mark.parametrize('language', ['fr', 'en'])
def test_016_native_visual_ranking_and_statistics(ui, app, monkeypatch, width, docked, theme, language):
    import os
    from copy import deepcopy
    from PySide6.QtCore import QRect
    from PySide6.QtWidgets import QStyleOptionComboBox, QStyle
    from pokemind.desktop.i18n import display, set_language
    from pokemind.desktop.insights import favorite_key, project_public_stats
    ui.navigation.setCurrentRow(2)
    ui.resize(width, 970)
    ui.chat_dock.setVisible(docked)
    ui.theme.setCurrentIndex(ui.theme.findData(theme))
    rows = ranking_016()
    ui.loaded_decks(rows)
    wait_until(app, lambda: _settled(ui))
    def view_for(row, *args, **kwargs):
        view = deepcopy(public_view_016()) | {'deck_key': favorite_key(row)}
        if row['public_ranking']['fraction'] is None:
            view.update(status='ARCHETYPE_AMBIGUOUS', archetype=None,
                identity={'status': 'AMBIGUOUS', 'candidates': ['Invented A', 'Invented B']},
                refresh={'automatic_due': False, 'last_outcome': {'status': 'ERROR'}})
        return view
    monkeypatch.setattr(ui.services, 'deck_public_stats', view_for)
    ui.language.setCurrentIndex(ui.language.findData(language))
    try:
        QTest.qWait(300)
        picker = ui.deck_picker
        prefix = '#1 · ' + ('48,7 %' if language == 'fr' else '48.7 %')
        assert picker.currentText().startswith(prefix)
        option = QStyleOptionComboBox(); picker.initStyleOption(option)
        field = picker.style().subControlRect(QStyle.ComplexControl.CC_ComboBox, option,
            QStyle.SubControl.SC_ComboBoxEditField, picker)
        assert field.width() > picker.fontMetrics().horizontalAdvance(prefix) + 20
        scale = picker.devicePixelRatioF()
        crop = QRect(round(field.x()*scale), 0,
                     round(picker.fontMetrics().horizontalAdvance(prefix)*scale), round(picker.height()*scale))
        long = picker.grab().toImage().copy(crop)
        original = picker.currentText()
        picker.setItemText(0, prefix + ' · QA')
        app.processEvents()
        short = picker.grab().toImage().copy(crop)
        assert long == short, 'Real native closed selector must paint the entire leading rank/rate'
        picker.setItemText(0, original)
        output = Path(os.environ.get('POKEMIND_016_CAPTURE_DIR') or Path(__file__).resolve().parents[1] / 'build/qa-016')
        output.mkdir(parents=True, exist_ok=True)
        tag = f'{theme}-{language}-{width}-coach{int(docked)}-{scale:g}'
        assert ui.grab().save(str(output / ('selector-' + tag + '.png')))
        ui.activateWindow()
        ui.raise_()
        picker.setFocus()
        QTest.mouseClick(picker, Qt.MouseButton.LeftButton)
        wait_until(app, lambda: picker.view().isVisible())
        QTest.qWait(60)
        popup = picker.view(); assert popup.isVisible()
        rect = popup.visualRect(picker.model().index(0, 0))
        assert rect.width() < width and rect.left() >= 0
        item_option = QStyleOptionViewItem()
        item_option.initFrom(popup)
        item_option.rect = rect
        picker.itemDelegate().initStyleOption(item_option, picker.model().index(0, 0))
        text_rect = popup.style().subElementRect(QStyle.SubElement.SE_ItemViewItemText, item_option, popup)
        popup_crop = QRect(round(text_rect.left()*scale), round(rect.top()*scale),
            round(picker.fontMetrics().horizontalAdvance(prefix)*scale), round(rect.height()*scale))
        long_popup = popup.viewport().grab().toImage().copy(popup_crop)
        picker.setItemText(0, prefix + ' · QA'); app.processEvents()
        short_popup = popup.viewport().grab().toImage().copy(popup_crop)
        assert long_popup == short_popup, 'Real open popup must retain the same visible rank/rate prefix'
        picker.setItemText(0, original)
        assert popup.grab().save(str(output / ('popup-' + tag + '.png')))
        picker.hidePopup()
        ui.deck_views.setCurrentIndex(3); QTest.qWait(100)
        table = ui.ranking_table
        assert table.rowCount() == 5 and table.horizontalScrollBar().maximum() == 0, (
            table.width(), table.viewport().width(), [table.columnWidth(c) for c in range(4)],
            table.horizontalHeader().minimumSectionSize())
        for c in range(4):
            assert not table.isColumnHidden(c)
            assert table.columnViewportPosition(c) >= 0
            assert table.columnViewportPosition(c) + table.columnWidth(c) <= table.viewport().width()+1
        assert table.item(0, 0).text() == '#1' and '48' in table.item(0, 2).text()
        assert table.item(0, 2).text() == ('48,7 %' if language == 'fr' else '48.7 %')
        assert table.item(2, 2).text() == ('Données insuffisantes' if language == 'fr' else 'Insufficient data')
        assert ui.grab().save(str(output / ('ranking-' + tag + '.png')))
        ui.deck_views.setCurrentIndex(2)
        wait_until(app, lambda: _settled(ui))
        QTest.qWait(600)  # settle the existing chart animation before native capture
        panel = ui.public_stats
        assert panel.value.isVisible() and not panel.details.isVisible()
        assert panel.sample.isVisible() and panel.sample.width() >= 90
        assert panel.sample.geometry().left() > panel.value.geometry().right()
        assert panel.value.fontMetrics().height() > panel.rate_title.fontMetrics().height() * 1.5
        assert panel.value.geometry().bottom() < panel.period.geometry().top()
        assert panel.legend.geometry().top() > panel.tabs.geometry().bottom()
        assert ui.public_stats_scroll.horizontalScrollBar().maximum() == 0
        assert panel.matchups.rows == project_public_stats(panel.view, 'BO1')['matchup_rows']
        assert ui.grab().save(str(output / ('statistics-' + tag + '.png')))
        ui.public_stats_scroll.ensureWidgetVisible(panel.details_toggle); QTest.qWait(100)
        assert ui.grab().save(str(output / ('chart-' + tag + '.png')))
        # Native keyboard disclosure and actual copy, then scroll to long source text.
        panel.details_toggle.setFocus(); QTest.keyClick(panel.details_toggle, Qt.Key.Key_Space)
        assert panel.details.isVisible()
        QTest.qWait(100)
        ui.public_stats_scroll.ensureWidgetVisible(panel.source); QTest.qWait(100)
        assert ui.public_stats_scroll.viewport().rect().contains(
            panel.source.mapTo(ui.public_stats_scroll.viewport(), panel.source.rect().center()))
        panel.source.setFocus(); QTest.keyClick(panel.source, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        QTest.keyClick(panel.source, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
        assert QApplication.clipboard().text() == panel.source.text()
        assert ui.grab().save(str(output / ('details-' + tag + '.png')))
        panel.tabs.setCurrentIndex(1)
        assert ('placements' if language == 'fr' else 'placements') in panel.chart_title.text().lower()
        assert 'Victoires' not in panel.legend.text() and 'Wins' not in panel.legend.text()
        panel.tabs.setCurrentIndex(0)
        ui.deck_picker.setCurrentIndex(2)
        wait_until(app, lambda: _settled(ui) and panel.view.get('archetype') is None)
        ui.public_stats_scroll.verticalScrollBar().setValue(0); QTest.qWait(100)
        assert panel.value.text() == '—' and not panel.details_toggle.isChecked()
        assert ('échec' if language == 'fr' else 'failed') in panel.status.text()
        assert ui.grab().save(str(output / ('unknown-' + tag + '.png')))
    finally:
        if ui.deck_picker.view().isVisible(): ui.deck_picker.hidePopup()
        ui.language.setCurrentIndex(ui.language.findData('fr'))
        set_language('fr')
