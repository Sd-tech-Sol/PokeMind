"""The independent design study must never touch the real app or its data."""
import builtins
import importlib.util
from pathlib import Path
import socket
import sqlite3

import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import QCoreApplication, QEvent, QPointF, Qt
from PySide6.QtGui import QEnterEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

SOURCE=Path(__file__).resolve().parents[1]/'demos/premium_decklab/demo.py'
spec=importlib.util.spec_from_file_location('premium_decklab_demo',SOURCE)
demo=importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


@pytest.fixture
def demo_window(qt_application,monkeypatch):
    def forbidden(*args,**kwargs):
        pytest.fail('The demo must not use SQLite or a network socket')
    monkeypatch.setattr(sqlite3,'connect',forbidden)
    monkeypatch.setattr(socket,'create_connection',forbidden)
    monkeypatch.setattr(socket.socket,'connect',forbidden)
    real_open=builtins.open
    def safe_open(file,*args,**kwargs):
        if isinstance(file,(str,Path)):
            normalized=str(file).replace('\\','/').lower()
            assert '/data/local' not in normalized and '/appdata/local/pokemind' not in normalized
        return real_open(file,*args,**kwargs)
    monkeypatch.setattr(builtins,'open',safe_open)
    # Path.open uses io.open rather than builtins.open.
    import io
    monkeypatch.setattr(io,'open',safe_open)
    widget=demo.DemoWindow();widget.show();qt_application.processEvents()
    yield widget
    widget.close();widget.deleteLater()
    QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
    qt_application.processEvents()


def test_premium_demo_offline_window_has_six_original_illustrations_and_no_production_models(demo_window):
    ui=demo_window
    assert ui.isVisible() and len(ui.cards)==6 and ui.tabs.count()==3
    assert ui.selected_index==0 and ui.cards[0].selected
    assert all(not picture.isNull() for picture in ui.pictures)
    assert len({picture.toImage().pixelColor(200,200).rgba() for picture in ui.pictures})>=4
    assert not hasattr(ui,'services') and not hasattr(ui,'store') and not hasattr(ui,'root')


def test_premium_demo_real_hover_has_intermediate_frames_without_moving_neighbours(demo_window,qt_application):
    ui=demo_window;tile=ui.cards[1]
    bounds=[c.geometry() for c in ui.cards]
    tile.set_hover(0);normal=tile.grab().toImage()
    position=QPointF(tile.rect().center())
    QApplication.sendEvent(tile,QEnterEvent(position,position,position))
    assert tile.animation.duration()==220 and tile.animation.state()==tile.animation.State.Running
    tile.animation.setCurrentTime(90);mid=tile.grab().toImage()
    assert 0<tile.hover<1
    tile.animation.setCurrentTime(220);end=tile.grab().toImage()
    assert normal!=mid and mid!=end
    assert [c.geometry() for c in ui.cards]==bounds
    assert ui.selected_index==0  # hovering is independent of selection
    QApplication.sendEvent(tile,QEvent(QEvent.Type.Leave))
    tile.animation.setCurrentTime(220)
    assert tile.hover==0


def test_premium_demo_keyboard_selection_tabs_and_details_are_live(demo_window,qt_application):
    ui=demo_window
    ui.cards[0].setFocus();QTest.keyClick(ui.cards[0],Qt.Key.Key_Tab)
    assert ui.cards[1].hasFocus()
    QTest.keyClick(ui.cards[1],Qt.Key.Key_Space)
    assert ui.selected_index==1 and ui.details.currentIndex()==1
    assert sum(card.selected for card in ui.cards)==1
    ui.tabs.setCurrentIndex(2)
    assert ui.pages.currentIndex()==2 and ui.pages.transition.animation.duration()==180
    assert ui.pages.transition.isVisible()
    ui.tabs.setCurrentIndex(1)
    assert '60 cartes imaginaires' in ui.pages.currentWidget().toPlainText()


def test_premium_demo_reduced_motion_cancels_hover_transitions_and_replay(demo_window,qt_application):
    ui=demo_window
    ui.cards[1].animate(1);ui.select_card(2);ui.replay_effects()
    assert any(timer.isActive() for timer in ui.replay_timers)
    ui.reduced.setChecked(True)
    assert not ui.replay_timers
    for card in ui.cards:
        card.animate(1)
        assert card.hover==0 and card.animation.state()==card.animation.State.Stopped
    ui.tabs.setCurrentIndex(2);ui.select_card(4);ui.replay_effects()
    assert not ui.pages.transition.isVisible() and not ui.details.transition.isVisible()
    assert not ui.replay_timers and sum(card.selected for card in ui.cards)==1
    ui.reduced.setChecked(False);ui.replay_effects();ui.hide();qt_application.processEvents()
    assert not ui.replay_timers
    assert all(c.animation.state()==c.animation.State.Stopped for c in ui.cards)


@pytest.mark.parametrize('width',[1100,1500])
def test_premium_demo_layout_keeps_three_columns_and_readable_details(demo_window,qt_application,width):
    ui=demo_window;ui.resize(width,880);qt_application.processEvents()
    assert ui.gallery_scroll.horizontalScrollBar().maximum()==0
    assert ui.cards[0].y()==ui.cards[1].y()==ui.cards[2].y()
    assert ui.cards[0].x()==ui.cards[3].x()
    assert all(card.width()>=170 and card.height()>=278 for card in ui.cards)
    assert ui.details.width()>=200
    assert not ui.grab().isNull()
