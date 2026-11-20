"""The Coach's idea buttons set every text of the application (owner, 2026-11-19, « le MÊME style PARTOUT »).

Every page is opened in both themes, with its tabs, and each visible widget is painted alone into a device whose
paint engine records the font of every piece of text drawn: what the style draws (labels, buttons, tables and
their headers, lists, fields, tabs), the rich text, and what the application paints by hand (charts, rings, bars,
the Active deck card, pills, the gallery). Anything that is not Segoe UI, 14 px, semibold (600) fails, except the
titles and the large numbers named in theme.TITLE_NAMES, the headings of rich text, the numbers in the rings, the
words in bold of the Coach's answers (700, same face and size; the Coach only) and the console grid of the Terminal
(fixed-width face, same size and weight).
"""
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import QPoint
from PySide6.QtGui import QFont, QPaintDevice, QPaintEngine, QRegion
from PySide6.QtWidgets import QAbstractButton, QAbstractScrollArea, QApplication, QComboBox, QTextEdit, QToolTip, QWidget

from test_desktop_qt import app, ui, wait_until  # noqa: F401
from pokemind.desktop import terminal, window
from pokemind.desktop.theme import IDEA_FAMILY, IDEA_SIZE, IDEA_WEIGHT, TITLE_NAMES, idea_font
from pokemind.desktop.widgets import CorpusChart, RecordRing

THEMES = ('dark', 'light')
HERE = Path(__file__).resolve().parent
NUMBER = re.compile(r'^(\d+|—)$')
COACH_BOLD = 700  # the words in bold of the Coach's answers (owner, 2026-11-19)


class Recorder(QPaintEngine):
    """Keeps (text, font) of every text item; draws nothing."""
    def __init__(self):
        super().__init__(QPaintEngine.PaintEngineFeature.AllFeatures)
        self.texts = []

    def begin(self, device):
        return True

    def end(self):
        return True

    def updateState(self, state):
        pass

    def drawTextItem(self, position, item):
        if item.text().strip():
            self.texts.append((item.text(), QFont(item.font())))

    def type(self):
        return QPaintEngine.Type.User

    # Each drawing call needs a body: the defaults of QPaintEngine call one another.
    def drawPixmap(self, *args): pass
    def drawImage(self, *args): pass
    def drawTiledPixmap(self, *args): pass
    def drawPolygon(self, *args): pass
    def drawPath(self, *args): pass
    def drawLines(self, *args): pass
    def drawRects(self, *args): pass
    def drawPoints(self, *args): pass
    def drawEllipse(self, *args): pass


class Device(QPaintDevice):
    METRICS = {QPaintDevice.PaintDeviceMetric.PdmWidth: 4000, QPaintDevice.PaintDeviceMetric.PdmHeight: 4000,
               QPaintDevice.PaintDeviceMetric.PdmWidthMM: 1058, QPaintDevice.PaintDeviceMetric.PdmHeightMM: 1058,
               QPaintDevice.PaintDeviceMetric.PdmDpiX: 96, QPaintDevice.PaintDeviceMetric.PdmDpiY: 96,
               QPaintDevice.PaintDeviceMetric.PdmPhysicalDpiX: 96, QPaintDevice.PaintDeviceMetric.PdmPhysicalDpiY: 96,
               QPaintDevice.PaintDeviceMetric.PdmDepth: 32, QPaintDevice.PaintDeviceMetric.PdmNumColors: 0xFFFFFF,
               QPaintDevice.PaintDeviceMetric.PdmDevicePixelRatio: 1,
               QPaintDevice.PaintDeviceMetric.PdmDevicePixelRatioScaled: 1}

    def __init__(self):
        super().__init__()
        self.engine = Recorder()

    def paintEngine(self):
        return self.engine

    def metric(self, metric):
        return self.METRICS.get(metric, 0)


def drawn(widget):
    """The texts this widget paints itself (its children are painted on their own)."""
    device = Device()
    widget.render(device, QPoint(), QRegion(), QWidget.RenderFlag.DrawWindowBackground)
    return device.engine.texts


def family(font):
    return (font.families() or [font.family()])[0]


def pixels(font):
    return font.pixelSize() if font.pixelSize() > 0 else round(font.pointSizeF() * 96 / 72)


def is_default(font):
    return family(font) == IDEA_FAMILY and pixels(font) == IDEA_SIZE and font.weight() == IDEA_WEIGHT


def owner(widget):
    """A scroll area paints its text in its viewport: the area is the widget that is named."""
    parent = widget.parentWidget()
    return parent if isinstance(parent, QAbstractScrollArea) and parent.viewport() is widget else widget


def headings(widget):
    """The text of the headings of a rich text (h1 to h6): the titles of its sections."""
    if not isinstance(widget, QTextEdit):
        return set()
    document, found = widget.document(), set()
    block = document.begin()
    while block.isValid():
        if block.blockFormat().headingLevel():
            found.add(block.text())
        block = block.next()
    return found


def bold_words(widget):
    """The words set in bold (<b>, <strong>, table headers) in the Coach's answers, the only rich text whose
    bold stands out (owner, 2026-11-19)."""
    if not isinstance(widget, QTextEdit) or widget.objectName() != 'chatTranscript':
        return set()
    found, block = set(), widget.document().begin()
    while block.isValid():
        iterator = block.begin()
        while not iterator.atEnd():
            fragment = iterator.fragment()
            if fragment.charFormat().fontWeight() == COACH_BOLD:
                found.add(fragment.text())
            iterator += 1
        block = block.next()
    return found


def allowed(widget, text, font):
    """The named exceptions: titles and large numbers keep their size and weight (same face); the words in bold
    of the Coach's answers are at 700 (same face and size); the console grid keeps a fixed-width face (same size
    and weight)."""
    named = owner(widget)
    if isinstance(named, terminal.TerminalView):
        return family(font) in terminal.MONO_FAMILIES and pixels(font) == IDEA_SIZE and font.weight() in (600, 700)
    if family(font) != IDEA_FAMILY:
        return False
    if named.objectName() in TITLE_NAMES:
        return True
    if pixels(font) == IDEA_SIZE and font.weight() == COACH_BOLD and any(
            text.strip() and text.strip() in words for words in bold_words(named)):
        return True  # bold in the Coach's answers
    if isinstance(named, (RecordRing, CorpusChart)) and NUMBER.match(text) and pixels(font) > IDEA_SIZE:
        return True  # the number in the middle of a ring
    return any(text.strip() and text.strip() in heading for heading in headings(named))


def offenders(root, where):
    found = []
    for widget in [root] + root.findChildren(QWidget):
        if not widget.isVisible() or widget.width() <= 0 or widget.height() <= 0:
            continue
        for text, font in drawn(widget):
            if not is_default(font) and not allowed(widget, text, font):
                found.append('%s · %s#%s · %r · %s %d px %d' % (where, type(owner(widget)).__name__,
                                                                owner(widget).objectName(), text[:40], family(font),
                                                                pixels(font), font.weight()))
    return found


def popups(ui, where):
    """The lists of the drop-down boxes and the menus of the buttons, opened one at a time."""
    found = []
    for combo in ui.findChildren(QComboBox):
        if combo.isVisible() and combo.count():
            combo.showPopup()
            QApplication.processEvents()
            found += offenders(combo.view().window(), where + ' › liste de ' + (combo.objectName() or 'choix'))
            combo.hidePopup()
    for button in ui.findChildren(QAbstractButton):
        menu = button.menu() if hasattr(button, 'menu') else None
        if button.isVisible() and menu is not None and menu.actions():
            menu.popup(button.mapToGlobal(QPoint(0, button.height())))
            QApplication.processEvents()
            found += offenders(menu, where + ' › menu ' + button.text())
            menu.hide()
    return found


def settle(app, ui):
    wait_until(app, lambda: not ui.jobs and not ui.stack.transition.isVisible(), 8000)
    app.processEvents()


@pytest.mark.parametrize('theme', THEMES)
def test_every_text_of_every_page_is_set_like_the_idea_buttons(ui, app, monkeypatch, theme):
    from test_desktop_terminal import FakeSession
    monkeypatch.setattr(terminal, 'Session', FakeSession)
    monkeypatch.setattr(terminal, 'available', lambda: True)
    monkeypatch.setattr(window.QMessageBox, 'question', lambda *a, **k: window.QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(window.QMessageBox, 'information', lambda *a, **k: None)
    try:
        found, tips = every_page(ui, app, theme)
    finally:
        for view in ui.terminal_views():
            if view.session:
                view.session.close()
        while ui.terminal_tabs.count():
            ui.close_terminal(0)
        ui.advanced_mode.setChecked(False)
        QToolTip.hideText()
    unique = list(dict.fromkeys(line.split(' · ', 1)[-1] for line in found))  # one line per text and widget
    assert tips and not found, '\n'.join(unique[:80])


def every_page(ui, app, theme):
    ui.resize(1440, 900)
    ui.theme.setCurrentIndex(1 if theme == 'light' else 0)
    ui.conversation['messages'] = [  # a discussion with what the Coach's answers hold: bold, heading, code, tools
        {'role': 'user', 'content': 'Question inventée ?'},
        {'role': 'assistant', 'content': '## Titre inventé\n\nRéponse **en gras** et `code`.\n\n- Point inventé.\n\n'
                                         '[Outil · Bash · python -V]\n\n| A | B |\n|---|---|\n| 1 | 2 |'}]
    ui.render_chat()
    ui.statusBar().showMessage('Message d’état inventé')
    ui.open_match('M0001')  # Combats: an opponent chosen, its summary and a game open
    settle(app, ui)
    found = []
    for row in range(7):
        if row == 6:
            ui.advanced_mode.setChecked(True)  # the Terminal page exists in advanced mode only
            settle(app, ui)
        ui.navigation.setCurrentRow(row)
        settle(app, ui)
        page = ui.navigation.item(row).text()
        if row == 6:
            for button in ui.terminal_buttons.values():
                button.setEnabled(True)
            ui.terminal_buttons['powershell'].click()
            view, = ui.terminal_views()
            view.feed('PS C:\\> Sortie inventée de la console\r\n')
            view.update()
            settle(app, ui)
        states = [(page, lambda: None)]
        if row == 0:
            states += [(page + ' › ' + ui.statistics.tabs.tabText(i), lambda i=i: ui.statistics.tabs.setCurrentIndex(i))
                       for i in range(ui.statistics.tabs.count())]
        elif row == 2:
            states += [(page + ' › ' + ui.deck_views.tabText(i), lambda i=i: ui.deck_views.setCurrentIndex(i))
                       for i in range(ui.deck_views.count())]
        elif row == 5:
            states += [(page + ' › ' + key, lambda k=key: ui.show_settings_section(k)) for key in ui.settings_sections]
        for name, enter in states:
            enter()
            settle(app, ui)
            found += offenders(ui, theme + ' · ' + name)
        found += popups(ui, theme + ' · ' + page)
    # A tooltip, drawn by the style outside the window.
    QToolTip.showText(ui.mapToGlobal(QPoint(40, 40)), 'Infobulle inventée', ui.navigation)
    app.processEvents()
    tips = [w for w in QApplication.topLevelWidgets() if w.isVisible() and w.metaObject().className() == 'QTipLabel']
    for tip in tips:
        found += offenders(tip, theme + ' · infobulle')
    QToolTip.hideText()
    # The Coach's bold stands out: drawn at 700, the rest of its answer at 600; a page's bold stays at 600.
    weights = {text.strip(): font.weight() for text, font in drawn(ui.transcript.viewport())}
    assert weights.get('en gras') == COACH_BOLD and weights.get('Réponse') == IDEA_WEIGHT, weights
    assert 'b, strong, th {font-weight:600;}' in window.browser_style(ui.memory_text, '#000')
    ui.statistics.tabs.setCurrentIndex(0)
    ui.deck_views.setCurrentIndex(0)
    ui.show_settings_section('general')
    return found, tips


def test_the_application_font_and_every_hand_painted_text_use_the_idea_font(app):
    from pokemind.desktop.theme import apply_application_font
    apply_application_font(app)
    for font in (app.font(), idea_font()):
        assert is_default(font)
    assert set(TITLE_NAMES) == {'title', 'brand', 'heroTitle', 'sectionTitle', 'gallerySection', 'loadingTitle',
                                'deckTitle', 'chatTitle', 'tileValue', 'tileName', 'statValue'}


WINDOWS_FONTS = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
SIZES = ((1100, 700), (1440, 900))


@pytest.mark.skipif(not (WINDOWS_FONTS / 'seguisb.ttf').is_file(), reason='polices Windows absentes (Segoe UI)')
def test_nothing_is_cut_in_the_smallest_window(local_tmp):
    """The semibold text takes more room: at 1100 × 700 (and at the usual size), the « Deck actif » card writes
    every line whole, the menu shows every row without a bar, and the tiles and the running text are as tall as
    their text. Measured with the real Segoe UI: off screen, Qt has no font unless it is given the Windows fonts,
    so the check runs in a process of its own that has them (as scripts/qa_premium_look.py)."""
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QPA_FONTDIR=str(WINDOWS_FONTS), LOCALAPPDATA=str(local_tmp),
               POKEMIND_TEST_OFFLINE='1', PYTHONPATH=os.pathsep.join([str(HERE), str(HERE.parent / 'src')]))
    done = subprocess.run([sys.executable, '-c', 'import sys, test_desktop_global_style as t; t.cut_check(sys.argv[1])',
                           str(local_tmp)], env=env, cwd=str(local_tmp), capture_output=True, text=True,
                          encoding='utf-8', errors='replace', timeout=300)
    assert done.returncode == 0 and 'COUPE : RIEN' in done.stdout, (done.stdout + done.stderr)[-4000:]


def cut_check(root):
    """Run in its own process (test above), with the Windows fonts."""
    import time
    from pathlib import Path as _Path
    from PySide6.QtGui import QFontInfo
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication as _Application
    from pokemind import seasons
    from pokemind.assistant.provider import ProviderAdapter
    application = _Application.instance() or _Application([])
    assert QFontInfo(idea_font()).family() == IDEA_FAMILY, QFontInfo(idea_font()).family()
    seasons.OFFICIAL = ()

    class Fake(ProviderAdapter):
        def health(self):
            return {'available': True, 'status': 'Invented provider'}

    report = {'as_of': '2026-10-25', 'model_version': 'battle-batch-v4', 'coverage': {'valid': 18},
              'outcomes': {'wins': 8, 'losses': 9, 'unknown': 1},
              'groups': [{'archetype': 'Famille inventée A', 'wins': 2, 'losses': 3, 'unknown': 0, 'n': 5}],
              'matches': [{'match': 'M0001', 'outcome': 'losses', 'opponent': {'label': 'Famille inventée A'},
                           'max_observed_turn': 7, 'evidence': [{'turn': 3, 'type': 'knockout',
                                                                 'text': 'Créature inventée mise K.O.'}]}],
              'persistence': {'status': 'BLOCKED_SCHEMA_NO_MIGRATION'}, 'recommendations': []}

    def load(services, update=False, **kwargs):
        services.report, services.learning = report, None
        return {'report': report, 'learning': None}
    window.Services.load = load
    window.Services.deck_options = lambda services: []
    window.CodexAppServer = window.ClaudeCode = Fake
    root = _Path(root) / 'cut'
    root.mkdir(parents=True, exist_ok=True)
    window.Store(root).write('preferences.json', {'cloud_consent': False, 'sharing': 'public', 'advanced_mode': True})
    ui = window.MainWindow(root)
    ui.show()

    def settle():
        end = time.monotonic() + 10
        while time.monotonic() < end and (ui.jobs or ui.stack.transition.isVisible()):
            application.processEvents()
            QTest.qWait(10)
        for _ in range(5):
            application.processEvents()
            QTest.qWait(10)

    settle()
    ui.loaded_decks([dict(label='Deck inventé du joueur', selector='synthetic', total=60, export='', source={},
                          opponent_rebuild=False, kind=window.T('Mon deck · référence personnelle enregistrée par le coach'),
                          legality=window.T('Standard / Live inconnus'))])
    ui.open_match('M0001')
    problems = []
    for size in SIZES:
        for theme in THEMES:
            ui.theme.setCurrentIndex(1 if theme == 'light' else 0)
            ui.resize(*size)
            for row in range(7):  # advanced mode: seven rows in the menu, the tallest it gets
                ui.navigation.setCurrentRow(row)
                settle()
                where = '%dx%d %s page %d' % (size + (theme, row))
                card = ui.active_deck
                if not card.isVisible() or card.compact != (size == (1100, 700)):
                    problems.append(where + ' : carte Deck actif (forme courte attendue à 1100 × 700 seulement)')
                for label in (card.name, card.detail, card.caption):
                    rows = label.rows(label.width())
                    if not rows or '…' in ''.join(rows) or label.height() < len(rows) * label.step():
                        problems.append(where + ' : carte coupée %r' % rows)
                if ui.navigation.verticalScrollBar().maximum():
                    problems.append(where + ' : le menu défile')
                for label in ui.findChildren(window.QLabel):
                    if (label.isVisible() and label.wordWrap() and label.heightForWidth(label.width()) > label.height()
                            and label.objectName() in ('tileCaption', 'tileValue', 'tileName', 'readingText')):
                        problems.append(where + ' : texte coupé %r' % label.text()[:50])
                for button in ui.findChildren(window.QPushButton):  # a button as wide as its words
                    if (button.isVisible() and button.text() and type(button) is window.QPushButton
                            and button.width() < button.sizeHint().width() - 1):
                        problems.append(where + ' : bouton coupé %r (%d < %d)' % (button.text(), button.width(),
                                                                                  button.sizeHint().width()))
    ui.close()
    ui.pool.waitForDone(5000)
    ui.image_pool.waitForDone(5000)
    print('\n'.join(problems) or 'COUPE : RIEN')
    sys.stdout.flush()
    os._exit(1 if problems else 0)  # no teardown: the window's threads are done, the process ends here
