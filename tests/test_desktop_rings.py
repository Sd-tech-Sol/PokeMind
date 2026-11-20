"""Results rings of the Overview and the Active deck card: drawn counts only, never a percentage."""
import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QImage, QPainter
from test_desktop_qt import app  # noqa: F401
from pokemind.desktop.theme import colors
from pokemind.desktop.widgets import ActiveDeckCard, CorpusChart, RecordRing, arc_point, games_word, paint_donut


def ring_image(values, theme='dark', reveal=1.0):
    image = QImage(200, 200, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(QColor(colors(theme)['surface']))
    p = QPainter(image)
    paint_donut(p, QRectF(40, 40, 120, 120), values, theme, stroke=24, reveal=reveal, number=sum(values),
                label=games_word(sum(values)))
    p.end()
    return image


def near(color, role, theme='dark'):
    target = QColor(colors(theme)[role])
    return max(abs(color.red() - target.red()), abs(color.green() - target.green()), abs(color.blue() - target.blue())) < 70


def test_ring_has_its_segments_a_gap_between_them_and_a_number_in_the_middle(app):
    image = ring_image((8, 9, 1))
    rect = QRectF(40, 40, 120, 120)
    # Wins start at the top and run clockwise: a little past the top is blue, the top itself is the gap.
    top = arc_point(rect, 90).toPoint()
    assert not near(image.pixelColor(top), 'blue') and not near(image.pixelColor(top), 'red')
    assert near(image.pixelColor(arc_point(rect, 20).toPoint()), 'blue')
    assert near(image.pixelColor(arc_point(rect, 200).toPoint()), 'red')
    centre = image.pixelColor(100, 85)  # the large number, in the text colour
    assert centre != QColor(colors('dark')['surface'])


def test_ring_fill_is_animated_on_opening_and_at_once_with_reduced_motion(app):
    ring = RecordRing()
    ring.show()
    ring.set_values((2, 1, 0))
    assert ring.fill.animation.state() == ring.fill.animation.State.Running and ring.reveal < 1
    ring.set_motion_enabled(False)
    assert ring.reveal == 1.0
    ring.set_values((3, 1, 0))
    assert ring.reveal == 1.0 and ring.fill.animation.state() != ring.fill.animation.State.Running
    half = ring_image((2, 1, 0), reveal=.5)
    rect = QRectF(40, 40, 120, 120)
    assert not near(half.pixelColor(arc_point(rect, 200).toPoint()), 'red')  # half filled: not yet the losses
    ring.close()


def test_rings_say_games_with_the_right_number_and_the_counts_under_them(app):
    assert str(games_word(1)) == 'partie' and str(games_word(18)) == 'parties'
    card = ActiveDeckCard()
    card.set_record({'wins': 8, 'losses': 9, 'unknown': 1})
    assert '8 V · 9 D · 1 sans résultat' in card.caption.text() and '%' not in card.caption.text()
    chart = CorpusChart()
    chart.set_motion_enabled(False)
    chart.set_report({'outcomes': {'wins': 1, 'losses': 0, 'unknown': 0}, 'groups': []})
    assert chart.reveal == 1.0
    card.deleteLater()
    chart.deleteLater()
