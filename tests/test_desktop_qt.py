"""Headless Qt interaction against invented services/providers only."""
import os
import threading
import time
import gc

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
pytest.importorskip('PySide6')
from PySide6.QtCore import Qt, QUrl, QCoreApplication, QEvent, QSize
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from shiboken6 import isValid

from pokemind.desktop import window
from pokemind.assistant.provider import ProviderAdapter
REAL_DECK_OPTIONS = window.Services.deck_options


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
    # These tests start from the opt-out (no cloud, public knowledge only); the defaults are tested on their own.
    window.Store(local_tmp).write('preferences.json',{'cloud_consent':False,'sharing':'public'})
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


def test_qt_reset_warns_then_closes_and_starts_again_for_a_first_launch(ui, app, monkeypatch):
    from pokemind import data_reset
    relaunched, warnings = [], []
    monkeypatch.setattr(ui, 'relaunch', lambda: relaunched.append(True))
    monkeypatch.setattr(ui, 'reset_choice', lambda: (False, [], True))        # Annuler
    QTest.mouseClick(ui.reset_button, Qt.MouseButton.LeftButton)
    assert data_reset.pending(ui.root) is None and ui.isVisible()
    def refuse(*a):
        warnings.append(a[1])
        return window.QMessageBox.StandardButton.No
    monkeypatch.setattr(window.QMessageBox, 'warning', refuse)
    monkeypatch.setattr(ui, 'reset_choice', lambda: (True, ['games', 'chats'], False))  # no copy: asked again
    QTest.mouseClick(ui.reset_button, Qt.MouseButton.LeftButton)
    assert warnings == ['Effacer sans copie?'] and data_reset.pending(ui.root) is None and ui.isVisible()
    preferences = ui.store.path('preferences.json')
    preferences.unlink(missing_ok=True)
    monkeypatch.setattr(ui, 'reset_choice', lambda: (True, ['chats', 'games'], True))
    QTest.mouseClick(ui.reset_button, Qt.MouseButton.LeftButton)
    wait_until(app, lambda: not ui.isVisible())
    request = data_reset.pending(ui.root)
    assert request['keep_copy'] is True and request['pid'] == os.getpid() and relaunched == [True]
    assert request['categories'] == ['games', 'chats']
    assert not preferences.exists()  # closing for a reset writes no preference back
    ui.close()
    assert relaunched == [True]


def test_qt_reset_during_an_analysis_stops_it_then_closes_instead_of_doing_nothing(ui, app, monkeypatch):
    from pokemind import data_reset
    relaunched, reloads = [], []
    monkeypatch.setattr(ui, 'relaunch', lambda: relaunched.append(True))
    monkeypatch.setattr(ui, 'reset_choice', lambda: (True, ['games'], True))
    ui.data_busy = True  # the analysis of an import, about 30 s on the owner's PC (2026-11-05)
    QTest.mouseClick(ui.reset_button, Qt.MouseButton.LeftButton)
    assert data_reset.pending(ui.root)['categories'] == ['games'] and ui.data_cancel.is_set()
    assert 'arrêt de l’opération en cours' in ui.statusBar().currentMessage() and not ui.reset_button.isEnabled()
    monkeypatch.setattr(ui.services, 'load', lambda *a, **k: reloads.append(True))
    ui.data_busy = False
    ui.reload(True)  # nothing new starts once the reset is asked
    wait_until(app, lambda: not ui.isVisible())
    assert relaunched == [True] and reloads == []


def test_qt_archive_button_saves_a_verified_zip_where_the_owner_chose(ui, app, monkeypatch, tmp_path):
    import zipfile
    from pathlib import Path
    log = Path(ui.root) / 'data/local/battle_logs/partie-inventee.log'
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text('Tour 1 inventé', encoding='utf-8')
    asked, notices = [], []

    def save(parent, caption, directory, filter, native=False):
        asked.append((Path(directory).name, native))
        return str(tmp_path / 'Bureau' / 'mes-donnees.zip'), ''
    monkeypatch.setattr(window.QFileDialog, 'getSaveFileName', save)
    monkeypatch.setattr(ui, 'archive_notice', notices.append)
    QTest.mouseClick(ui.archive_button, Qt.MouseButton.LeftButton)
    wait_until(app, lambda: bool(notices), 15000)
    assert asked[0][1] is True and asked[0][0].startswith('PokeMind-') and asked[0][0].endswith('.zip')
    with zipfile.ZipFile(tmp_path / 'Bureau' / 'mes-donnees.zip') as archive:
        assert 'data/local/battle_logs/partie-inventee.log' in archive.namelist()
    assert notices[0]['status'] == 'ARCHIVED' and ui.archive_button.isEnabled() and ui.restore_button.isEnabled()
    assert 'Archive vérifiée' in ui.statusBar().currentMessage() and not ui.archiving
    infos = []
    monkeypatch.setattr(window.QMessageBox, 'information', lambda *a, **k: infos.append(str(a[2])))
    monkeypatch.setattr(window.QFileDialog, 'getSaveFileName', lambda *a, **k: pytest.fail('no dialog while busy'))
    ui.data_busy = True  # an analysis is writing: the zip would be incomplete
    QTest.mouseClick(ui.archive_button, Qt.MouseButton.LeftButton)
    assert infos and 'en cours' in infos[0]
    ui.data_busy = False


def test_qt_restore_button_asks_then_closes_and_the_next_launch_restores(ui, app, monkeypatch, tmp_path):
    from pathlib import Path
    from pokemind import data_archive
    source = tmp_path / 'ancien'
    (source / 'data/local/battle_logs').mkdir(parents=True)
    (source / 'data/local/battle_logs/ancienne.log').write_text('Partie inventée', encoding='utf-8')
    saved = data_archive.archive(source, target=tmp_path / 'cle' / 'archive.zip', parts=('data/local',), app=True)
    relaunched, questions = [], []
    monkeypatch.setattr(ui, 'relaunch', lambda: relaunched.append(True))
    monkeypatch.setattr(window.QFileDialog, 'getOpenFileName',
                        lambda parent, caption, directory, filter, native=False: (saved['zip'], '') if native else None)

    def refuse(parent, title, text, *rest):
        questions.append(str(text))
        return window.QMessageBox.StandardButton.No
    monkeypatch.setattr(window.QMessageBox, 'question', refuse)
    QTest.mouseClick(ui.restore_button, Qt.MouseButton.LeftButton)
    assert data_archive.pending_restore(ui.root) is None and ui.isVisible()
    assert str(Path(saved['zip']).parent) in questions[0]  # where the current data will be archived
    monkeypatch.setattr(window.QMessageBox, 'question', lambda *a, **k: window.QMessageBox.StandardButton.Yes)
    QTest.mouseClick(ui.restore_button, Qt.MouseButton.LeftButton)
    wait_until(app, lambda: not ui.isVisible())
    request = data_archive.pending_restore(ui.root)
    assert request['zip'] == saved['zip'] and request['parts'] == ['data/local'] and request['pid'] == os.getpid()
    assert relaunched == [True] and not ui.archive_button.isEnabled()


def test_qt_season_picker_shows_the_current_season_then_every_season(ui, app, monkeypatch):
    from pokemind import seasons
    from test_seasons import corpus
    monkeypatch.setattr(seasons, 'periods', lambda root, today=None: [
        {'key': 'before', 'name': 'Avant le 2026-11-05', 'start': None, 'end': '2026-11-05'},
        {'key': '2026-11-05', 'name': 'Delta Reign', 'start': '2026-11-05', 'end': None}])
    report = corpus(ui.root)
    report['recommendations'] = []
    ui.services.set_full_report(report)
    ui.loaded({'report': report, 'learning': None})
    wait_until(app, lambda: not ui.jobs)
    picker = ui.season_pickers[0]
    texts = [picker.itemText(i) for i in range(picker.count())]
    assert texts == ['Saison actuelle · Delta Reign (2026-11-05 →) · n=3', 'Avant le 2026-11-05 · n=2',
                     'Cumul · toutes les saisons · n=6']
    assert [m.text() for m in ui.metrics] == ['3', '1', '1'] and ui.battle_tiles['games'].text() == '2'
    picker.activated.emit(2)
    assert [m.text() for m in ui.metrics] == ['6', '3', '2'] and ui.battle_tiles['games'].text() == '5'
    assert ui.preferences['season_view'] == 'all' and all(p.currentData() == 'all' for p in ui.season_pickers)
    assert ui.store.preferences()['season_view'] == 'all'  # kept for the next launch
    ui.season_pickers[1].activated.emit(1)
    assert [m.text() for m in ui.metrics] == ['2', '1', '1'] and ui.season_pickers[0].currentData() == 'before'
    assert report['coverage']['valid'] == 6  # every game stays in the full report


def test_qt_new_season_starts_today_and_becomes_the_current_season(ui, app, monkeypatch):
    from datetime import date
    from pokemind import seasons
    monkeypatch.setattr(window.W.QInputDialog, 'getText', lambda *a, **k: ('Saison inventée', True))
    QTest.mouseClick(ui.new_season_button, Qt.MouseButton.LeftButton)
    today = date.today().isoformat()
    assert ui.season_pickers[0].itemText(0) == 'Saison actuelle · Saison inventée (' + today + ' →)'
    assert seasons.owner_starts(ui.root) == [{'start': today, 'name': 'Saison inventée'}]
    monkeypatch.setattr(window.W.QInputDialog, 'getText', lambda *a, **k: ('', False))
    QTest.mouseClick(ui.new_season_button, Qt.MouseButton.LeftButton)
    assert seasons.owner_starts(ui.root) == [{'start': today, 'name': 'Saison inventée'}]  # Annuler changes nothing


def test_qt_reset_window_starts_with_nothing_ticked_and_everything_ticks_all(app):
    from pokemind.data_reset import CATEGORIES
    from pokemind.desktop.reset_dialog import ResetDialog
    dialog = ResetDialog()
    try:
        assert dialog.choices() == [] and not dialog.confirm.isEnabled() and dialog.keep.isChecked()
        assert dialog.cancel.isDefault() and not dialog.everything.isChecked()
        dialog.boxes['decks'].setChecked(True)
        assert dialog.choices() == ['decks'] and dialog.confirm.isEnabled() and not dialog.everything.isChecked()
        dialog.everything.click()
        assert dialog.choices() == list(CATEGORIES) and dialog.everything.isChecked()
        dialog.boxes['technical'].setChecked(False)
        assert not dialog.everything.isChecked() and len(dialog.choices()) == len(CATEGORIES) - 1
        dialog.boxes['technical'].setChecked(True)
        assert dialog.everything.isChecked()
        dialog.everything.click()
        assert dialog.choices() == [] and not dialog.confirm.isEnabled()
    finally:
        dialog.deleteLater()


def test_qt_an_import_ending_after_its_discussion_was_emptied_does_not_crash(ui, app, monkeypatch):
    ui.chat_controls(True)
    assert not ui.delete_button.isEnabled() and not ui.delete_all_button.isEnabled()
    ui.chat_controls(False)
    ui.ingest_busy = True
    monkeypatch.setattr(window.QMessageBox, 'question', lambda *a, **k: pytest.fail('no deletion during an import'))
    ui.delete_conversation()
    ui.delete_all_conversations()
    ui.conversation = ui.store.new(ui.provider.currentData())  # emptied while the import ran (diagnostic 2026-11-03)
    ui._before_matches = set()
    ui.ingest_phase('Validation du journal local')
    ui.ingest_done([{'status': 'REFUSED', 'reasons': []}])
    messages = ui.conversation['messages']
    assert [m['role'] for m in messages] == ['assistant']
    assert 'Validation du journal local' in messages[0]['content'] and 'Importation refusée' in messages[0]['content']
    ui.ingest_failed('BATCH_CANCELLED')
    assert 'Traitement interrompu' in ui.conversation['messages'][-1]['content']


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


def test_qt_coach_sharing_choice_reads_in_full_in_both_languages(ui, app):
    """0.9.5 reception: « Ce que le coach reçoit » showed a cut choice beside a tall, thin explanation."""
    ui.navigation.setCurrentRow(5)
    wait_until(app, lambda: not ui.stack.transition.isVisible())
    for language in (1, 0):  # English, then back to French
        ui.language.setCurrentIndex(language)
        app.processEvents()
        metrics = ui.sharing.fontMetrics()
        widest = max(metrics.horizontalAdvance(ui.sharing.itemText(i)) for i in range(ui.sharing.count()))
        expected = min(widest + 60, ui.sharing.maximumWidth())  # offscreen without fonts draws wider boxes
        assert ui.sharing.minimumWidth() >= expected and ui.sharing.width() >= expected
        assert ui.sharing.view().minimumWidth() >= widest + 40
        hint = next(label for label in ui.sharing.parentWidget().findChildren(window.QLabel) if label.objectName() == 'settingHint')
        assert ui.sharing.geometry().top() >= hint.geometry().bottom()  # under the explanation, not squeezing it
    assert ui.store.preferences()['language'] == 'fr'


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


def offers(version='9.9.9'):
    from pokemind import app_update
    return {'app': {'status': 'AVAILABLE', 'version': version, 'page': app_update.PAGE + '/tag/v' + version,
                    'installer': {'name': 'PokeMind-Setup-%s.exe' % version, 'size': 1, 'url': app_update.DOWNLOADS},
                    'checksum': app_update.DOWNLOADS},
            'cards': {'status': 'AVAILABLE', 'commit': 'c' * 40, 'installed': {'printings': 100},
                      'new_sets': [{'id': 'dlt', 'name': 'Delta Reign', 'cards': 33}], 'grown_sets': [], 'notable': True}}


def test_qt_update_banner_offers_cards_and_a_new_version_and_one_click_does_both(ui, app, monkeypatch):
    from pokemind import app_update, catalog_update
    monkeypatch.setattr(app_update, 'save_check', lambda *a, **k: None)
    ui.updates_checked(offers())
    assert ui.update_banner.isVisibleTo(ui) and '9.9.9' in ui.update_detail.text()
    assert 'Delta Reign' in ui.update_detail.text() and 'Delta Reign' in ui.cards_update_status.text()
    assert ui.cards_update_button.isEnabled() and ui.app_update_button.isEnabled()
    assert ui.app_update_button.text() == 'Voir la nouvelle version'  # not the installed copy
    opened, updated = [], []
    monkeypatch.setattr(window, 'QDesktopServices', type('Desktop', (), {
        'openUrl': staticmethod(lambda url: opened.append(url.toString()))}))
    monkeypatch.setattr(catalog_update, 'update', lambda root, **k: updated.append(root) or {
        'status': 'UPDATED', 'printings': 133, 'commit': 'c' * 40})
    QTest.mouseClick(ui.update_now, Qt.MouseButton.LeftButton)
    wait_until(app, lambda: bool(opened), 10000)
    assert updated == [ui.root] and opened == [app_update.PAGE + '/tag/v9.9.9']  # cards first, then the release
    assert '133' in ui.cards_update_status.text() and not ui.cards_update_button.isEnabled() and not ui.catalog_busy
    QTest.mouseClick(ui.update_later, Qt.MouseButton.LeftButton)
    assert not ui.update_banner.isVisibleTo(ui)
    ui.updates_checked(offers(), saved=False)
    assert not ui.update_banner.isVisibleTo(ui)  # « Plus tard » holds until the next launch


def test_qt_the_installed_copy_downloads_checks_installs_and_closes(ui, app, monkeypatch, tmp_path):
    from pokemind import app_update
    setup = tmp_path / 'PokeMind-Setup-9.9.9.exe'
    setup.write_bytes(b'invented')
    started, questions = [], []
    monkeypatch.setattr(app_update, 'installed_copy', lambda *a, **k: True)
    monkeypatch.setattr(app_update, 'download', lambda release, **k: setup)
    monkeypatch.setattr(app_update, 'start_installer', started.append)
    monkeypatch.setattr(window.QMessageBox, 'question',
                        lambda *a, **k: questions.append(str(a[2])) or window.QMessageBox.StandardButton.Yes)
    ui.update_info = {'app': offers()['app'], 'cards': {'status': 'CURRENT'}}
    ui.show_update_state()
    assert ui.app_update_button.text() == 'Mettre à jour'
    QTest.mouseClick(ui.app_update_button, Qt.MouseButton.LeftButton)
    wait_until(app, lambda: not ui.isVisible(), 10000)
    assert started == [setup] and 'se rouvrir' in questions[0]


def test_qt_check_now_asks_once_then_the_automatic_check_reuses_the_answer(ui, app, monkeypatch):
    from pokemind import app_update, catalog_update
    monkeypatch.setattr(app_update, 'check', lambda *a, **k: {'status': 'CURRENT', 'version': '0.9.2'})
    monkeypatch.setattr(catalog_update, 'check', lambda root, **k: {'status': 'MISSING'})
    QTest.mouseClick(ui.update_check_button, Qt.MouseButton.LeftButton)
    wait_until(app, lambda: 'Dernière vérification' in ui.update_checked.text(), 10000)
    assert not ui.update_banner.isVisibleTo(ui) and 'à jour' in ui.app_update_status.text()
    assert app_update.last_check(ui.root)['app']['status'] == 'CURRENT' and 'Pas encore' in ui.cards_update_status.text()
    monkeypatch.setattr(app_update, 'check', lambda *a, **k: pytest.fail('no second request within 12 hours'))
    ui.check_updates()
    assert not ui.update_busy
    ui.update_auto.setChecked(False)
    assert ui.preferences['update_check'] is False
    monkeypatch.setattr(app_update, 'due', lambda root: pytest.fail('the check is turned off'))
    ui.check_updates()


def test_qt_theme_switch_redraws_the_drawn_icons_and_the_chat(ui, app):
    from PySide6.QtGui import QIcon
    from pokemind.desktop.theme import colors

    def shows(icon, color, mode=QIcon.Mode.Normal, state=QIcon.State.Off):
        image, target = icon.pixmap(QSize(32, 32), mode, state).toImage(), QColor(color)
        return any(QColor.fromRgba(image.pixel(x, y)).alpha() > 200 and
                   sum(abs(a - b) for a, b in zip(QColor.fromRgba(image.pixel(x, y)).getRgb()[:3], target.getRgb()[:3])) < 40
                   for x in range(image.width()) for y in range(image.height()))
    for index, name in ((1, 'light'), (0, 'dark')):
        ui.theme.setCurrentIndex(index)
        app.processEvents()
        c = colors(name)
        assert ui.preferences['theme'] == name and ui.styleSheet() == (window.LIGHT if name == 'light' else window.DARK)
        menu = ui.navigation.item(1).icon()
        assert shows(menu, c['accent']) and shows(menu, c['nav_icon_selected'], QIcon.Mode.Selected)
        assert shows(ui.settings_tabs['general'].icon(), c['nav_icon_selected'], state=QIcon.State.On)
        bubble, _ = ui.chat_bubble({'role': 'user', 'content': 'Question inventée'}, c)
        assert c['primary'] not in bubble and 'bgcolor=' not in bubble and '#a9233c' not in bubble


@pytest.fixture
def premium_gallery(ui, app, monkeypatch):
    """Twenty invented entries, exactly sixty cards; an image with four coloured corners."""
    from PySide6.QtCore import QBuffer, QIODevice
    from PySide6.QtGui import QImage, QPainter
    image = QImage(300, 420, QImage.Format.Format_RGB32)
    image.fill(QColor('#123456'))
    painter = QPainter(image)
    for x, y, color in ((0, 0, '#ff0000'), (260, 0, '#00ff00'),
                        (0, 380, '#ff00ff'), (260, 380, '#ffff00')):
        painter.fillRect(x, y, 40, 40, QColor(color))
    painter.end()
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, 'PNG')
    raw = bytes(buffer.data())
    cards = [dict(name='Synthetic creature with a long readable name ' + str(i), quantity=3,
                  category=category, printing='Synthetic printing reference ' + str(i),
                  identity='synthetic-' + str(i) if i < 19 else None)
             for i, category in enumerate(['pokemon'] * 10 + ['trainer'] * 6 + ['energy'] * 4)]
    lines = []
    for category, title in (('pokemon', 'Pokémon'), ('trainer', 'Trainer'), ('energy', 'Energy')):
        group = [(i, c) for i, c in enumerate(cards) if c['category'] == category]
        lines.append(f'{title}: {sum(c["quantity"] for _, c in group)}')
        lines.extend(f"3 {c['name']} SYN {i}" for i, c in group)
    export = '\n'.join(lines)
    monkeypatch.setattr(ui.services, 'gallery_cards', lambda value: cards)
    monkeypatch.setattr(ui.images, 'fetch', lambda *args: {
        'data': raw, 'source_url': 'https://example.invalid/synthetic.png'})
    ui.navigation.setCurrentRow(2)
    ui.deck_views.setCurrentIndex(0)
    ui.loaded_decks([dict(label='Synthetic deck · 20 references / 60 cards', selector='synthetic',
                         total=60, export=export, kind='Synthetic QA', legality='unknown', source={})])
    wait_until(app, lambda: not ui.jobs and len(ui.gallery.tiles) == 20 and
               ui.gallery.isVisible() and not ui.stack.transition.isVisible())
    assert all(not tile.picture.isNull() for tile in ui.gallery.tiles[:-1])
    return ui.gallery


def test_qt_premium_gallery_hover_keeps_grid_and_all_four_image_corners(ui, app, premium_gallery):
    gallery = premium_gallery
    tile = gallery.tiles[1]
    app.processEvents()
    geometry = [other.geometry() for other in gallery.tiles]
    art_geometry, picture = tile.art.geometry(), tile.picture.cacheKey()
    QApplication.sendEvent(tile.art, QEvent(QEvent.Type.Enter))
    assert tile.art.animation.state() == tile.art.animation.State.Running
    tile.art.animation.setCurrentTime(110)
    assert 0 < tile.art.hover < 1
    tile.art.animation.setCurrentTime(220)
    assert tile.art.hover == 1
    app.processEvents()
    assert [other.geometry() for other in gallery.tiles] == geometry
    assert tile.art.geometry() == art_geometry and tile.picture.cacheKey() == picture
    # Native pixel rendering, including the transformed image's extreme corners.
    image = tile.art.grab().toImage()
    visible = {image.pixelColor(x, y).name() for y in range(image.height()) for x in range(image.width())}
    assert {'#ff0000', '#00ff00', '#ff00ff', '#ffff00'} <= visible
    assert id(tile) not in ui.motion.layers and id(tile.art) not in ui.motion.layers
    QApplication.sendEvent(tile.art, QEvent(QEvent.Type.Leave))
    wait_until(app, lambda: tile.art.hover == 0 and tile.art.animation.state() == tile.art.animation.State.Stopped)


def test_qt_premium_gallery_keyboard_selection_is_distinct_from_hover_and_opens_zoom(ui, app, premium_gallery):
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QDialog
    gallery = premium_gallery
    first, second = gallery.tiles[:2]
    first.art.setFocus()
    app.processEvents()
    assert gallery.selected_tile is first and first.property('selected')
    QApplication.sendEvent(second.art, QEvent(QEvent.Type.Enter))
    assert gallery.selected_tile is first and not second.property('selected')
    QTest.keyClick(first.art, Qt.Key.Key_Tab)
    app.processEvents()
    assert second.art.hasFocus() and gallery.selected_tile is second and not first.property('selected')
    dialogs = []
    def close_zoom():
        from PySide6.QtWidgets import QLabel
        dialog = QApplication.activeModalWidget()
        dialogs.append(isinstance(dialog, QDialog) and dialog.windowTitle() == second.card['name'] and
                       any(second.provenance in label.text() for label in dialog.findChildren(QLabel)))
        if dialog:
            if output := os.environ.get('POKEMIND_GALLERY_QA_DIR'):
                dialog.grab().save(output + '/zoom.png')
            dialog.accept()
    for key in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
        QTimer.singleShot(50, close_zoom)
        QTest.keyClick(second.art, key)
    assert dialogs == [True] * 3 and gallery.selected_tile is second


def test_qt_premium_gallery_reduced_motion_hide_and_close_stop_every_card(ui, app, premium_gallery):
    gallery = premium_gallery
    tile = gallery.tiles[0]
    tile.art.animate(1)
    ui.reduced_motion.setChecked(True)
    assert not gallery.motion_enabled
    assert all(not t.art.motion_enabled and t.art.hover == 0 and
               t.art.animation.state() == t.art.animation.State.Stopped for t in gallery.tiles)
    QApplication.sendEvent(tile.art, QEvent(QEvent.Type.Enter))
    assert tile.art.hover == 0 and tile.art.animation.state() == tile.art.animation.State.Stopped
    # Newly populated cards inherit the setting too.
    gallery.populate([t.card for t in gallery.tiles])
    tile = gallery.tiles[0]
    assert not tile.art.motion_enabled
    ui.reduced_motion.setChecked(False)
    app.processEvents()
    tile.art.animate(1)
    assert tile.art.animation.state() == tile.art.animation.State.Running
    ui.deck_views.setCurrentIndex(1)
    app.processEvents()
    assert tile.art.hover == 0 and tile.art.animation.state() == tile.art.animation.State.Stopped
    tile.art.animate(1)  # A queued enter cannot start an animation on a hidden page.
    assert tile.art.animation.state() == tile.art.animation.State.Stopped
    ui.deck_views.setCurrentIndex(0)
    tile.art.animate(1)
    ui.close()
    app.processEvents()
    assert all(t.art.animation.state() == t.art.animation.State.Stopped for t in gallery.tiles)


@pytest.mark.parametrize('width,theme,language,font_size', [
    (1100, 'dark', 'fr', 14), (1500, 'light', 'en', 14),
    (1100, 'light', 'en', 18), (1500, 'dark', 'fr', 18),
    (1500, 'dark', 'fr', 14), (1100, 'light', 'en', 14),
    (1500, 'light', 'en', 18), (1100, 'dark', 'fr', 18)])
def test_qt_premium_gallery_layout_languages_themes_and_large_font(ui, app, premium_gallery,
                                                                 width, theme, language, font_size):
    from PySide6.QtWidgets import QLabel
    gallery = premium_gallery
    ui.theme.setCurrentIndex(1 if theme == 'light' else 0)
    ui.language.setCurrentIndex(ui.language.findData(language))
    if font_size == 18:
        ui.setStyleSheet(ui.styleSheet() + '\nQScrollArea#deckGallery QLabel {font-size:18px;}')
    ui.resize(width, 970 if width == 1500 else 900)
    app.processEvents()
    if not os.environ.get('POKEMIND_GALLERY_QA_BASELINE'):
        # The offscreen shell has different dock/font metrics. Check actual rows
        # in every backend; the exact full-window 3/2 contract is native Windows.
        actual_columns = len({tile.x() for tile in gallery.grids[0][1]})
        assert actual_columns == gallery._columns and 1 <= actual_columns <= 3
        if app.platformName() == 'windows':
            assert actual_columns == (3 if width == 1500 else 2), gallery.viewport().width()
    if output := os.environ.get('POKEMIND_GALLERY_QA_DIR'):
        import json
        from pathlib import Path
        ui.resize(width, 970 if width == 1500 else 900)
        app.processEvents()
        name = f'gallery-{width}-{theme}-{language}-{font_size}'
        folder = Path(output)
        gallery.select_tile(gallery.tiles[0])
        ui.grab().save(str(folder / (name + '.png')))
        tile = gallery.tiles[0]
        bounds = tile.art.rect().adjusted(*((12, 14, -12, -10)
            if os.environ.get('POKEMIND_GALLERY_QA_BASELINE') else (7, 10, -7, -6)))
        art = tile.picture.size().scaled(bounds.size(), Qt.AspectRatioMode.KeepAspectRatio)
        (folder / (name + '.json')).write_text(json.dumps({
            'window': [ui.width(), ui.height()], 'dpr': ui.devicePixelRatioF(),
            'viewport': [gallery.viewport().width(), gallery.viewport().height()],
            'columns': gallery._columns, 'tile': [tile.width(), tile.height()],
            'art': [art.width(), art.height()],
            'horizontal_scroll': gallery.horizontalScrollBar().maximum(),
            'vertical_scroll': gallery.verticalScrollBar().maximum(),
        }, indent=2), encoding='utf-8')
        if (width, theme, language, font_size) == (1500, 'dark', 'fr', 14) and not os.environ.get('POKEMIND_GALLERY_QA_BASELINE'):
            frames = folder / 'frames'
            frames.mkdir(exist_ok=True)
            art = gallery.tiles[1].art
            for frame in range(24):
                if frame in (0, 10):
                    QApplication.sendEvent(art, QEvent(QEvent.Type.Enter if frame == 0 else QEvent.Type.Leave))
                if frame < 20:
                    art.animation.setCurrentTime(min(220, (frame % 10) * 50))
                if frame == 20:
                    gallery.select_tile(gallery.tiles[1])
                app.processEvents()
                ui.grab().save(str(frames / f'{frame:03}.png'))
    assert gallery.horizontalScrollBar().maximum() == 0
    assert gallery.verticalScrollBar().maximum() > 0
    first_edges = []
    widths = []
    for grid, tiles in gallery.grids:
        first_edges.append(tiles[0].x())
        widths.append(tiles[0].width())
        for tile in tiles:
            assert tile.art.geometry().bottom() < tile.name_label.geometry().top()
            assert tile.name_label.geometry().bottom() < tile.stamp_label.geometry().top()
            for label in (tile.name_label, tile.stamp_label):
                assert label.wordWrap() and tile.rect().contains(label.geometry())
                assert label.height() >= label.heightForWidth(label.width())
    assert len(set(first_edges)) == 1 and max(widths) - min(widths) <= 1
    headers = gallery.findChildren(QLabel, 'gallerySection')
    assert any(('Trainers' if language == 'en' else 'Dresseurs') in h.text() for h in headers)
    assert all(str(count) in header.text() for count, header in zip((30, 18, 12), headers))
    fallback = gallery.tiles[-1]
    gallery.ensureWidgetVisible(fallback)
    app.processEvents()
    assert fallback.picture.isNull() and fallback.art.icon().isNull()
    assert ('Image unavailable' if language == 'en' else 'Image indisponible') in fallback.art.text()
    bounds = fallback.art.fontMetrics().boundingRect(fallback.art.rect().adjusted(12, 12, -12, -12),
        int(Qt.TextFlag.TextWordWrap), fallback.art.text())
    assert bounds.height() <= fallback.art.height() - 24
    if output := os.environ.get('POKEMIND_GALLERY_QA_DIR'):
        ui.grab().save(output + '/' + f'last-{width}-{theme}-{language}-{font_size}.png')


def test_qt_premium_gallery_scroll_resize_and_repopulate_keep_images_and_release_old_widgets(ui, app, premium_gallery, monkeypatch):
    gallery = premium_gallery
    monkeypatch.setattr(ui.images, 'fetch', lambda *a, **k: pytest.fail('scroll/hover must not request an image'))
    original = [(tile.picture.cacheKey(), tile.art.icon().cacheKey()) for tile in gallery.tiles]
    for width in (1500, 1100, 1500, 1100):
        ui.resize(width, 900)
        app.processEvents()
        gallery.verticalScrollBar().setValue(gallery.verticalScrollBar().maximum())
        gallery.verticalScrollBar().setValue(0)
    assert [(tile.picture.cacheKey(), tile.art.icon().cacheKey()) for tile in gallery.tiles] == original
    assert gallery.horizontalScrollBar().maximum() == 0
    tile = gallery.tiles[0]
    gallery.select_tile(tile)
    tile.art.animate(1)
    gallery.populate([dict(name='Replacement fixture', quantity=60, category='energy')])
    app.processEvents()
    assert not isValid(tile) and gallery.selected_tile is None
    assert len(gallery.tiles) == 1 and gallery.tiles[0].picture.isNull()


def test_qt_premium_gallery_narrow_singleton_empty_and_scroll_anchor(ui, app, premium_gallery):
    gallery = premium_gallery
    ui.resize(1500, 970)
    app.processEvents()
    columns = gallery._columns
    gallery.verticalScrollBar().setValue(150)
    ui.resize(1490, 970)  # same column count, new card width; keep the user's position
    app.processEvents()
    assert abs(gallery.verticalScrollBar().value() - 150) <= 2
    assert gallery._columns == columns
    gallery.setFixedWidth(330)  # available central space, e.g. a widened Coach dock
    app.processEvents()
    assert gallery._columns == 1 and gallery.horizontalScrollBar().maximum() == 0
    fallback = gallery.tiles[-1]
    gallery.ensureWidgetVisible(fallback)
    app.processEvents()
    position = fallback.mapTo(gallery.viewport(), fallback.rect().topLeft())
    assert gallery.viewport().rect().intersects(fallback.rect().translated(position))
    for category in ('pokemon', 'trainer', 'energy'):
        gallery.populate([dict(name='Singleton', quantity=60, category=category)])
        app.processEvents()
        assert len(gallery.tiles) == 1 and gallery.horizontalScrollBar().maximum() == 0
        assert gallery.tiles[0].x() == 16
    gallery.populate([])
    app.processEvents()
    assert not gallery.tiles and gallery.horizontalScrollBar().maximum() == 0


@pytest.mark.parametrize('theme', ['dark', 'light'])
@pytest.mark.parametrize('floating', [False, True])
def test_013_native_chat_curves_selection_links_and_synthetic_capture(ui, app, monkeypatch, theme, floating):
    from pathlib import Path
    from types import SimpleNamespace
    from PySide6.QtGui import QTextCursor, QTextDocument
    from pokemind.desktop.theme import colors
    ui.theme.setCurrentIndex(ui.theme.findData(theme))
    ui.resize(1100 if ui.devicePixelRatioF() > 1 else 1500, 970)
    ui.navigation.setCurrentRow(2)
    ui.conversation['messages'] = [
        {'role': 'user', 'content': 'Question inventée : pourquoi ce matchup?'},
        {'role': 'assistant', 'content': 'Réponse **hypothétique**. [Source](https://example.org/public)\n\n'
         '| Carte | Rôle |\n|---|---|\n| Alpha | Attaque |\n\n' + 'Texte inventé lisible. ' * 8},
        {'role': 'user', 'content': 'Deuxième tour : <script>alert(1)</script>'},
        {'role': 'assistant', 'content': 'Deuxième réponse, sans carte cachée inventée.'}]
    ui.render_chat()
    monkeypatch.setattr(ui.activity, 'elapsed', SimpleNamespace(start=lambda: None, isValid=lambda: True, elapsed=lambda: 14000))
    ui.activity.start('Outils PokeMind · consultation 1')
    ui.activity.clock.setText('14 s')
    if floating:
        ui.chat_dock.setFloating(True)
        ui.chat_dock.resize(355, 850)
    else:
        ui.resizeDocks([ui.chat_dock], [355], Qt.Orientation.Horizontal)
    app.processEvents()
    transcript = ui.transcript
    assert transcript.document().rootFrame().childFrames() and len(transcript.bubble_rects()) == 4
    # Sample actual native pixels: the corner is viewport colour, the upper edge is bubble fill.
    for role, rect in transcript.bubble_rects()[:2]:
        transcript.verticalScrollBar().setValue(max(0, int(rect.top()) - 8))
        app.processEvents()
        image = transcript.viewport().grab().toImage()
        scale = image.devicePixelRatio()
        left = rect.left() - transcript.horizontalScrollBar().value()
        top = rect.top() - transcript.verticalScrollBar().value()
        def pixel(dx, dy):
            return image.pixelColor(round((left + dx) * scale), round((top + dy) * scale)).name()
        c = colors(theme)
        assert pixel(1, 1) == c['input'].lower(), (role, pixel(1, 1), c['input'])
        assert pixel(rect.width() - 20, 5) == (c['alternate'] if role == 'user' else c['surface']).lower()
    transcript.setFocus()
    QTest.keyClick(transcript, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    assert transcript.textCursor().hasSelection()
    copied = transcript.createMimeDataFromSelection().text()
    assert 'Deuxième tour' in copied and '<script>alert(1)</script>' in copied and 'Deuxième réponse' in copied
    cursor = transcript.textCursor()
    cursor.clearSelection()
    transcript.setTextCursor(cursor)
    # The native hit-test and HTTPS signal remain usable with the custom background painter.
    document = transcript.document()
    found = document.find('Source', 0, QTextDocument.FindFlag.FindCaseSensitively)
    found.setPosition(found.selectionStart() + 2)
    transcript.setTextCursor(found)
    transcript.ensureCursorVisible()
    app.processEvents()
    opened = []
    monkeypatch.setattr(window.QDesktopServices, 'openUrl', lambda url: opened.append(url.toString()) or True)
    point = transcript.cursorRect(found).center()
    assert transcript.anchorAt(point) == 'https://example.org/public'
    QTest.mouseClick(transcript.viewport(), Qt.MouseButton.LeftButton, pos=point)
    assert opened == ['https://example.org/public']
    assert ui.source_toggle.isVisible() and 'https://example.org/public' in ui.source_drawer.toPlainText()
    transcript.moveCursor(QTextCursor.MoveOperation.Start)
    transcript.ensureCursorVisible()
    app.processEvents()
    output = Path(__file__).resolve().parents[1] / 'build/qa-013'
    output.mkdir(parents=True, exist_ok=True)
    suffix = f'{theme}-{"floating" if floating else "docked"}-{transcript.devicePixelRatioF():g}'
    assert ui.grab().save(str(output / f'mainwindow-{suffix}.png'))
    assert ui.chat_dock.grab().save(str(output / f'chat-{suffix}.png'))
    assert ui.activity.clock.text() == '14 s' and ui.activity.timer.isActive()
    assert transcript.isReadOnly()  # selection remains available in read-only mode


def test_013_streaming_appends_without_reparse_or_growing_prefix_cache(ui, app, monkeypatch):
    ui.conversation['messages'] = [{'role': 'user', 'content': 'Premier tour'},
        {'role': 'assistant', 'content': 'Première réponse'}, {'role': 'user', 'content': 'Deuxième tour'},
        {'role': 'assistant', 'content': ''}]
    ui.render_chat(streaming=True)
    parsed = []
    real = window.message_html
    monkeypatch.setattr(window, 'message_html', lambda text: (parsed.append(len(text)), real(text))[1])
    cached = len(ui._bubbles)
    for _ in range(100):
        ui.chat_delta(' **inventé**')
    assert ui.chat_render_timer.isActive()
    ui.chat_render_timer.stop()
    ui.render_stream()
    for _ in range(10):
        ui.chat_delta(' texte')
        ui.chat_render_timer.stop()
        ui.render_stream()
    assert parsed == [] and len(ui._bubbles) == cached
    assert ui.transcript.toPlainText().count('POKEMIND') == 2 and 'Première réponse' in ui.transcript.toPlainText()
    ui.render_chat()
    assert parsed == [len(ui.conversation['messages'][-1]['content'])]
    assert '**' not in ui.transcript.toPlainText() and ui.transcript.toPlainText().count('inventé') == 100


def install_selected_history(ui, app):
    """Invented canonical read model; selection must still happen through the real widgets."""
    from copy import deepcopy
    from test_opponent_auto_deck import match, NAMES
    from pokemind.battle_batch import group_matches
    records = [match() | {'match': ref, 'opponent': {'label': family}, 'evidence': []}
               for ref, family in [('OLD-A1', 'Invented Alpha'), ('OLD-A2', 'Invented Alpha'),
                                   ('RECENT-B', 'Invented Beta')]]
    records[-1]['opponent_cards'] = match(NAMES[:2])['opponent_cards']
    report = deepcopy(ui.services.report)
    report.update(matches=records, groups=group_matches(records), coverage={'valid': 3},
                  outcomes={'wins': 0, 'losses': 3, 'unknown': 0})
    ui.services.full_report = ui.services.report = report
    ui.loaded({'report': report, 'learning': None})
    wait_until(app, lambda: not ui.jobs)
    return report


def select_combo_item(app, combo, index):
    """A real activation, including choosing the already displayed first item."""
    combo.showPopup()
    wait_until(app, lambda: combo.view().isVisible())
    QTest.keyClick(combo.view(), Qt.Key.Key_Home)
    for _ in range(index):
        QTest.keyClick(combo.view(), Qt.Key.Key_Down)
    QTest.keyClick(combo.view(), Qt.Key.Key_Return)
    app.processEvents()


def select_historical_game(ui, app, reference):
    """Combats -> family row -> game dropdown. Never inject Services.selected_match."""
    ui.navigation.setCurrentRow(1)
    wait_until(app, lambda: ui.games.isVisible() and not ui.stack.transition.isVisible())
    family = 'Invented Beta' if reference == 'RECENT-B' else 'Invented Alpha'
    row = next(i for i in range(ui.matchups.rowCount()) if ui.matchups.item(i, 0).text() == family)
    QTest.mouseClick(ui.matchups.viewport(), Qt.MouseButton.LeftButton,
                     pos=ui.matchups.visualItemRect(ui.matchups.item(row, 0)).center())
    app.processEvents()
    index = next(i for i in range(ui.games.count()) if ui.games.itemData(i)['match'] == reference)
    select_combo_item(app, ui.games, index)
    assert ui.games.currentData()['match'] == reference


def test_013_explicit_selected_old_match_is_local_and_visible_without_provider(ui, app, monkeypatch):
    from test_opponent_auto_deck import match, public_index, files
    from pokemind import battle_batch, deck_public_stats
    from pokemind.desktop.services import Services
    monkeypatch.setattr(battle_batch, 'public_context', lambda *a: (public_index(), [], {}))
    # The independent selector-refresh journey covers collection; this local-action journey never collects.
    monkeypatch.setattr(deck_public_stats, 'refresh_state', lambda *a, **k: {'automatic_due': False})
    install_selected_history(ui, app)
    select_historical_game(ui, app, 'OLD-A2')
    monkeypatch.setattr(ui, 'get_adapter', lambda: pytest.fail('local request must not reach a provider'))
    monkeypatch.setattr(ui.services, 'deck_options', lambda: REAL_DECK_OPTIONS(ui.services))
    ui.chat_input.setPlainText('Reconstruis le deck adverse de cette partie')
    ui.send_chat()
    wait_until(app, lambda: not ui.chat_busy and not ui.jobs, timeout=15000)
    assert len(files(ui.root)) == 1 and len(ui.deck_rows) == 1
    assert 'Deck adverse ajouté (reconstruction hypothétique)' in ui.transcript.toPlainText()
    assert 'PUBLIC/' in ui.transcript.toPlainText() and '6 cartes observées / 60 supposées' in ui.transcript.toPlainText()
    assert not ui.cloud_consent.isChecked() and all(m['local_only'] for m in ui.conversation['messages'])
    ui.chat_input.setPlainText('Reconstruis le deck adverse de cette partie')
    ui.send_chat()
    wait_until(app, lambda: not ui.chat_busy and not ui.jobs, timeout=15000)
    assert len(files(ui.root)) == 1 and 'Déjà dans Deck Lab' in ui.transcript.toPlainText()


def test_013_cancelled_late_selected_reconstruction_never_saves_or_changes_other_discussion(ui, app, monkeypatch):
    from test_opponent_auto_deck import match, public_index, files
    from pokemind import battle_batch
    monkeypatch.setattr(battle_batch, 'public_context', lambda *a: (public_index(), [], {}))
    entered, release = threading.Event(), threading.Event()
    real = ui.services.save_public_opponent
    def slow(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return real(*args, **kwargs)
    monkeypatch.setattr(ui.services, 'save_public_opponent', slow)
    install_selected_history(ui, app)
    select_historical_game(ui, app, 'OLD-A2')
    ui.chat_input.setPlainText('Ajoute le deck adverse de cette partie')
    ui.send_chat()
    wait_until(app, entered.is_set)
    previous = ui.conversation
    ui.stop_chat()
    ui.conversation = ui.store.new('codex')
    ui.render_chat()
    release.set()
    wait_until(app, lambda: not ui.chat_busy and not ui.jobs)
    assert not files(ui.root) and ui.conversation['messages'] == []
    assert 'annulé' in previous['messages'][-1]['content']


def test_qt_premium_gallery_real_exports_comparison_and_preferences(ui, app, premium_gallery, monkeypatch, local_tmp):
    from types import SimpleNamespace
    from pokemind.desktop.insights import favorite_key
    copied = []
    # Exercise the real copy slot without reading or replacing the OS clipboard.
    monkeypatch.setattr(window.QApplication, 'clipboard', staticmethod(lambda: SimpleNamespace(setText=copied.append)))
    export = ui.deck_rows[0]['export']
    QTest.mouseClick(ui.copy_deck, Qt.MouseButton.LeftButton)
    assert copied == [export]
    destination = local_tmp / 'synthetic-export.txt'
    monkeypatch.setattr(window.QFileDialog, 'getSaveFileName', lambda *args: (str(destination), ''))
    QTest.mouseClick(ui.save_deck, Qt.MouseButton.LeftButton)
    assert destination.read_text(encoding='utf-8') == export
    destination.write_text('Previous synthetic export', encoding='utf-8')
    QTest.mouseClick(ui.save_deck, Qt.MouseButton.LeftButton)
    assert destination.read_text(encoding='utf-8') == 'Previous synthetic export'
    ui.compare_decks()  # Actual Services.compare and deck parser, same 60-card reference.
    assert '60 copies communes' in ui.deck_diff.text()
    QTest.mouseClick(ui.favorite_button, Qt.MouseButton.LeftButton)
    QTest.mouseClick(ui.main_button, Qt.MouseButton.LeftButton)
    wait_until(app, lambda: not ui.jobs)
    key = favorite_key(ui.deck_rows[0])
    saved = window.Store(ui.root).preferences()
    assert saved['favorite_decks'] == [key] and saved['main_deck'] == key
    assert not saved['cloud_consent'] and saved['sharing'] == 'public'
    assert ui.deck_text.toPlainText() == export and len(ui.gallery.tiles) == 20
    ui.deck_views.setCurrentIndex(1)
    app.processEvents()
    assert ui.deck_text.isVisible() and ui.deck_text.toPlainText() == export


def configure_deck_controls(ui, app, width, theme, language, font_size):
    ui.theme.setCurrentIndex(1 if theme == 'light' else 0)
    ui.language.setCurrentIndex(ui.language.findData(language))
    ui.apply_theme()  # reset a prior large-font QA override; keep 006's 17/14px defaults
    for control in (ui.deck_picker, ui.favorite_button, ui.main_button, ui.add_deck_button):
        control.setStyleSheet(f'font-size:{font_size}px;')
    if font_size == 18:
        ui.setStyleSheet(ui.styleSheet() + '\nQScrollArea#deckGallery QLabel {font-size:18px;}')
    ui.resize(width, 970 if width == 1500 else 900)
    for _ in range(4):
        app.processEvents()


def deck_controls_measurements(ui):
    from PySide6.QtCore import QPoint
    from PySide6.QtWidgets import QStyle, QStyleOptionButton
    controls = (ui.deck_picker, ui.favorite_button, ui.main_button, ui.add_deck_button)
    result = []
    for control in controls:
        position = control.mapTo(ui, QPoint(0, 0))
        value = dict(text=control.currentText() if control is ui.deck_picker else control.text(),
                     geometry=[position.x(), position.y(), control.width(), control.height()],
                     font_px=control.font().pixelSize(), visible=control.isVisible())
        if control is not ui.deck_picker:
            option = QStyleOptionButton()
            control.initStyleOption(option)
            contents = control.style().subElementRect(QStyle.SubElement.SE_PushButtonContents, option, control)
            value.update(text_width=control.fontMetrics().horizontalAdvance(control.text()),
                         text_height=control.fontMetrics().height(),
                         contents=[contents.x(), contents.y(), contents.width(), contents.height()])
        result.append(value)
    return result


def assert_deck_controls_readable(ui):
    from PySide6.QtCore import QRect
    measurements = deck_controls_measurements(ui)
    boxes = [QRect(*entry['geometry']) for entry in measurements]
    for entry, box in zip(measurements, boxes):
        assert entry['visible'] and ui.rect().contains(box), entry
    page = ui.deck_picker.parentWidget()
    for control in (ui.deck_picker, ui.favorite_button, ui.main_button, ui.add_deck_button):
        assert page.rect().contains(control.geometry())
    for entry in measurements[1:]:
        # Both native style contents and independent QSS padding/border budget.
        assert entry['contents'][2] >= entry['text_width'], entry
        assert entry['geometry'][2] >= entry['text_width'] + 30, entry
        assert entry['contents'][3] >= entry['text_height'], entry
    for index, box in enumerate(boxes):
        assert all(not box.intersects(other) for other in boxes[index + 1:]), measurements
    combo = ui.deck_picker
    assert combo.width() >= combo.fontMetrics().horizontalAdvance('M' * 12) + 35
    assert combo.currentText() == combo.accessibleName()
    assert combo.toolTip().startswith(combo.currentText())  # full source/period now augment the readable name
    assert combo.itemData(combo.currentIndex(), Qt.ItemDataRole.ToolTipRole) == combo.toolTip()
    assert ui.gallery.horizontalScrollBar().maximum() == 0
    return measurements


@pytest.mark.parametrize('width', [1100, 1500])
@pytest.mark.parametrize('theme,language', [('dark', 'fr'), ('light', 'en'), ('light', 'fr'), ('dark', 'en')])
@pytest.mark.parametrize('font_size', [14, 18])
def test_qt_deck_controls_layout(ui, app, premium_gallery, width, theme, language, font_size):
    configure_deck_controls(ui, app, width, theme, language, font_size)
    if output := os.environ.get('POKEMIND_CONTROLS_QA_DIR'):
        import json
        from pathlib import Path
        folder = Path(output)
        name = f'controls-{width}-{theme}-{language}-{font_size}'
        ui.gallery.select_tile(ui.gallery.tiles[0])
        ui.grab().save(str(folder / (name + '.png')))
        (folder / (name + '.json')).write_text(json.dumps(dict(
            window=[ui.width(), ui.height()], dpr=ui.devicePixelRatioF(),
            controls=deck_controls_measurements(ui),
            viewport=[ui.gallery.viewport().width(), ui.gallery.viewport().height()],
            columns=ui.gallery._columns,
            horizontal_scroll=ui.gallery.horizontalScrollBar().maximum()), indent=2), encoding='utf-8')
    measurements = assert_deck_controls_readable(ui)
    if app.platformName() == 'windows' and width == 1500 and font_size == 14:
        # QComboBox is 3 px taller; fixed-height buttons are vertically centred.
        centers = [entry['geometry'][1] + entry['geometry'][3] / 2 for entry in measurements]
        assert max(centers) - min(centers) <= 1
    if app.platformName() == 'windows':
        assert ui.gallery._columns == (3 if width == 1500 else 2)
    assert ui.gallery.viewport().height() >= 200


def test_qt_deck_controls_resize_language_focus_and_real_actions(ui, app, premium_gallery, monkeypatch):
    from pokemind.desktop.deck_entry import DeckEntryDialog
    from pokemind.desktop.insights import favorite_key
    from PySide6.QtWidgets import QDockWidget
    rows = [dict(ui.deck_rows[0]), dict(ui.deck_rows[0], label='Second invented deck', selector='second',
                                     export=ui.deck_rows[0]['export'].replace('Synthetic', 'Alternative'))]
    rows[0]['label'] = 'Synthetic deck with a very long title ' * 5
    ui.loaded_decks(rows)
    wait_until(app, lambda: not ui.jobs)
    controls = (ui.deck_picker, ui.favorite_button, ui.main_button, ui.add_deck_button)
    configure_deck_controls(ui, app, 1100, 'dark', 'fr', 18)
    before = dict(ui.preferences)
    for width, language in ((1500, 'en'), (1100, 'fr'), (1500, 'fr'), (1100, 'en')):
        ui.language.setCurrentIndex(ui.language.findData(language))
        ui.resize(width, 900)
        for _ in range(4):
            app.processEvents()
        assert_deck_controls_readable(ui)
        assert (ui.deck_picker, ui.favorite_button, ui.main_button, ui.add_deck_button) == controls
    # The production shell enforces 1100 px. Constrain only this test page to
    # exercise a smaller content area; the shell/dock minimums stay unchanged.
    dock = next(d for d in ui.findChildren(QDockWidget) if d.isVisible())
    ui.resize(900, 900)
    app.processEvents()
    assert ui.width() >= 1100  # existing production minimum, deliberately preserved
    page = ui.deck_picker.parentWidget()
    page.setFixedWidth(340)
    for _ in range(4):
        app.processEvents()
    assert_deck_controls_readable(ui)
    assert ui.deck_picker.width() <= 300
    assert ui.gallery._columns == 1
    assert ui.gallery.viewport().height() >= 200
    if output := os.environ.get('POKEMIND_CONTROLS_QA_DIR'):
        import json
        from pathlib import Path
        folder = Path(output)
        ui.grab().save(str(folder / 'controls-narrow-content-dark-en-18.png'))
        (folder / 'controls-narrow-content-dark-en-18.json').write_text(json.dumps(dict(
            requested_window_width=900, actual_window_width=ui.width(), dock_width=dock.width(),
            page_width=ui.deck_picker.parentWidget().width(), controls=deck_controls_measurements(ui),
            viewport=[ui.gallery.viewport().width(), ui.gallery.viewport().height()],
            columns=ui.gallery._columns, horizontal_scroll=ui.gallery.horizontalScrollBar().maximum()),
            indent=2), encoding='utf-8')
    page.setMinimumWidth(0)
    page.setMaximumWidth(16777215)
    for _ in range(4):
        app.processEvents()
    # Natural Tab order survives wrapping; Space invokes each same slot once.
    ui.deck_picker.setFocus()
    for control in controls[1:]:
        QTest.keyClick(app.focusWidget(), Qt.Key.Key_Tab)
        assert control.hasFocus()
    calls = []
    monkeypatch.setattr(DeckEntryDialog, 'exec', lambda dialog: calls.append(dialog.services) or
                        DeckEntryDialog.DialogCode.Rejected)
    key = favorite_key(rows[0])
    for button, preference in ((ui.favorite_button, 'favorite_decks'), (ui.main_button, 'main_deck')):
        QTest.mouseClick(button, Qt.MouseButton.LeftButton)
        wait_until(app, lambda: not ui.jobs)
        assert key in ui.preferences[preference]
        assert_deck_controls_readable(ui)  # checked glyph/text also fit
        button.setFocus()
        QTest.keyClick(button, Qt.Key.Key_Space)
        wait_until(app, lambda: not ui.jobs)
        assert not ui.preferences[preference]
    QTest.mouseClick(ui.add_deck_button, Qt.MouseButton.LeftButton)
    ui.add_deck_button.setFocus()
    QTest.keyClick(ui.add_deck_button, Qt.Key.Key_Space)
    assert calls == [ui.services, ui.services]
    ui.deck_picker.setFocus()
    QTest.keyClick(ui.deck_picker, Qt.Key.Key_Down)
    wait_until(app, lambda: not ui.jobs)
    assert ui.deck_picker.currentIndex() == 1 and ui.deck_text.toPlainText() == rows[1]['export']
    assert_deck_controls_readable(ui)
    ui.deck_picker.showPopup()
    # Native Qt animates the popup before its live list becomes visible.
    wait_until(app, lambda: ui.deck_picker.view().isVisible())
    view = ui.deck_picker.view()
    index = view.model().index(0, 0)
    QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=view.visualRect(index).center())
    ui.deck_picker.hidePopup()
    ui.deck_picker.setFocus()
    QTest.keyClick(ui.deck_picker, Qt.Key.Key_Up)
    wait_until(app, lambda: not ui.jobs)
    assert ui.deck_picker.currentIndex() == 0
    # Use the real offline public-stats read, forbid any refresh path.
    original = ui.services.deck_public_stats
    def offline_stats(row, refresh='none', **kwargs):
        assert refresh == 'none'
        return original(row, refresh, **kwargs)
    monkeypatch.setattr(ui.services, 'deck_public_stats', offline_stats)
    for index, view in ((1, ui.deck_text), (2, ui.public_stats_scroll), (0, ui.gallery)):
        ui.deck_views.setCurrentIndex(index)
        wait_until(app, lambda: not ui.jobs)
        assert view.isVisible()
    assert dock.isVisible() and ui.chat_input.isVisible()
    configure_deck_controls(ui, app, 1500, 'light', 'fr', 14)
    assert_deck_controls_readable(ui)
    configure_deck_controls(ui, app, 1100, 'dark', 'fr', 18)
    assert_deck_controls_readable(ui)
    saved = window.Store(ui.root).preferences()
    assert saved['cloud_consent'] == before['cloud_consent'] and not saved['cloud_consent']
    assert saved['sharing'] == before['sharing'] == 'public'
    ui.loaded_decks([])
    app.processEvents()
    assert ui.deck_picker.toolTip() == ui.deck_picker.accessibleName() == ''
    assert not ui.favorite_button.isEnabled() and not ui.main_button.isEnabled()
    assert ui.add_deck_button.isEnabled()


@pytest.mark.parametrize('delayed', ['gallery', 'image'])
def test_qt_premium_gallery_real_delayed_workers_never_cross_decks(ui, app, premium_gallery, monkeypatch, delayed):
    raw = premium_gallery.tiles[0].picture.toImage()
    from PySide6.QtCore import QBuffer, QIODevice
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    raw.save(buffer, 'PNG')
    data = bytes(buffer.data())
    entered, release = threading.Event(), threading.Event()
    def cards(export):
        if export == 'A' and delayed == 'gallery':
            entered.set()
            assert release.wait(5)
        return [dict(name=export, category='pokemon', quantity=60, identity=export)]
    def fetch(identity):
        if identity == 'A' and delayed == 'image':
            entered.set()
            assert release.wait(5)
        return dict(data=data, source_url='https://example.invalid/' + identity)
    monkeypatch.setattr(ui.services, 'gallery_cards', cards)
    monkeypatch.setattr(ui.images, 'fetch', fetch)
    rows = [dict(label=name, selector=name, export=name, kind='Synthetic QA', legality='unknown',
                 source={}, total=60) for name in ('A', 'B')]
    try:
        ui.loaded_decks(rows)
        wait_until(app, entered.is_set)
        old = ui.gallery.tiles[0]
        old.art.animate(1)
        ui.deck_picker.setCurrentIndex(1)
        wait_until(app, lambda: len(ui.gallery.tiles) == 1 and ui.gallery.tiles[0].card['name'] == 'B' and
                   ui.gallery.tiles[0].provenance.endswith('/B'))
        generation = ui.gallery.generation
        assert not isValid(old)
        release.set()
        wait_until(app, lambda: not ui.jobs)
        assert ui.gallery.generation == generation
        assert ui.gallery.tiles[0].card['name'] == 'B' and ui.gallery.tiles[0].provenance.endswith('/B')
        assert ui.deck_text.toPlainText() == 'B' and not ui.cloud_consent.isChecked()
    finally:
        release.set()
