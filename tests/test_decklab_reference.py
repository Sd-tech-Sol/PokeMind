"""Reference adapter: no personal state, genuine Qt interactions and dock geometry."""
import builtins
import importlib.util
import io
from pathlib import Path
import socket
import sqlite3

import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import Qt, QEvent, QPointF, QCoreApplication
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import QApplication, QPushButton
from PySide6.QtTest import QTest

SOURCE = Path(__file__).resolve().parents[1] / 'demos/premium_decklab/reference.py'
spec = importlib.util.spec_from_file_location('decklab_reference', SOURCE)
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)


@pytest.fixture
def ui(qt_application, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Reference preview must not use SQLite or network')
    monkeypatch.setattr(sqlite3, 'connect', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    real_open = builtins.open
    def safe_open(file, *args, **kwargs):
        if isinstance(file, (str, Path)):
            normalized = str(file).replace('\\', '/').lower()
            assert '/data/local' not in normalized
            assert '/appdata/local/pokemind' not in normalized
        return real_open(file, *args, **kwargs)
    monkeypatch.setattr(builtins, 'open', safe_open)
    monkeypatch.setattr(io, 'open', safe_open)
    window = reference.ReferenceWindow()
    window.show()
    qt_application.processEvents()
    window.reflow()
    qt_application.processEvents()
    yield window
    window.close()
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qt_application.processEvents()


@pytest.mark.parametrize('width,height', [(1500, 970), (1100, 900)])
def test_decklab_reference_shell_and_responsive_gallery(ui, qt_application, width, height):
    ui.resize(width, height)
    qt_application.processEvents()
    ui.reflow()
    qt_application.processEvents()
    assert ui.size().width() == width and ui.height() == height
    assert ui.dockWidgetArea(ui.chat_dock) == Qt.DockWidgetArea.RightDockWidgetArea
    assert ui.chat_dock.width() >= 355
    assert [ui.navigation.item(i).text() for i in range(7)] == list(reference.NAVIGATION)
    assert ui.navigation.currentRow() == 2
    assert [ui.tabs.tabText(i) for i in range(3)] == ['Galerie · 60/60', 'Liste texte', 'Statistiques']
    assert ui.gallery_scroll.horizontalScrollBar().maximum() == 0
    assert ui.columns == (3 if width == 1500 else 2)
    assert len(ui.cards) % ui.columns == 0  # no lonely last card / empty row
    for tile in ui.tiles:
        assert tile.width() >= 190
    # Measured artwork width in DemoCard.paintEvent, compared to ~144 px in 003.
    for card in ui.cards:
        art_height = min(card.height()-32, (card.width()-30)*1.4)
        assert art_height / 1.4 >= 200
    assert not hasattr(ui, 'store') and not hasattr(ui, 'services') and not hasattr(ui, 'root')
    assert not ui.chat_input.isEnabled()
    assert all(not b.isEnabled() for b in ui.chat_dock.findChildren(QPushButton))
    assert not ui.grab().isNull()


def test_decklab_reference_polish_coach_and_titles_fit_at_1100(ui, qt_application):
    from PySide6.QtWidgets import QLabel
    ui.resize(1100, 900)
    QTest.qWait(50)
    assert ui.transcript.verticalScrollBar().maximum() == 0
    assert ui.transcript.horizontalScrollBar().maximum() == 0
    assert ui.gallery_scroll.horizontalScrollBar().maximum() == 0
    for tile in ui.tiles:
        title = tile.findChild(QLabel, 'cardCaption')
        subtitle = tile.findChild(QLabel, 'cardSubtitle')
        assert title.font().pixelSize() >= 17 and subtitle.font().pixelSize() >= 12
        assert max(title.fontMetrics().horizontalAdvance(word) for word in title.text().split()) <= title.contentsRect().width()
        assert title.height() >= title.heightForWidth(title.width())
    assert ui.hero.height() >= 90 and not ui.hero.scene.isNull()
    assert 'Aucune réponse IA simulée' in ' '.join(x.text() for x in ui.chat_dock.findChildren(QLabel))


def test_decklab_reference_real_motion_selection_and_keyboard(ui, qt_application):
    card = ui.cards[1]
    bounds = [c.geometry() for c in ui.cards]
    normal = card.grab().toImage()
    pos = QPointF(card.rect().center())
    QApplication.sendEvent(card, QEnterEvent(pos, pos, pos))
    card.animation.setCurrentTime(100)
    assert 0 < card.hover < 1
    intermediate = card.grab().toImage()
    card.animation.setCurrentTime(220)
    assert normal != intermediate and intermediate != card.grab().toImage()
    assert bounds == [c.geometry() for c in ui.cards]
    card.setFocus()
    QTest.keyClick(card, Qt.Key.Key_Space)
    assert ui.selected_index == ui.details.currentIndex() == 1
    assert sum(c.selected for c in ui.cards) == 1
    ui.tabs.setCurrentIndex(2)
    assert ui.pages.currentIndex() == 2 and ui.pages.transition.isVisible()
    assert 'Données insuffisantes' in ui.pages.currentWidget().toPlainText()
    ui.tabs.setCurrentIndex(0)
    ui.reduced.setChecked(True)
    card.animate(1)
    ui.select_card(3)
    assert card.hover == 0 and card.animation.state() == card.animation.State.Stopped
    assert not ui.details.transition.isVisible() and not ui.pages.transition.isVisible()
    ui.reduced.setChecked(False)
    card.animate(1)
    ui.hide()
    qt_application.processEvents()
    assert all(c.animation.state() == c.animation.State.Stopped for c in ui.cards)


def test_decklab_reference_text_contrast():
    from pokemind.desktop.theme import contrast
    for foreground in ('text', 'muted', 'accent', 'blue'):
        for background in ('background', 'sidebar', 'surface', 'input'):
            assert contrast(reference.C[foreground], reference.C[background]) >= 4.5


@pytest.mark.parametrize('width,height', [(1500, 970), (1100, 900)])
def test_finish_safe_banner_and_contextual_details(ui, qt_application, width, height):
    from PySide6.QtCore import QRectF
    from PySide6.QtWidgets import QLabel
    ui.resize(width, height)
    QTest.qWait(50)
    art = ui.hero.art_rect()
    assert QRectF(ui.hero.rect()).adjusted(5, 5, -5, -5).contains(art)
    assert art.width()/art.height() == pytest.approx(ui.hero.sprite.width()/ui.hero.sprite.height())
    for text in ui.hero.findChildren(QLabel):
        assert not QRectF(text.geometry()).intersects(art)
        assert text.height() >= text.heightForWidth(text.width())
    assert ui.deck_picker.parentWidget() is not ui.hero
    assert not ui.details.isVisible()
    viewport_height = ui.gallery_scroll.viewport().height()
    scroll_position = ui.gallery_scroll.verticalScrollBar().value()
    QTest.mouseClick(ui.cards[1], Qt.MouseButton.LeftButton)
    assert ui.selected_index == 1 and 'Flamaris' in ui.detail_toggle.text()
    ui.detail_toggle.setFocus()
    assert ui.detail_toggle.hasFocus()
    QTest.keyClick(ui.detail_toggle, Qt.Key.Key_Tab)
    QTest.keyClick(qt_application.focusWidget(), Qt.Key.Key_Backtab)
    assert ui.detail_toggle.hasFocus()
    QTest.keyClick(ui.detail_toggle, Qt.Key.Key_Space)
    QTest.qWait(30)
    assert ui.details.isVisible() and ui.details.currentIndex() == 1
    assert ui.gallery_scroll.viewport().height() < viewport_height
    for text in ui.details.currentWidget().findChildren(QLabel):
        assert text.height() >= text.heightForWidth(text.width())
    QTest.mouseClick(ui.detail_toggle, Qt.MouseButton.LeftButton)
    QTest.qWait(30)
    assert not ui.details.isVisible()
    assert ui.gallery_scroll.viewport().height() == viewport_height
    assert ui.gallery_scroll.verticalScrollBar().value() == scroll_position
    assert ui.gallery_scroll.horizontalScrollBar().maximum() == 0
    bar = ui.gallery_scroll.verticalScrollBar()
    bar.setValue(bar.maximum())
    last = ui.tiles[-1]
    position = last.mapTo(ui.gallery_scroll.viewport(), last.rect().bottomRight())
    assert 0 < position.y() <= viewport_height


@pytest.mark.parametrize('width,height', [(1500, 970), (1100, 900)])
def test_finish_larger_labels_and_coach_empty_state(ui, qt_application, width, height):
    from PySide6.QtWidgets import QLabel
    ui.setStyleSheet(ui.styleSheet() +
        'QLabel#cardCaption {font-size:20px;} QLabel#cardSubtitle {font-size:16px;}'
        'QLabel#coachDescription {font-size:15px;}')
    ui.resize(width, height)
    QTest.qWait(60)
    assert ui.width() == width and ui.height() == height
    assert ui.transcript.verticalScrollBar().maximum() == 0
    assert ui.transcript.horizontalScrollBar().maximum() == 0
    assert ui.gallery_scroll.horizontalScrollBar().maximum() == 0
    for widget in ui.chat_dock.findChildren(QLabel):
        if widget.isVisible() and widget.wordWrap():
            assert widget.height() >= widget.heightForWidth(widget.width())
            assert ui.chat_dock.rect().contains(widget.mapTo(ui.chat_dock, widget.rect().bottomRight()))
    for tile in ui.tiles:
        for name in ('cardCaption', 'cardSubtitle'):
            text = tile.findChild(QLabel, name)
            assert text.height() >= text.heightForWidth(text.width())
