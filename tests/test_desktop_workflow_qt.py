"""Desktop regression journeys. Every combat/person/image here is invented."""
import json
import threading
from pathlib import Path

import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import Qt, QMimeData, QUrl, QTimer, QBuffer, QIODevice
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QStyleOptionViewItem

from test_desktop_qt import app, ui, wait_until, dispose_window, Fake
from test_desktop_ingestion import text
from pokemind.desktop import window, ingestion
from pokemind.assistant.sessions import Store


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
    class FalseClaims(Fake):
        def ask_stream(self, prompt, history, emit, tool=None):
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
    for content in (saved['content'], ui.transcript.toPlainText()):
        assert expected in content
        assert 'Pistes conditionnelles' in content and 'unverified' in content
        assert url in content and fact['retrieved_at'] in content and fact['version'] in content
        assert '1 faits ajoutés' in content
        assert '100% légale' not in content and "Rien n'a été enregistré" not in content
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
    assert saved['content']==public_research_message(receipt,question)
    for content in (saved['content'],ui.transcript.toPlainText()):
        assert all(part in content for part in expected)
        assert '100% légale' not in content and "Rien n'a été mémorisé" not in content
    assert len(calls)==1 and ui.stack.count()==7
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
        assert "Rien n'a été mémorisé" not in text
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
    ui.chat_delta("Rien n'a été mémorisé; 999 faits ajoutés, règles certaines.")
    ui.render_chat()
    assert '999' not in ui.transcript.toPlainText()
    ui.chat_done(None)
    saved = ui.store.load(ui.conversation['id'])['messages'][-1]
    assert saved == ui.conversation['messages'][-1]
    for text in (saved['content'], ui.transcript.toPlainText()):
        assert "Rien n'a été mémorisé" not in text and '999' not in text
        assert 'État : ' + status in text and 'commentaire du modèle est écarté' in text
        assert 'Validation sur la source : non attestée' in text
        assert 'Utilisation par le modèle : non attestée' in text
        assert receipt['sources'][0] in text
        if persisted is not True or type(added) is not int or status == 'CACHE_FRESH' and added:
            assert 'aucun compte d’écriture annoncé' in text and '2 faits ajoutés' not in text
        else:
            assert f'{added} faits ajoutés' in text
            if status in {'CACHE_FRESH','OFFLINE_STALE_OR_EMPTY','SOURCE_COOLDOWN'}:
                assert 'Aucune nouvelle écriture' in text
    assert saved['memory_receipt']['offline_fact_count'] == facts
    assert ui.services.last_research_receipt is None


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
    assert '2 faits ajoutés' in message['content'] and "Rien n'a été mémorisé" not in message['content']
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
        assert '2 faits ajoutés' in reopened.transcript.toPlainText()
        assert "Rien n'a été mémorisé" not in reopened.transcript.toPlainText()
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


def test_pasted_defeat_alone_makes_the_coach_rebuild_and_save_the_opponent_deck(ui,app,monkeypatch):
    # The owner pastes a lost game and wants the deck that beat them in « Mes decks », named.
    captured=[]
    export='Pokémon: 20\n20 Invented Alpha INV 1\nTrainer: 20\n20 Invented Beta INV 2\nEnergy: 20\n20 Basic Invented Energy INV 3'
    class Capture(Fake):
        def ask_stream(self,prompt,history,emit,tool=None):
            captured.append(prompt)
            captured.append(tool({'operation':'save_deck','query':'Deck adverse inventé','export_text':export}))
            before.append(len(refreshed))
            super().ask_stream(prompt,history,emit,tool)
    monkeypatch.setattr(window,'CodexAppServer',Capture)
    refreshed,before=[],[]
    monkeypatch.setattr(window.Services,'deck_options',lambda s:refreshed.append(1) or [])
    ui.cloud_consent.setChecked(True);ui.sharing.setCurrentIndex(1)
    ui.chat_input.setPlainText(text())
    QTest.keyClick(ui.chat_input,Qt.Key.Key_Return)
    wait_until(app,lambda:len(captured)==2 and not ui.chat_busy and not ui.ingest_busy)
    assert 'Quel deck m’a affronté' in captured[0] and '"selected_match"' in captured[0] and '"opponent_reconstruction"' in captured[0]
    assert 'InventedRival' not in captured[0] and 'Reference player:' not in captured[0]
    assert captured[1]['status']=='SAVED_DECK' and captured[1]['name']=='Deck adverse inventé'
    assert ui.services.my_decks()[0]['name']=='Deck adverse inventé' and ui.services.my_decks()[0]['export']==export
    assert 'Deck ajouté à Mes decks : Deck adverse inventé' in ui.statusBar().currentMessage()
    wait_until(app,lambda:len(refreshed)>before[0])  # Deck Lab reloads after the save (the fixture stubs the list)
    assert 'Statistiques actualisées' not in ui.transcript.toPlainText()


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
    assert streamed.count('POKEMIND') == 1 and 'Début inventé un deux trois' in streamed
    ui.render_chat()
    assert ui.transcript.toPlainText() == streamed
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


def test_logo_is_two_cards_with_a_brain_and_the_exe_icon_holds_every_size(app):
    import importlib.util, struct
    from pokemind.desktop.theme import logo_pixmap, logo_icon_sizes
    picture=logo_pixmap(256).toImage()
    for x,y in ((125,110),(165,100)):                                             # pink brain
        colour=picture.pixelColor(x,y)
        assert colour.red()>200 and 120<colour.green()<170 and colour.blue()>150
    window,front,back=picture.pixelColor(150,140),picture.pixelColor(160,195),picture.pixelColor(70,150)
    assert min(window.red(),window.green(),window.blue())>230                     # the card's picture window
    assert front.red()>150 and front.green()<60                                   # red front card
    assert back.blue()>150 and back.red()<100                                     # blue card behind
    assert picture.pixelColor(4,4).alpha()==0                                     # no square background
    spec=importlib.util.spec_from_file_location('make_icon',Path(__file__).resolve().parents[1]/'scripts/make_icon.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    data=module.ico_bytes(logo_icon_sizes())
    reserved,kind,count=struct.unpack_from('<HHH',data)
    assert (reserved,kind,count)==(0,1,len(logo_icon_sizes()))
    for index in range(count):
        side,_,_,_,_,_,length,offset=struct.unpack_from('<BBBBHHII',data,6+16*index)
        assert data[offset:offset+8]==b'\x89PNG\r\n\x1a\n' and offset+length<=len(data)


def test_settings_are_short_rows_in_categories_with_details_on_demand(ui,app):
    ui.show();ui.navigation.setCurrentRow(5)
    wait_until(app,lambda:not ui.stack.transition.isVisible())
    assert list(ui.settings_tabs)==['general','coach','battles','data','about']
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
    reds=sum(1 for x in range(rect.left(),rect.right(),3)
             if (lambda c:c.red()>180 and c.green()<90)(picture.pixelColor(x,rect.center().y())))
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
    def download(target, *, progress, cancelled):
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
