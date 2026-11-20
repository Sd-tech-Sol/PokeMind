"""One bar everywhere and the pages' running text set like the Coach's idea buttons (owner, 2026-11-19)."""
import re

import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import QRectF, QUrl, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QTextDocument
from PySide6.QtWidgets import QLabel as NativeLabel, QTableWidget, QTableWidgetItem

from test_desktop_qt import app, ui  # noqa: F401
from pokemind.desktop import charts, widgets
from pokemind.desktop.insights import bar_url, learning_view
from pokemind.desktop.theme import (IDEA_FAMILY, IDEA_PADDING, IDEA_RADIUS, IDEA_SIZE, IDEA_WEIGHT, colors, contrast,
                                    idea_font, stylesheet)
from pokemind.desktop.widgets import (BAR_HEIGHT, CorpusChart, PageBrowser, RecordBarDelegate, bar_image, paint_bar,
                                      parse_bar_url)

THEMES = ('dark', 'light')


def bar(values, theme='dark', scale=None, reveal=1.0, width=200):
    image = QImage(width, BAR_HEIGHT, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    p = QPainter(image)
    paint_bar(p, QRectF(0, 0, width, BAR_HEIGHT), values, theme, scale=scale, reveal=reveal, track=False)
    p.end()
    return image


def near(color, role, theme='dark'):
    target = QColor(colors(theme)[role])
    return color.alpha() > 200 and max(abs(color.red() - target.red()), abs(color.green() - target.green()),
                                       abs(color.blue() - target.blue())) < 40


@pytest.mark.parametrize('theme', THEMES)
def test_the_bar_has_rounded_ends_a_gap_between_segments_and_the_theme_colours(app, theme):
    image = bar((2, 3, 1), theme)  # 200 px: wins 0–67, losses 67–167, unknown 167–200
    middle = BAR_HEIGHT // 2
    assert near(image.pixelColor(30, middle), 'blue', theme)
    assert near(image.pixelColor(117, middle), 'red', theme)
    assert near(image.pixelColor(185, middle), 'yellow', theme)
    assert image.pixelColor(0, 0).alpha() < 60 and image.pixelColor(199, BAR_HEIGHT - 1).alpha() < 60  # round ends
    assert near(image.pixelColor(2, middle), 'blue', theme)  # ... but the end itself is filled at mid-height
    assert image.pixelColor(67, middle).alpha() < 200  # the small gap at the join of wins and losses


def test_the_bar_compares_rows_grows_with_reveal_and_keeps_a_tiny_value_seen(app):
    half = bar((0, 3), scale=6)
    assert near(half.pixelColor(80, 5), 'red') and half.pixelColor(150, 5).alpha() == 0
    grown = bar((4,), reveal=.5)
    assert near(grown.pixelColor(80, 5), 'blue') and grown.pixelColor(150, 5).alpha() == 0
    tiny = bar((1, 300))
    assert tiny.pixelColor(0, 5).alpha() > 0 and tiny.pixelColor(0, 5).blue() > tiny.pixelColor(0, 5).red()
    assert bar(()).pixelColor(100, 5).alpha() == 0 and bar((0, 0, 0)).pixelColor(100, 5).alpha() == 0


def test_every_results_bar_of_the_pages_is_drawn_by_the_one_painter(app, monkeypatch):
    calls = []

    def spy(p, rect, values, theme, **kwargs):
        calls.append((rect.height(), tuple(values), kwargs.get('scale')))
        return paint_bar(p, rect, values, theme, **kwargs)
    monkeypatch.setattr(widgets, 'paint_bar', spy)
    monkeypatch.setattr(charts, 'paint_bar', spy)
    chart = CorpusChart()  # Overview › Bilan: losses by opponent deck
    chart.resize(700, 200)
    chart.set_motion_enabled(False)
    chart.set_report({'outcomes': {'wins': 1, 'losses': 3, 'unknown': 0},
                      'groups': [{'archetype': 'A', 'losses': 2, 'n': 3}, {'archetype': 'B', 'losses': 1, 'n': 1}]})
    chart.grab()
    assert calls == [(BAR_HEIGHT, (0, 2), 2), (BAR_HEIGHT, (0, 1), 2)]
    calls.clear()
    count = charts.CountChart(grouped=True)  # Opponents, Turns, Actions; Deck Lab › Statistics
    count.resize(700, 260)
    count.set_motion_enabled(False)
    count.set_rows([{'label': 'A', 'values': [1, 2, 0]}, {'label': 'B', 'values': [3, 0, 1]}])
    count.grab()
    assert calls == [(BAR_HEIGHT, (1, 2, 0), 4), (BAR_HEIGHT, (3, 0, 1), 4)]
    calls.clear()
    table = QTableWidget(1, 5)  # the Combats table
    table.setItemDelegateForColumn(4, RecordBarDelegate(table))
    for column, value in enumerate(('A', '2', '3', '1', '6')):
        table.setItem(0, column, QTableWidgetItem(value))
    table.resize(700, 120)
    table.setColumnWidth(4, 300)
    table.grab()
    assert calls and calls[0][:2] == (BAR_HEIGHT, (2, 3, 1)) and calls[0][2] is None
    for widget in (chart, count, table):
        widget.deleteLater()


@pytest.mark.parametrize('theme', THEMES)
def test_learning_bars_are_pictures_of_the_same_bar_in_the_page_theme(app, theme):
    learning = {'current': [{'kind': 'derived_statistic', 'recorded_at': '2026-11-16T10:00:00', 'payload': {
        'groups': [{'archetype': 'Famille inventée', 'wins': 1, 'losses': 2, 'n': 4}]}}]}
    text = str(learning_view(learning, colors(theme))[1])
    url = bar_url((1, 2, 1), colors(theme))
    assert url == 'pokemind-bar:' + theme + '/1-2-1/220' and '<img src="' + url + '"' in text
    assert 'bgcolor' not in text and 'font-size:7px' not in text  # the old square table cells are gone
    assert parse_bar_url(QUrl(url)) == (theme, (1, 2, 1), 220)
    assert parse_bar_url(QUrl('pokemind-bar:dark/x/1')) is None and parse_bar_url(QUrl('https://example.invalid/a')) is None
    page = PageBrowser()
    picture = page.loadResource(QTextDocument.ResourceType.ImageResource.value, QUrl(url))
    assert picture == bar_image((1, 2, 1), theme, 220)
    assert picture.devicePixelRatio() == 2 and picture.width() == 440  # sharp at 200 %
    page.deleteLater()


GRADIENT = 'background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {panel_start},stop:1 {panel_end})'


@pytest.mark.parametrize('theme', THEMES)
def test_reading_text_and_its_boxes_follow_the_coach_idea_buttons(theme):
    """The idea buttons' settings, and the page text and boxes that take them (owner, 2026-11-19)."""
    css, c = stylesheet(theme), colors(theme)
    def rule(selector):
        return re.search(r'(?m)^' + re.escape(selector) + r' \{([^}]*)\}', css).group(1)
    gradient = GRADIENT.format(**c)
    button, idea = rule('QPushButton'), rule('QWidget#chatBody QPushButton#chatIdea')
    assert gradient in button and 'border:1px solid ' + c['neon_soft'] in button
    every = rule('QWidget')  # their text is the default of every widget (owner, 2026-11-19)
    for part in ('font-family:"Segoe UI"', 'font-size:14px', 'font-weight:600', 'color:' + c['text']):
        assert part in every, part
    assert 'color:' + c['text'] in button and 'border-radius:10px' in idea and 'padding:9px 12px' in idea
    assert (IDEA_FAMILY, IDEA_SIZE, IDEA_WEIGHT, IDEA_RADIUS, IDEA_PADDING) == ('Segoe UI', 14, 600, 10, (9, 12))
    reading = rule('QLabel#readingText, QLabel[reading="text"]')
    assert 'color:' + c['text'] in reading and 'font' not in reading  # the face comes from the QWidget rule
    for frame in (rule('QFrame#textBubble'), rule('QTextBrowser#readingText')):
        assert gradient in frame and 'border:1px solid ' + c['neon_soft'] in frame and 'border-radius:10px' in frame
    assert 'border:1px solid ' + c['focus'] in rule('QTextBrowser#readingText:focus')  # focus still shows
    assert 'font' not in rule('QPushButton#homeLink')  # « Tes decks favoris », « Parties à reprendre »: the default
    assert 'font-size:28px' in rule('QLabel#tileValue') and 'font-size:28px' in rule('QLabel#title')  # unchanged
    for foreground in ('text', 'muted', 'link'):  # what a box holds, on both ends of its gradient
        for ground in ('panel_start', 'panel_end'):
            assert contrast(c[foreground], c[ground]) >= 4.5, (foreground, ground)


def test_the_bar_labels_take_the_idea_buttons_face():
    font = idea_font()
    assert font.families()[0] == 'Segoe UI' and font.pixelSize() == 14 and font.weight() == QFont.Weight.DemiBold


def test_the_pages_running_text_is_set_and_framed_like_the_coach_idea_buttons(ui, app):
    """Overview, Combats and Learning: the idea buttons' face, weight and colour, their kind of box, on the left."""
    from PySide6.QtWidgets import QFrame
    assert ui.matchup_story_box.objectName() == 'textBubble' and ui.learning_story_box.objectName() == 'textBubble'
    assert ui.overview.parentWidget().objectName() == 'textBubble'
    for view in (ui.dashboard_text, ui.battle_details, ui.memory_text):
        assert view.objectName() == 'readingText'
        view.ensurePolished()
        assert view.font().weight() == QFont.Weight.DemiBold and view.font().pixelSize() == 14
        view.setHtml('<h3>Titre</h3><p>Une phrase inventée.</p><ul><li>Un point inventé.</li></ul>')
        block = view.document().begin()
        assert block.begin().fragment().charFormat().fontWeight() == 700  # the headings stay bold
        while block.isValid():
            assert not block.blockFormat().alignment() & Qt.AlignmentFlag.AlignHCenter  # never centred
            block = block.next()
    for label in (ui.overview, ui.matchup_story, ui.learning_story, ui.home_focus):
        label.ensurePolished()
        assert label.font().weight() == QFont.Weight.DemiBold and label.font().pixelSize() == 14, label.objectName()
        assert not label.alignment() & Qt.AlignmentFlag.AlignHCenter
    shown = NativeLabel.text(ui.overview)  # what Qt lays out: one paragraph per line, no bubble line height
    assert shown.count('<p style') == ui.overview.text().count('\n') + 1 and 'line-height' not in shown
    # The light theme takes the same rules with its own colours.
    ui.theme.setCurrentIndex(1)
    app.processEvents()
    assert ui.overview.palette().color(ui.overview.foregroundRole()) == QColor(colors('light')['text'])
    assert isinstance(ui.matchup_story_box, QFrame)
    ui.theme.setCurrentIndex(0)
    app.processEvents()
