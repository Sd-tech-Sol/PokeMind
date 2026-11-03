"""Headless Qt interaction against invented services/providers only."""
import os
import threading
import time
import gc

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
pytest.importorskip('PySide6')
from PySide6.QtCore import Qt, QUrl, QCoreApplication, QEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from shiboken6 import isValid

from pokemind.desktop import window
from pokemind.assistant.provider import ProviderAdapter


@pytest.fixture(scope='module')
def app(qt_application):
    yield qt_application


def wait_until(app, condition, timeout=5000):
    end = time.monotonic() + timeout/1000
    while not condition() and time.monotonic() < end:
        app.processEvents()
        QTest.qWait(10)
        # QTest's native wait can hold the GIL on Windows; let real Python
        # parser/SQLite workers run, as QApplication.exec does in production.
        time.sleep(.002)
    assert condition()


def dispose_window(widget, app):
    """Destroy native callbacks while Python/Qt are alive, not during final GC.

    processEvents alone does not deliver DeferredDelete without app.exec().
    Both private pools and their queued completions must finish before deletion.
    """
    widget.close()
    assert widget.pool.waitForDone(5000)
    assert widget.image_pool.waitForDone(5000)
    wait_until(app, lambda: not widget.jobs)
    widget.close()
    assert not widget.isVisible()
    assert not widget.watch_timer.isActive()
    assert not widget.chat_render_timer.isActive()
    assert not widget.activity.timer.isActive()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()
    assert not isValid(widget)
    gc.collect()


class Fake(ProviderAdapter):
    def health(self):
        return {'available': True, 'status': 'Invented provider'}
    def ask_stream(self, prompt, history, emit, tool=None):
        self.session = self.session or 'invented-thread'
        emit('Réponse inventée → ')
        emit('avec source PokeMind.')


@pytest.fixture
def ui(local_tmp, monkeypatch, app):
    def load(services, update=False, **kwargs):
        services.report = {'as_of':'2026-10-25','model_version':'battle-batch-v4',
            'coverage':{'valid':6},'outcomes':{'wins':2,'losses':4,'unknown':0},
            'groups':[{'archetype':'Invented Family','wins':2,'losses':4,'unknown':0,'n':6}],
            'matches':[{'match':'M0001','outcome':'losses','opponent':{'label':'Invented Family'},
                'evidence':[{'turn':3,'type':'knockout','text':'Créature inventée mise K.O.'}]}],
            'persistence':{'status':'BLOCKED_SCHEMA_NO_MIGRATION'},'recommendations':[]}
        services.learning = None
        return {'report':services.report,'learning':None}
    monkeypatch.setattr(window.Services,'load',load)
    monkeypatch.setattr(window.Services,'deck_options',lambda s:[])
    monkeypatch.setattr(window,'CodexAppServer',Fake)
    monkeypatch.setattr(window,'ClaudeCode',Fake)
    widget=window.MainWindow(local_tmp)
    widget.show()
    # Dashboard and deck/catalog jobs complete independently. Tests must not
    # inject a gallery while an older initial deck result is still queued.
    wait_until(app,lambda:widget.metrics[0].text()=='6' and not widget.jobs)
    yield widget
    dispose_window(widget, app)


def test_qt_navigable_dashboard_and_real_read_models(ui, app):
    assert ui.isVisible() and ui.stack.count()==7
    assert [m.text() for m in ui.metrics]==['6','2','4']
    assert ui.provider.currentData()=='codex'
    assert not ui.cloud_consent.isChecked()
    for index in range(6):
        ui.navigation.setCurrentRow(index)
        app.processEvents()
        assert ui.stack.currentIndex()==index
    ui.internal_link(QUrl('pokemind://page/1'))
    ui.matchups.selectRow(0)
    app.processEvents()
    assert ui.games.count()==1 and 'K.O.' in ui.battle_details.toPlainText()


def test_qt_filter_ask_and_empty_decks(ui, app):
    ui.matchup_filter.setText('absent')
    assert ui.matchups.rowCount()==0
    ui.matchup_filter.clear()
    ui.matchups.selectRow(0)
    ui.ask_matchup()
    assert 'Invented Family' in ui.chat_input.toPlainText()
    assert not ui.copy_deck.isEnabled()


def test_qt_cloud_preference_blocks_send_without_modal_or_network(ui, app):
    ui.chat_input.setPlainText('Question inventée')
    QTest.mouseClick(ui.send_button,Qt.MouseButton.LeftButton)
    assert ui.stack.currentIndex()==5
    assert not ui.chat_busy and ui.conversation['messages']==[]
    assert ui.chat_input.toPlainText()=='Question inventée'


def test_qt_chat_two_turns_and_history_resume(ui, app):
    ui.cloud_consent.setChecked(True)
    for message in ('Question inventée 1','Question inventée 2'):
        ui.chat_input.setPlainText(message)
        QTest.mouseClick(ui.send_button,Qt.MouseButton.LeftButton)
        wait_until(app,lambda:not ui.chat_busy)
    assert len(ui.conversation['messages'])==4
    assert 'Réponse inventée' in ui.transcript.toPlainText()
    identity=ui.conversation['id']
    assert ui.store.load(identity)['session']=='invented-thread'
    ui.new_conversation()
    index=ui.history_picker.findData(identity)
    assert index>0
    ui.resume_conversation(index)
    assert ui.conversation['id']==identity and len(ui.conversation['messages'])==4


def test_qt_delete_conversation_asks_first_then_erases_only_it(ui, app, monkeypatch):
    ui.cloud_consent.setChecked(True)
    identities = []
    for message in ('Question inventée à garder', 'Question inventée à effacer'):
        ui.new_conversation()
        ui.chat_input.setPlainText(message)
        QTest.mouseClick(ui.send_button, Qt.MouseButton.LeftButton)
        wait_until(app, lambda: not ui.chat_busy)
        identities.append(ui.conversation['id'])
    kept, erased = identities
    path = ui.store.path('conversation-' + erased + '.json')
    monkeypatch.setattr(window.QMessageBox, 'question', lambda *a: window.QMessageBox.StandardButton.No)
    QTest.mouseClick(ui.delete_button, Qt.MouseButton.LeftButton)
    assert path.exists() and ui.conversation['id'] == erased
    monkeypatch.setattr(window.QMessageBox, 'question', lambda *a: window.QMessageBox.StandardButton.Yes)
    QTest.mouseClick(ui.delete_button, Qt.MouseButton.LeftButton)
    assert not path.exists() and ui.conversation['id'] != erased and ui.conversation['messages'] == []
    assert ui.history_picker.findData(erased) == -1 and ui.history_picker.findData(kept) > 0
    assert ui.store.load(kept)['messages'] and ui.store.preferences()['current'] is None
    assert erased not in [row['id'] for row in ui.store.preferences()['conversations']]


def test_qt_delete_all_conversations_asks_once_then_erases_every_one(ui, app, monkeypatch):
    ui.cloud_consent.setChecked(True)
    identities = []
    for message in ('Première question inventée', 'Deuxième question inventée'):
        ui.new_conversation()
        ui.chat_input.setPlainText(message)
        QTest.mouseClick(ui.send_button, Qt.MouseButton.LeftButton)
        wait_until(app, lambda: not ui.chat_busy)
        identities.append(ui.conversation['id'])
    paths = [ui.store.path('conversation-' + identity + '.json') for identity in identities]
    count = len(ui.preferences['conversations'])
    asked = []
    def refuse(*a):
        asked.append(a[2])
        return window.QMessageBox.StandardButton.No
    monkeypatch.setattr(window.QMessageBox, 'question', refuse)
    QTest.mouseClick(ui.delete_all_button, Qt.MouseButton.LeftButton)
    assert all(p.exists() for p in paths) and count >= 2 and str(count) + ' discussion' in asked[0]
    monkeypatch.setattr(window.QMessageBox, 'question', lambda *a: window.QMessageBox.StandardButton.Yes)
    QTest.mouseClick(ui.delete_all_button, Qt.MouseButton.LeftButton)
    assert not any(p.exists() for p in paths)
    assert ui.conversation['messages'] == [] and ui.conversation['id'] not in identities
    assert all(ui.history_picker.findData(identity) == -1 for identity in identities)
    assert ui.store.preferences()['conversations'] == [] and ui.store.preferences()['current'] is None
    assert 'Toutes les discussions' in ui.provider_status.text()


def test_qt_chat_stop_is_responsive_and_keeps_partial(ui, app):
    class Slow(Fake):
        def ask_stream(self,prompt,history,emit,tool=None):
            self.stopped.clear()
            self.session='invented-thread'
            emit('Réponse partielle')
            self.stopped.wait(3)
    ui.adapter=Slow(ui.store.sandbox)
    ui.cloud_consent.setChecked(True)
    ui.chat_input.setPlainText('Question inventée')
    ui.send_chat()
    wait_until(app,lambda:'Réponse partielle' in ui.transcript.toPlainText())
    QTest.mouseClick(ui.stop_button,Qt.MouseButton.LeftButton)
    wait_until(app,lambda:not ui.chat_busy)
    assert 'interrompue' in ui.transcript.toPlainText()
    assert ui.store.load(ui.conversation['id'])['messages'][-1]['content']


def test_qt_settings_theme_and_provider_persist(ui, app):
    ui.theme.setCurrentIndex(1)
    ui.provider.setCurrentIndex(1)
    app.processEvents()
    assert ui.store.preferences()['theme']=='light'
    assert ui.store.preferences()['provider']=='claude'


def test_qt_motion_rapid_navigation_and_resize_restore_live_page(ui, app):
    for index in (1, 5, 2, 4, 0):
        ui.navigation.setCurrentRow(index)
        assert ui.stack.currentIndex() == index
        assert ui.stack.transition.isVisible()
        QTest.qWait(12)
        app.processEvents()
    wait_until(app, lambda: not ui.stack.transition.isVisible())
    assert ui.stack.transition.before.isNull() and ui.stack.transition.after.isNull()
    assert ui.metrics[0].text() == '6'
    ui.navigation.setCurrentRow(1)
    assert ui.stack.transition.isVisible()
    ui.resize(1200, 760)
    app.processEvents()
    assert not ui.stack.transition.isVisible()
    assert ui.stack.currentWidget().isVisible()
    ui.navigation.setCurrentRow(5)
    wait_until(app, lambda: not ui.stack.transition.isVisible())
    assert ui.stack.currentWidget().horizontalScrollBar().maximum() == 0


def test_qt_reduced_motion_cancels_effects_and_persists(ui, app):
    ui.navigation.setCurrentRow(1)
    assert ui.stack.transition.isVisible()
    ui.reduced_motion.setChecked(True)
    assert window.Store(ui.root).preferences()['reduced_motion'] is True
    assert not ui.stack.transition.isVisible()
    for index in range(6):
        ui.navigation.setCurrentRow(index)
        assert ui.stack.currentIndex() == index
        assert not ui.stack.transition.isVisible()
    assert ui.corpus_chart.reveal == 1.0
    assert ui.hero_emblem.progress == 1.0
    ui.reduced_motion.setChecked(False)
    ui.navigation.setCurrentRow(0)
    assert ui.stack.transition.isVisible()


def test_qt_button_effect_does_not_intercept_mouse_or_keyboard(ui, app):
    from PySide6.QtCore import QEvent
    button = ui.new_button
    clicks = []
    button.clicked.connect(lambda: clicks.append(True))
    QApplication.sendEvent(button, QEvent(QEvent.Type.Enter))
    app.processEvents()
    assert id(button) in ui.motion.layers
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    button.setFocus()
    QTest.keyClick(button, Qt.Key.Key_Space)
    assert len(clicks) == 2
    layer = ui.motion.layers[id(button)]
    wait_until(app, lambda: layer.ripple == 1.0)
    ui.reduced_motion.setChecked(True)
    assert layer.glow == 0.0 and layer.ripple == 1.0


def test_qt_close_during_motion_stops_all_effects(ui, app):
    ui.navigation.setCurrentRow(1)
    assert ui.stack.transition.isVisible()
    ui.close()
    app.processEvents()
    assert not ui.isVisible()
    assert not ui.stack.transition.isVisible()
    assert not ui.motion.enabled
    for animation in (ui.stack.transition.animation, ui.hero_emblem.animation, ui.corpus_chart.animation):
        assert animation.state() == animation.State.Stopped


def test_qt_hostile_chat_is_plain_text_and_no_embedded_html(ui, app):
    ui.conversation['messages']=[{'role':'assistant','content':'<img src="file:///invented/private"><script>evil</script>'}]
    ui.render_chat()
    assert '<img src=' in ui.transcript.toPlainText()
    assert '<script>' in ui.transcript.toPlainText()


def test_chat_citations_clickable_without_interpreting_html_or_credentials():
    value=window.message_html('<img src="file:///private"> https://example.invalid/card pokemind://card/invented-1?lang=fr https://user:secret@example.invalid/ https://[invalid')
    assert '<img ' not in value and '&lt;img ' in value
    assert '<a href="https://example.invalid/card">' in value
    assert '<a href="pokemind://card/invented-1?lang=fr">' in value
    assert '<a href="https://user:secret' not in value


def test_chat_markdown_sources_and_emphasis_do_not_load_untrusted_images():
    value=window.message_html('**7 parties** [rapport local](pokemind://page/1) ![image](https://example.invalid/card.png) <script>unsafe</script>')
    assert '<b>7 parties</b>' in value
    assert '<a href="pokemind://page/1">rapport local</a>' in value
    assert '<img' not in value and '<script>' not in value and '&lt;script&gt;' in value


def test_chat_tool_lines_become_one_friendly_line_and_markdown_blocks_stay_safe():
    from pokemind.desktop.locale_text import variant
    value = window.message_html('Début.\n\n[Outil · mcp__pokemind__pokemind_tool · cards]\n\n'
        '[Tool · mcp__pokemind__pokemind_tool · cards]\n[Outil · mcp__pokemind__pokemind_tool · save_deck]\n'
        '[Outil · Bash · git status]\n\n## Liste <b>inventée</b>\n- **4** Créature inventée\n'
        '| Carte | Qté |\n|---|---:|\n| <img src=x> | 2 |\n```\n<script>x</script>\n```')
    french, english = variant(value, 'fr'), variant(value, 'en')
    assert 'mcp__' not in french and '[Outil' not in french and '[Tool' not in french
    assert french.count('⚙') == 1 and 'cartes ×2' in french and 'Mes decks' in french and '<code>git status</code>' in french
    assert 'cards ×2' in english and 'saved to My decks' in english
    assert '<b>4</b>' in french and '•' in french and 'font-weight:700' in french
    assert '<table' in french and '<b>Carte</b>' in french and '---' not in french
    assert '<img' not in french and '<script>' not in french and '&lt;b&gt;inventée' in french
    assert '&lt;img src=x&gt;' in french and '&lt;script&gt;x&lt;/script&gt;' in french


def test_qt_refresh_calls_existing_service_on_worker(ui,app,monkeypatch):
    original=ui.services.load
    observed=[]
    def load(update=False, **kwargs):
        observed.append((update,threading.current_thread() is threading.main_thread()))
        return original(update, **kwargs)
    monkeypatch.setattr(ui.services,'load',load)
    QTest.mouseClick(ui.refresh_button,Qt.MouseButton.LeftButton)
    wait_until(app,lambda:not ui.data_busy)
    assert observed==[(True,False)]


def test_qt_export_is_exact60_and_never_overwrites_existing_file(ui,local_tmp,monkeypatch):
    exported='Energy: 60\n60 Invented Energy\n\nTotal Cards: 60\n'
    ui.loaded_decks([{'label':'Invented','selector':'invented','total':60,'export':exported,
        'kind':'Fixture','legality':'unknown','source':{}}])
    target=local_tmp/'invented-export.txt'
    monkeypatch.setattr(window.QFileDialog,'getSaveFileName',lambda *a:(str(target),'Text'))
    ui.export_deck()
    assert target.read_text(encoding='utf-8')==exported
    target.write_text('invented existing owner file',encoding='utf-8')
    ui.export_deck()
    assert target.read_text()=='invented existing owner file'


def test_history_write_failure_is_visible_without_private_error_text(ui,monkeypatch):
    def fail(*a):
        raise OSError('invented-private-detail')
    monkeypatch.setattr(ui.store,'save',fail)
    assert ui.remember() is False
    assert 'non enregistré' in ui.provider_status.text()
    assert 'invented-private-detail' not in ui.provider_status.text()


def test_qt_cancel_local_operation_preserves_previous_report(ui,app,monkeypatch):
    before=ui.services.report
    started=threading.Event()
    def slow(update=False, cancelled=None, progress=None):
        started.set()
        deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            if cancelled():
                raise ValueError('DESKTOP_CANCELLED')
            time.sleep(.01)
        return {'report':before}
    monkeypatch.setattr(ui.services,'load',slow)
    ui.reload(True)
    wait_until(app,started.is_set)
    QTest.mouseClick(ui.cancel_data_button,Qt.MouseButton.LeftButton)
    wait_until(app,lambda:not ui.data_busy)
    assert ui.services.report is before
    assert 'frontière sûre' in ui.statusBar().currentMessage()


def test_qt_loading_banner_is_visible_during_analysis_with_progress(ui,app,monkeypatch):
    assert ui.loading_banner.isHidden()
    started,release=threading.Event(),threading.Event()
    def slow(update=False, cancelled=None, progress=None):
        started.set()
        progress(3,7)
        release.wait(3)
        return {'report':ui.services.report}
    monkeypatch.setattr(ui.services,'load',slow)
    ui.reload(True)
    wait_until(app,lambda:started.is_set() and ui.loading_bar.maximum()==7)
    assert not ui.loading_banner.isHidden()
    assert 'Analyse de tes combats' in ui.loading_title.text()
    assert '3 / 7' in ui.loading_detail.text() and ui.loading_bar.value()==3
    assert ui.metrics[0].text()=='6'  # the previous numbers stay, the banner says they will update
    release.set()
    wait_until(app,lambda:not ui.data_busy)
    assert ui.loading_banner.isHidden()
    report,ui.services.report=ui.services.report,None
    ui.show_loading(False)  # first reading: no zero anywhere, the charts wait for real numbers
    assert ui.statistics.isHidden() and ui.metrics[0].text()=='…' and 'Chargement' in ui.loading_title.text()
    ui.hide_loading()
    assert not ui.statistics.isHidden() and ui.metrics[0].text()=='—'
    ui.services.report=report


def test_background_failure_is_journaled_and_copyable(ui, app):
    from pokemind import diagnostics
    diagnostics.reset_for_tests()
    path = diagnostics.setup(ui.root)
    try:
        codes = []
        def broken(events):
            raise KeyError('clé inventée')
        ui.submit(broken, lambda result: None, codes.append)
        wait_until(app, lambda: codes and not ui.jobs)
        assert codes == ['LOCAL_SERVICE_UNAVAILABLE']
        content = path.read_text(encoding='utf-8')
        assert 'Tâche de fond en échec · KeyError' in content and 'clé inventée' in content
        ui.navigation.setCurrentRow(5)
        QTest.mouseClick(ui.copy_diagnostic, Qt.MouseButton.LeftButton)
        copied = QApplication.clipboard().text()
        assert copied.startswith('PokeMind ') and 'KeyError' in copied and str(ui.root) not in copied
        assert diagnostics.LOG_NAME in ui.statusBar().currentMessage()
    finally:
        diagnostics.reset_for_tests()
