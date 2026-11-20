"""Local, code-drawn styling: deep blue panels with neon lines; no downloaded artwork or fonts.
The brand card is bundled (branding/)."""
import os
import tempfile
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QDir, Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QFont, QGuiApplication, QIcon, QImage, QPainter, QPainterPath, QPen, QPixmap, QPalette


# BrainBall electric (owner, 2026-11-05): docs/design/pokemind-brainball/palette.json is the source of truth.
# Its tokens are copied here unchanged; the few derived tokens are marked and checked by the tests.
BRAND = dict(bleu_nuit='#001261', bleu_royal='#01339F', bleu_electrique='#004CCB', bleu_lumineux='#0793FA',
             cyan='#68D6F9', gold='#FECF4D', rouge_cerveau='#EE4B50', rouge_profond='#C32039', blanc_nacre='#FEFCFA')

PALETTES = {
    'dark': dict(background='#030A1F', sidebar='#06163A', surface='#0A1B41', alternate='#12305F', input='#050F2A',
                 text='#F7FAFF', muted='#C3D8F4', border='#335A8E', hover='#1B4380', accent='#FFD54F',
                 primary='#0054C7', primary_hover='#074DB4', on_primary='#FFFFFF', link='#6FD5FF', focus='#FFDD5D',
                 red='#FF6B74', blue='#68BFFF', yellow='#FFD54F', success='#62D1B3', warning='#FFE493',
                 warning_bg='#392F24', selection='#0054C7', selection_text='#FFFFFF', hero_start='#00339F',
                 hero_end='#004CCB', hero_text='#FFFFFF', hero_kicker='#FFD54F', danger='#B72C43', on_danger='#FFFFFF',
                 neutral_chart='#90A9CF',
                 # derived
                 primary_pressed='#003F96', hero_muted='#DCE8FF', hero_border='#0793FA', nav_icon_selected='#FFD54F',
                 tooltip='#06163A', tooltip_text='#F7FAFF', tooltip_border='#FFD54F', overlay='rgba(3,10,31,0.94)',
                 field_border='#4F79B0',
                 # derived, premium look: neon lines from the brand blues, panels as a soft vertical gradient
                 neon='#0793FA', neon_hi='#68D6F9', neon_soft='#2A6FD6', panel_start='#0D2250', panel_end='#071532',
                 primary_glow='#0A6BE0'),
    'light': dict(background='#F1F7FF', sidebar='#E0EDFF', surface='#FFFFFF', alternate='#E6F0FF', input='#F8FBFF',
                  text='#081B3A', muted='#425778', border='#B7CBE7', hover='#D6E9FF', accent='#003EA6',
                  primary='#003EA6', primary_hover='#003A9E', on_primary='#FFFFFF', link='#004CCB', focus='#004CCB',
                  red='#B72C43', blue='#004CCB', yellow='#735100', success='#116C4D', warning='#704C00',
                  warning_bg='#FFF3D0', selection='#C6E2FF', selection_text='#081B3A', hero_start='#01339F',
                  hero_end='#004CCB', hero_text='#FFFFFF', hero_kicker='#FFD54F', danger='#B72C43', on_danger='#FFFFFF',
                  neutral_chart='#576A88',
                  # derived
                  primary_pressed='#002E7A', hero_muted='#DCE8FF', hero_border='#0793FA', nav_icon_selected='#FFFFFF',
                  tooltip='#FFFFFF', tooltip_text='#081B3A', tooltip_border='#004CCB', overlay='rgba(255,255,255,0.96)',
                  field_border='#7088AD',
                  # derived, premium look
                  neon='#0A6BE0', neon_hi='#0793FA', neon_soft='#5B93DE', panel_start='#FFFFFF', panel_end='#EEF5FF',
                  primary_glow='#0A5AD6'),
}
DERIVED = ('primary_pressed', 'hero_muted', 'hero_border', 'nav_icon_selected', 'tooltip', 'tooltip_text',
           'tooltip_border', 'overlay',
           'field_border',  # palette.json borders are decorative (under 3:1 around inputs); fields get this one
           # Premium look (owner, 2026-11-16): `neon` marks what is selected or hovered, `neon_hi` edges the filled
           # blue controls, `neon_soft` outlines panels and buttons at rest; panels and buttons are a vertical
           # gradient from `panel_start` to `panel_end`; `primary_glow` is the lit end of a primary fill.
           'neon', 'neon_hi', 'neon_soft', 'panel_start', 'panel_end', 'primary_glow',
           # One lit outline per panel (owner, 2026-11-18): a frame inside a panel is the surface colour with this
           # quiet line, `neon` laid at 30 % over `surface`. Decorative: the fill already separates the frame.
           'inner_line')
INNER_LINE_ALPHA = .30


def _over(color, ground, alpha):
    """`color` laid at `alpha` over `ground`, as one opaque colour (style sheets and painters read the same)."""
    top, low = QColor(color), QColor(ground)
    mixed = [round(a * alpha + b * (1 - alpha)) for a, b in zip(top.getRgb()[:3], low.getRgb()[:3])]
    return '#%02X%02X%02X' % tuple(mixed)


for _palette in PALETTES.values():
    _palette['inner_line'] = _over(_palette['neon'], _palette['surface'], INNER_LINE_ALPHA)
# The same in both themes: the binder is a physical object (royal blue cover, navy pages, so the sleeves and the
# card names keep their contrast), and the terminal stays dark because console programs pick their ANSI colours
# for a dark background.
OBJECTS = dict(binder_start='#01339F', binder_end='#001261', binder_border='#0793FA', page_start='#132E63',
               page_end='#0B1D42', page_border='#06122B', spine_edge='#001261', spine_mid='#004CCB',
               terminal='#081C3E', terminal_text='#F7FAFF', gold_line='#FECF4D')


def colors(theme):
    return PALETTES['light' if theme == 'light' else 'dark']


# The Coach's idea buttons (« Fais-moi le bilan de ma saison en 5 points »…), whose text is the default of the
# whole application and whose boxes the pages' running text takes (owner, 2026-11-19). Measured on the buttons
# (QPushButton, QWidget#chatBody QPushButton,
# QPushButton#chatIdea and WrapPushButton): « Segoe UI » (the application face), 14 px, semibold (600), colour
# `text` (#F7FAFF dark, #081B3A light: the same token as the other text, at full opacity: the semibold strokes on
# the gradient make it read a little softer), a vertical `panel_start` → `panel_end` gradient, a 1 px `neon_soft`
# line, 10 px corners, 9 px × 12 px inside; the words centred (a button) — the pages keep theirs on the left.
IDEA_FAMILY, IDEA_SIZE, IDEA_WEIGHT = 'Segoe UI', 14, 600
IDEA_RADIUS, IDEA_PADDING = 10, (9, 12)       # px: corners; inside, top/bottom × left/right


def idea_font(base=None):
    """The idea buttons' face: the default text of the whole application (owner, 2026-11-19, « le MÊME style
    PARTOUT »). The style sheet gives it to every widget (QWidget rule), the application font to what it does not
    reach, and every painter that draws words takes it from here."""
    font = QFont(base) if base is not None else QFont()
    font.setFamilies([IDEA_FAMILY])
    font.setPixelSize(IDEA_SIZE)
    font.setWeight(QFont.Weight.DemiBold)
    return font


# The only text that is not set like the idea buttons (owner, 2026-11-19): the titles of the pages and of their
# sections, and the large numbers of the tiles and the rings. Same face, their own size and weight. By object
# name; the tests read this list. (The wordmark of the menu, the title of the loading banner, the deck shown in
# Deck Lab and the discussion's name in the Coach are titles; the rival's name stands in the tile where the other
# tiles have their number; `statValue` is the large number of the public statistics.)
TITLE_NAMES = ('title', 'brand', 'heroTitle', 'sectionTitle', 'gallerySection', 'loadingTitle', 'deckTitle', 'chatTitle',
               'tileValue', 'tileName', 'statValue')


def apply_application_font(application=None):
    """The idea buttons' face as the application font: dialogs, menus and painters outside the style sheet."""
    application = application or QGuiApplication.instance()
    if application is not None:
        application.setFont(idea_font())


def theme_of(widget_palette):
    """'light' or 'dark' from a widget's palette, for painters that are not told the theme."""
    return 'light' if widget_palette.color(QPalette.ColorRole.Window).lightness() > 128 else 'dark'


def _channel(value):
    value /= 255
    return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4


def luminance(color):
    value = QColor(color)
    return 0.2126 * _channel(value.red()) + 0.7152 * _channel(value.green()) + 0.0722 * _channel(value.blue())


def contrast(foreground, background):
    """WCAG 2 contrast ratio of two opaque colours."""
    high, low = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def palette(theme):
    c = colors(theme)
    value = QPalette()
    for role, color in ((QPalette.ColorRole.Window, c['background']),
                        (QPalette.ColorRole.Base, c['input']),
                        (QPalette.ColorRole.AlternateBase, c['alternate']),
                        (QPalette.ColorRole.WindowText, c['text']),
                        (QPalette.ColorRole.Text, c['text']),
                        (QPalette.ColorRole.Button, c['surface']),
                        (QPalette.ColorRole.ButtonText, c['text']),
                        (QPalette.ColorRole.PlaceholderText, c['muted']),
                        (QPalette.ColorRole.Mid, c['border']),
                        (QPalette.ColorRole.Link, c['link']),
                        (QPalette.ColorRole.ToolTipBase, c['tooltip']),
                        (QPalette.ColorRole.ToolTipText, c['tooltip_text']),
                        (QPalette.ColorRole.Highlight, c['selection']),
                        (QPalette.ColorRole.HighlightedText, c['selection_text'])):
        value.setColor(role, QColor(color))
    return value


ARROWS = 'pokemind-theme'  # Qt search-path prefix of the drawn combo-box chevrons


def _chevron(color, up=False):
    """A chevron PNG in the theme colour, drawn once into a temporary folder that Qt reads as 'pokemind-theme:'.
    The native drop-down button paints a dark edge on the themed combo boxes; this replaces it."""
    folder = Path(tempfile.gettempdir()) / ARROWS
    name = 'chevron-%s-%s.png' % (color.lstrip('#').lower(), 'up' if up else 'down')
    if not (folder / name).is_file():
        folder.mkdir(parents=True, exist_ok=True)
        image = QImage(20, 12, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(0)
        p = QPainter(image)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(color), 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        ends = (9, 3) if up else (3, 9)
        p.drawPolyline([QPointF(3, ends[0]), QPointF(10, ends[1]), QPointF(17, ends[0])])
        p.end()
        temporary = folder / ('%s.%d.tmp.png' % (name, os.getpid()))
        if not image.save(str(temporary)):
            raise OSError('chevron not written')
        os.replace(temporary, folder / name)
    QDir.addSearchPath(ARROWS, str(folder))
    return ARROWS + ':' + name


def _check_mark(color):
    """The tick of a checked box, in the theme colour, kept beside the chevrons."""
    folder = Path(tempfile.gettempdir()) / ARROWS
    name = 'check-%s.png' % color.lstrip('#').lower()
    if not (folder / name).is_file():
        folder.mkdir(parents=True, exist_ok=True)
        image = QImage(32, 32, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(0)
        p = QPainter(image)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(color), 4.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.drawPolyline([QPointF(7, 17), QPointF(13.5, 23), QPointF(25, 9)])
        p.end()
        temporary = folder / ('%s.%d.tmp.png' % (name, os.getpid()))
        if not image.save(str(temporary)):
            raise OSError('check mark not written')
        os.replace(temporary, folder / name)
    QDir.addSearchPath(ARROWS, str(folder))
    return ARROWS + ':' + name


def _check_boxes(c):
    """An empty box has a visible edge (it was almost invisible on the dark theme: owner, 2026-11-16)."""
    try:
        tick = 'image:url(' + _check_mark(c['on_primary']) + '); '
    except OSError:
        tick = ''  # a filled box still reads as checked
    return ('QCheckBox::indicator { width:16px; height:16px; border:2px solid ' + c['field_border'] + '; border-radius:5px; '
            'background:' + c['input'] + '; }\n'
            'QCheckBox::indicator:hover { border-color:' + c['neon'] + '; }\n'
            'QCheckBox::indicator:checked { ' + tick + 'background:' + c['primary'] + '; border-color:' + c['neon_hi'] + '; }\n'
            'QCheckBox::indicator:disabled { border-color:' + c['border'] + '; }\n')


def apply_color_scheme(theme):
    """The Windows title bar and the native dialogs follow the theme chosen in PokeMind, not the system's:
    a white caption above the dark application looked foreign (owner, 2026-11-16). Qt 6.8 or later."""
    application = QGuiApplication.instance()
    hints = application.styleHints() if application is not None else None
    if hints is not None and hasattr(hints, 'setColorScheme'):
        hints.setColorScheme(Qt.ColorScheme.Dark if theme == 'dark' else Qt.ColorScheme.Light)


def _combo_arrows(c):
    try:
        down, up, off = _chevron(c['muted']), _chevron(c['muted'], up=True), _chevron(c['border'])
    except OSError:
        return ''  # the native arrow stays
    return ('QComboBox::drop-down { subcontrol-origin:padding; subcontrol-position:center right; width:26px; '
            'border:0; background:transparent; }\n'
            'QComboBox::down-arrow { image:url(' + down + '); width:10px; height:6px; }\n'
            'QComboBox::down-arrow:on { image:url(' + up + '); }\n'
            'QComboBox::down-arrow:disabled { image:url(' + off + '); }\n')


def _header_arrows(c):
    """The sort arrow of a table header, centred above the header text as in Windows Explorer: the native arrow
    was drawn over a right-aligned header (« D▾ »: owner, 2026-11-18), and the text keeps its alignment with
    the column. (An arrow image placed at the right made Qt drop the text of the sorted column.)"""
    try:
        down, up = _chevron(c['muted']), _chevron(c['muted'], up=True)
    except OSError:
        return ('QHeaderView::up-arrow,QHeaderView::down-arrow { width:10px; height:6px; '
                'subcontrol-position:top center; }\n')
    return ('QHeaderView::up-arrow { image:url(' + up + '); width:10px; height:6px; subcontrol-position:top center; }\n'
            'QHeaderView::down-arrow { image:url(' + down + '); width:10px; height:6px; subcontrol-position:top center; }\n')


def stylesheet(theme):
    c = dict(OBJECTS, **colors(theme))
    template = '''
QWidget { background:@background; color:@text; font-family:"Segoe UI"; font-size:14px; font-weight:600; }
QMainWindow,QStackedWidget { background:@background; }
QTabWidget > QStackedWidget { background:transparent; }
QMainWindow::separator { background:transparent; width:5px; height:5px; }
QMainWindow::separator:hover { background:@neon; }
QWidget#motionOverlay { background:transparent; border:0; }
QLabel { background:transparent; }
QLabel#title { font-size:28px; font-weight:800; }
QLabel#muted { color:@muted; }
QFrame#sidebar { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 @sidebar,stop:1 @background); border-right:1px solid @neon_soft; }
QFrame#sidebar QLabel#brand { color:@accent; font-size:25px; font-weight:800; }
QFrame#sidebar QLabel#brandCaption { color:@muted; }
QFrame#activeDeck, QFrame#activeDeck QWidget { background:transparent; }
QFrame#sidebar QLabel#activeDeckTitle { color:@accent; }
QLabel#deckCover { background:@input; color:@muted; border:1px solid @inner_line; border-radius:5px; }
QComboBox#deckSwitch { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 @panel_start,stop:1 @panel_end); color:@text; border:1px solid @neon_soft; border-radius:12px; padding:5px 24px 5px 14px; min-height:24px; }
QComboBox#deckSwitch:hover { background:@hover; border-color:@neon; }
QFrame#sidebar QLabel#activeDeckCover { background:@input; color:@muted; border:1px solid @neon_soft; border-radius:6px; }
QListWidget { background:@sidebar; color:@text; border:0; padding:0; outline:0; }
QFrame#sidebar QListWidget { background:transparent; }
QListWidget::item { padding:11px 10px; border-radius:12px; margin:3px 0; border:1px solid transparent; }
QListWidget::item:hover { background:@hover; border:1px solid @neon_soft; }
QListWidget::item:selected { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 @primary,stop:1 @primary_glow); color:@on_primary; border:1px solid @neon_hi; }
QListWidget::item:focus { border:1px solid @focus; }
QFrame#hero { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 @hero_start,stop:1 @hero_end); border:1px solid @inner_line; border-radius:18px; }
QFrame#hero QLabel { color:@hero_text; }
QFrame#hero QLabel#heroKicker { color:@hero_kicker; }
QLabel#heroTitle { font-size:24px; font-weight:800; }
QLabel#heroDescription { color:@hero_muted; }
QFrame#card { background:@surface; border:1px solid @inner_line; border-radius:16px; }
QFrame#card[metricKind="games"] { border-top:3px solid @neutral_chart; }
QFrame#card[metricKind="wins"] { border-top:3px solid @blue; }
QFrame#card[metricKind="losses"] { border-top:3px solid @red; }
QFrame#card[metricKind="rival"] { border-top:3px solid @yellow; }
QFrame#card[metricKind="plans"] { border-top:3px solid @yellow; }
QFrame#card[metricKind="plans"] QLabel#tileValue { color:@yellow; }
QFrame#card QLabel { background:transparent; }
QFrame#textBubble { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 @panel_start,stop:1 @panel_end); border:1px solid @neon_soft; border-radius:10px; }
QFrame#textBubble QLabel { background:transparent; }
QLabel#readingText, QLabel[reading="text"] { color:@text; }
QTextBrowser#readingText { color:@text; background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 @panel_start,stop:1 @panel_end); border:1px solid @neon_soft; border-radius:10px; padding:5px 8px; }
QTextBrowser#readingText:focus { border:1px solid @focus; }
QLabel#sectionTitle { font-size:18px; font-weight:700; color:@text; }
QLabel#smallCaption { color:@muted; }
QLabel#tileCaption { color:@text; }
QPushButton#sidebarToggle { background:transparent; color:@accent; border:1px solid @neon_soft; padding:6px; }
QPushButton#sidebarToggle:hover { background:@hover; border-color:@neon; }
QPushButton#favoriteButton:checked { color:@yellow; border-color:@yellow; background:@alternate; }
QPushButton#homeLink { text-align:left; padding:6px 10px; border-radius:10px; }
QPushButton#sourceToggle { padding:6px; }
QLabel#battleBadge { color:@text; background:@surface; border:1px solid @inner_line; border-left:4px solid @blue; border-radius:12px; padding:10px 14px; }
QLabel#tileValue { font-size:28px; font-weight:800; color:@accent; }
QFrame#card[metricKind="games"] QLabel#tileValue { color:@text; }
QFrame#card[metricKind="wins"] QLabel#tileValue { color:@blue; }
QFrame#card[metricKind="losses"] QLabel#tileValue { color:@red; }
QLabel#tileName { font-size:16px; font-weight:700; color:@yellow; }
QLabel#statValue { font-size:32px; font-weight:700; }
QLabel#corpusNote { color:@warning; padding:12px; background:@warning_bg; border:1px solid @border; border-radius:12px; }
QLabel[cardType="pokemon"] { color:@red; }
QLabel[cardType="trainer"] { color:@blue; }
QLabel[cardType="energy"] { color:@yellow; }
QScrollArea#deckGallery { background:@background; border:0; }
QScrollArea#deckGallery QFrame#card[galleryTile="true"] { background:transparent; border:2px solid transparent; border-radius:12px; }
QScrollArea#deckGallery QFrame#card[selected="true"] { border-color:@focus; background:@surface; }
QScrollArea#deckGallery QFrame#card QLabel#countBadge { background:transparent; color:@text; border:0; padding:2px 11px; }
QWidget#deckLabPage > QLabel#title, QWidget#deckLabPage > QLabel#muted { background:transparent; }
QLabel#gallerySection { color:@text; font-size:17px; font-weight:700; padding:5px 0; border-bottom:1px solid @blue; }
QLabel#galleryCardName { color:@text; }
QLabel#galleryStamp { color:@muted; }
QScrollArea#deckGallery QPushButton#cardArt { background:transparent; border:0; border-radius:10px; padding:0; }
QScrollArea#deckGallery QPushButton#cardArt[pictured="false"] { background:@input; border:1px solid @inner_line; }
QScrollArea#deckGallery QPushButton#cardArt:focus { border:1px solid @focus; padding:0; }
QScrollArea#deckGallery QPushButton#cardArt:pressed { background:@alternate; }
QTextEdit,QTextBrowser,QLineEdit,QComboBox,QTableWidget { background:@input; color:@text; border:1px solid @border; border-radius:12px; padding:9px; selection-background-color:@selection; selection-color:@selection_text; }
QTextEdit,QLineEdit,QComboBox { border-color:@field_border; }
QTextBrowser,QTableWidget { border-color:@inner_line; }
QLineEdit:hover,QComboBox:hover { border-color:@neon; }
QTextEdit:focus,QTextBrowser:focus,QLineEdit:focus,QComboBox:focus,QTableWidget:focus { border:1px solid @focus; }
QLineEdit { min-height:25px; }
QComboBox { min-height:24px; padding-right:24px; }
QComboBox QAbstractItemView { background:@surface; color:@text; selection-background-color:@selection; selection-color:@selection_text; border:1px solid @neon_soft; padding:4px; outline:0; }
QComboBox QAbstractItemView::item { color:@text; background:@surface; padding:7px 10px; min-height:22px; border-radius:6px; }
QComboBox QAbstractItemView::item:hover { color:@text; background:@hover; }
QComboBox QAbstractItemView::item:selected { color:@selection_text; background:@selection; }
QPushButton { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 @panel_start,stop:1 @panel_end); color:@text; border:1px solid @neon_soft; border-radius:12px; padding:6px 14px; min-height:22px; }
QPushButton:hover { background:@hover; border-color:@neon; }
QPushButton:pressed { background:@alternate; }
QPushButton:focus { border:2px solid @focus; padding:5px 13px; }
QPushButton#primary { background:@primary; color:@on_primary; border:1px solid @neon_hi; }
QPushButton#primary:hover { background:@primary_glow; border-color:@focus; }
QPushButton#compact { padding:6px 8px; }
QPushButton#compact:focus { padding:5px 7px; }
QPushButton#primary:pressed { background:@primary_pressed; }
QPushButton[destructive="true"] { color:@red; }
QPushButton[destructive="true"]:hover { background:@danger; color:@on_danger; border-color:@danger; }
QPushButton:disabled { background:@alternate; color:@muted; border:1px solid @border; }
QPushButton#primary:disabled,QPushButton[destructive="true"]:disabled { background:@alternate; color:@muted; border:1px solid @border; }
QHeaderView { background:transparent; }
QHeaderView::section { background:transparent; color:@text; border:0; border-bottom:1px solid @neon_soft; padding:9px 8px; }
QTableWidget { gridline-color:@inner_line; alternate-background-color:@alternate; selection-background-color:@hover; selection-color:@text; }
QTableWidget::item { padding:0 8px; border:0; border-bottom:1px solid @inner_line; }
QTableWidget::item:hover { background:@alternate; }
QTableWidget::item:selected { background:@hover; color:@text; }
QTabWidget::pane { border:0; border-top:1px solid @border; }
QTabBar { background:transparent; }
QTabBar::tab { background:transparent; color:@text; padding:10px 14px; margin-right:4px; border:0; border-bottom:3px solid transparent; }
QTabBar::tab:hover { color:@text; border-bottom:3px solid @neon_soft; }
QTabBar::tab:selected { color:@link; border-bottom:3px solid @neon; }
QDockWidget::title { background:@sidebar; color:@accent; padding:12px; }
QWidget#chatBody QComboBox { padding:5px 8px; min-height:20px; }
QWidget#chatBody QPushButton { padding:7px 10px; }
QWidget#chatBody QPushButton#chatMenu { padding:6px 12px; }
QWidget#chatBody QPushButton#chatMenu::menu-indicator { image:none; width:0; }
QFrame#chatEmpty { background:@input; border:1px solid @inner_line; border-radius:12px; }
QFrame#chatEmpty QLabel { background:transparent; }
QWidget#chatBody QPushButton#chatIdea { text-align:left; padding:9px 12px; border-radius:10px; }
QCheckBox { spacing:8px; padding:6px; }
QProgressBar { background:@alternate; border:0; border-radius:4px; }
QProgressBar::chunk { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 @neon,stop:1 @neon_hi); border-radius:4px; }
QTextBrowser#chatTranscript { padding:2px; }
QFrame#loadingBanner { background:@alternate; border:0; border-bottom:3px solid @blue; }
QFrame#loadingBanner QLabel { background:transparent; }
QFrame#loadingBanner QProgressBar { background:@surface; }
QFrame#updateBanner { background:@alternate; border:0; border-bottom:3px solid @success; }
QFrame#updateBanner QLabel { background:transparent; }
QFrame#updateBanner QProgressBar { background:@surface; }
QLabel#loadingTitle { color:@text; font-size:17px; font-weight:800; }
QLabel#loadingDetail { color:@muted; }
QFrame#activityCard { background:transparent; border:1px solid transparent; border-radius:12px; }
QFrame#activityCard[busy="true"] { background:@surface; border:1px solid @inner_line; }
QLabel#activityLabel { color:@muted; }
QLabel#activityLabel[busy="true"] { color:@text; }
QLabel#activityClock { color:@muted; }
QLabel#activityClock[busy="true"] { color:@muted; background:@alternate; border:1px solid @border; border-radius:9px; padding:2px 9px; }
QLabel#permissionBadge { color:@warning; background:@warning_bg; border:1px solid @yellow; border-radius:10px; padding:3px 9px; }
QLabel#chatNotice { color:@warning; background:@warning_bg; border-radius:9px; padding:5px 9px; }
QPushButton#chatExpand { background:transparent; color:@accent; border:1px solid @neon_soft; border-radius:9px; padding:3px 10px; }
QPushButton#chatExpand:hover { background:@hover; }
QFrame#settingRow { background:@surface; border:1px solid @inner_line; border-radius:13px; }
QFrame#settingRow QLabel { background:transparent; }
QFrame#settingRow QCheckBox { background:transparent; padding:2px 0; }
QFrame#binderEmpty { background:transparent; }
QFrame#binderNotice { background:@overlay; border:1px solid @yellow; border-radius:14px; }
QFrame#binderNotice QLabel { background:transparent; color:@text; }
QFrame#settingRow QRadioButton { background:transparent; padding:2px 0; spacing:8px; }
QRadioButton::indicator { width:14px; height:14px; border-radius:9px; border:2px solid @field_border; background:@input; }
QRadioButton::indicator:checked { background:@primary; border:2px solid @focus; }
QLabel#settingHint { color:@muted; }
QPushButton#settingsTab { background:transparent; color:@muted; border:1px solid @border; border-radius:11px; padding:6px 10px; text-align:center; }
QPushButton#settingsTab:hover { background:@hover; color:@text; border-color:@neon_soft; }
QPushButton#settingsTab:checked { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 @primary,stop:1 @primary_glow); color:@on_primary; border:1px solid @neon_hi; }
QPushButton#linkButton { background:transparent; border:0; color:@link; padding:2px 0; text-align:left; }
QPushButton#linkButton:hover { text-decoration:underline; }
QFrame#binderBook { background:qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 @binder_start, stop:1 @binder_end); border:1px solid @binder_border; border-radius:16px; }
QFrame#binderPage { background:qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 @page_start, stop:1 @page_end); border:1px solid @page_border; border-radius:10px; }
QFrame#binderSpine { background:qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 @spine_edge, stop:0.5 @spine_mid, stop:1 @spine_edge); border:0; }
QTabWidget#terminalTabs::pane { background:@terminal; border:1px solid @inner_line; border-radius:12px; top:-1px; }
QTabWidget#terminalTabs QTabBar::tab { background:@surface; border:1px solid @border; border-bottom:0; margin-right:4px; border-top-left-radius:10px; border-top-right-radius:10px; }
QTabWidget#terminalTabs QTabBar::tab:selected { background:@terminal; color:@terminal_text; border:1px solid @neon_soft; border-bottom:0; }
QPushButton#binderTurn { padding:2px 14px; border-radius:16px; }
QScrollArea { border:0; }
QScrollBar:vertical { background:transparent; width:11px; margin:0; }
QScrollBar::handle:vertical { background:@field_border; min-height:25px; border-radius:5px; }
QScrollArea#pageScroll > QWidget > QScrollBar:vertical { width:24px; margin:20px 14px 20px 0; }
QScrollArea#pageScroll > QWidget > QScrollBar[idle="true"]::handle:vertical { background:transparent; }
QWidget#glowFrame { background:transparent; }
QScrollBar::handle:vertical:hover { background:@neon; }
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical { height:0; }
QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical { background:transparent; }
QScrollBar:horizontal { background:transparent; height:11px; margin:0; }
QScrollBar::handle:horizontal { background:@field_border; min-width:25px; border-radius:5px; }
QScrollBar::handle:horizontal:hover { background:@neon; }
QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal { width:0; }
QScrollBar::add-page:horizontal,QScrollBar::sub-page:horizontal { background:transparent; }
QSplitter::handle { background:@border; }
QStatusBar { background:@sidebar; color:@muted; border-top:1px solid @neon_soft; }
QStatusBar::item { border:0; }
QToolTip { background:@tooltip; color:@tooltip_text; border:1px solid @tooltip_border; padding:6px; }
QMenu { background:@surface; color:@text; border:1px solid @neon_soft; border-radius:8px; padding:6px; }
QMenu::item { background:transparent; padding:7px 26px 7px 14px; border-radius:6px; }
QMenu::item:selected { background:@hover; color:@text; }
QMenu::item:disabled { color:@border; }
QMenu::separator { height:1px; background:@border; margin:5px 8px; }
'''
    for key in sorted(c, key=len, reverse=True):
        template = template.replace('@' + key, c[key])
    return template + _combo_arrows(c) + _check_boxes(c) + _header_arrows(c)


BRAND_CARD = Path(__file__).resolve().parent / 'branding' / 'pokemind-card.png'
BRAND_CARD_SIZE = (530, 742)  # half of the approved 1060 x 1484 card (scripts/make_icon.py --card)


@lru_cache(maxsize=1)
def _card_source():
    """The packaged PokeMind / TCG Coach card (owner-approved artwork, never redrawn)."""
    image = QImage(str(BRAND_CARD))
    return image.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied) if not image.isNull() else image


@lru_cache(maxsize=48)
def _card_scaled(pixels):
    source = _card_source()
    if source.isNull():
        return QImage()
    return source.scaledToHeight(pixels, Qt.TransformationMode.SmoothTransformation)


def screen_ratio():
    application = QGuiApplication.instance()
    return application.devicePixelRatio() if application is not None else 1.0


def card_width(height):
    return max(1, round(height * BRAND_CARD_SIZE[0] / BRAND_CARD_SIZE[1]))


def card_pixmap(height=96, ratio=None):
    """The whole card, `height` logical pixels tall, proportions kept, sharp on high-DPI screens."""
    ratio = ratio or screen_ratio()
    result = QPixmap.fromImage(_card_scaled(max(1, round(height * ratio))))
    result.setDevicePixelRatio(ratio)
    return result


def logo_pixmap(size=64, ratio=None):
    """The PokeMind logo: the whole card, centred in a transparent square (icons, menu, small spots)."""
    ratio = ratio or screen_ratio()
    pixels = max(1, round(size * ratio))
    canvas = QImage(pixels, pixels, QImage.Format.Format_ARGB32_Premultiplied)
    canvas.fill(Qt.GlobalColor.transparent)
    card = _card_scaled(pixels)
    if not card.isNull():
        p = QPainter(canvas)
        p.drawImage((pixels - card.width()) // 2, 0, card)
        p.end()
    result = QPixmap.fromImage(canvas)
    result.setDevicePixelRatio(ratio)
    return result


def logo_icon_sizes():
    return (16, 20, 24, 32, 40, 48, 64, 128, 256)


def expand_icon(collapse=False, theme='dark'):
    """Four corner arrows pointing out (expand) or in (bring back)."""
    picture = QPixmap(32, 32)
    picture.fill(Qt.GlobalColor.transparent)
    p = QPainter(picture)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor(colors(theme)['accent']), 2.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        corner_x, corner_y = 16 - sx * 12, 16 - sy * 12
        inner_x, inner_y = 16 - sx * 5, 16 - sy * 5
        tip_x, tip_y = (inner_x, inner_y) if collapse else (corner_x, corner_y)
        p.drawLine(corner_x, corner_y, inner_x, inner_y)
        p.drawLine(tip_x, tip_y, tip_x + sx * 6 * (-1 if collapse else 1), tip_y)
        p.drawLine(tip_x, tip_y, tip_x, tip_y + sy * 6 * (-1 if collapse else 1))
    p.end()
    return QIcon(picture)


def logo_icon():
    icon = QIcon()
    for size in logo_icon_sizes():
        icon.addPixmap(logo_pixmap(size, 1.0))
    return icon


def navigation_icon(index, theme='dark'):
    """Menu glyph in the theme accent; a selected item (primary background) gets its own contrasting colour."""
    if index == 0:
        return logo_icon()
    c = colors(theme)
    icon = QIcon()
    icon.addPixmap(_navigation_glyph(index, c['accent']), QIcon.Mode.Normal)
    icon.addPixmap(_navigation_glyph(index, c['nav_icon_selected']), QIcon.Mode.Selected)
    return icon


def _navigation_glyph(index, color):
    picture = QPixmap(32, 32)
    picture.fill(Qt.GlobalColor.transparent)
    p = QPainter(picture)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor(color), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.setBrush(Qt.BrushStyle.NoBrush)
    if index == 1:
        for a,b,c,d in ((7,6,25,25), (25,6,7,25), (5,20,12,27), (20,27,27,20)):
            p.drawLine(a,b,c,d)
    elif index == 2:
        p.drawRoundedRect(7,4,17,23,3,3)
        p.drawLine(3,10,3,28)
        p.drawLine(3,28,19,28)
        p.drawEllipse(12,10,7,7)
    elif index == 3:
        p.drawEllipse(5,4,17,17)
        p.drawLine(20,20,28,28)
        p.drawLine(10,12,17,12)
        p.drawLine(13,8,13,16)
    elif index == 4:
        p.drawRoundedRect(4,6,24,21,2,2)
        p.drawLine(16,6,16,27)
        for y in (12,17,22):
            p.drawLine(8,y,12,y)
            p.drawLine(20,y,24,y)
    elif index == 6:
        p.drawRoundedRect(3,5,26,22,3,3)
        p.drawLine(8,12,13,16)
        p.drawLine(13,16,8,20)
        p.drawLine(16,21,23,21)
    else:
        import math
        p.drawEllipse(7,7,18,18)
        p.drawEllipse(12,12,8,8)
        for i in range(8):
            angle = i * math.pi / 4
            p.drawLine(round(16+10*math.cos(angle)), round(16+10*math.sin(angle)),
                       round(16+14*math.cos(angle)), round(16+14*math.sin(angle)))
    p.end()
    return picture


# Each settings glyph takes a palette role, so it follows the theme: cyan/blue for display and information,
# gold for files and keys, green for data kept safe, red only for the destructive reset.
SETTING_ROLES = {'theme': 'link', 'language': 'blue', 'motion': 'success', 'images': 'yellow', 'cloud': 'blue',
                 'share': 'success', 'folder': 'yellow', 'shield': 'success', 'key': 'yellow', 'pulse': 'success',
                 'refresh': 'link', 'reset': 'red', 'eye': 'link', 'database': 'yellow', 'copy': 'blue',
                 'info': 'link', 'general': 'yellow', 'archive': 'success', 'restore': 'yellow', 'updates': 'success',
                 'coach': 'link', 'battles': 'yellow', 'data': 'success', 'about': 'blue', 'terminal': 'link'}


def setting_tint(kind, theme='dark'):
    return colors(theme)[SETTING_ROLES.get(kind, 'yellow')]


def setting_tab_icon(kind, theme='dark'):
    """A settings tab glyph; the checked tab (primary background) shows it in the selected-item colour."""
    icon = QIcon()
    icon.addPixmap(setting_icon(kind, theme=theme).pixmap(32, 32), QIcon.Mode.Normal, QIcon.State.Off)
    icon.addPixmap(setting_icon(kind, theme=theme, tint=colors(theme)['nav_icon_selected']).pixmap(32, 32),
                   QIcon.Mode.Normal, QIcon.State.On)
    return icon


def setting_icon(kind, size=32, theme='dark', tint=None):
    """Windows-like settings glyph: a coloured line drawing on a soft rounded tile."""
    tint = QColor(tint or setting_tint(kind, theme))
    picture = QPixmap(size, size)
    picture.fill(Qt.GlobalColor.transparent)
    p = QPainter(picture)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(size / 32, size / 32)
    tile = QColor(tint)
    tile.setAlpha(46)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(tile)
    p.drawRoundedRect(QRectF(0, 0, 32, 32), 8, 8)
    p.setPen(QPen(tint, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.setBrush(Qt.BrushStyle.NoBrush)
    if kind == 'theme':
        p.drawEllipse(QRectF(8, 8, 16, 16))
        p.setBrush(tint)
        p.drawPie(QRectF(8, 8, 16, 16), 90 * 16, 180 * 16)
    elif kind in ('language',):
        p.drawEllipse(QRectF(7, 7, 18, 18))
        p.drawEllipse(QRectF(12, 7, 8, 18))
        p.drawLine(QPointF(7.5, 16), QPointF(24.5, 16))
    elif kind == 'motion':
        for y in (11, 16, 21):
            wave = QPainterPath(QPointF(7, y))
            wave.cubicTo(11, y - 4, 13, y + 4, 17, y)
            wave.cubicTo(20, y - 3, 22, y + 3, 25, y)
            p.drawPath(wave)
    elif kind == 'images':
        p.drawRoundedRect(QRectF(7, 8, 18, 16), 2, 2)
        p.drawPolyline([QPointF(8, 22), QPointF(14, 15), QPointF(18, 19), QPointF(21, 16), QPointF(24, 20)])
        p.drawEllipse(QRectF(18, 10.5, 3, 3))
    elif kind == 'cloud':
        cloud = QPainterPath()
        for x, y, r in ((12, 18, 4), (17, 14, 5.5), (21.5, 18, 4)):
            bubble = QPainterPath()
            bubble.addEllipse(QPointF(x, y), r, r)
            cloud = cloud.united(bubble)
        base = QPainterPath()
        base.addRect(QRectF(12, 17, 9.5, 5))
        p.drawPath(cloud.united(base))
    elif kind == 'share':
        for a, b in (((10, 16), (21, 10)), ((10, 16), (21, 22))):
            p.drawLine(QPointF(*a), QPointF(*b))
        for x, y in ((10, 16), (21, 10), (21, 22)):
            p.setBrush(tint)
            p.drawEllipse(QPointF(x, y), 2.6, 2.6)
    elif kind in ('folder',):
        p.drawPolyline([QPointF(7, 23), QPointF(7, 10), QPointF(13, 10), QPointF(15, 12), QPointF(25, 12),
                        QPointF(25, 23), QPointF(7, 23)])
    elif kind == 'shield':
        shield = QPainterPath(QPointF(16, 7))
        shield.lineTo(24, 10)
        shield.cubicTo(24, 18, 21, 22, 16, 25)
        shield.cubicTo(11, 22, 8, 18, 8, 10)
        shield.closeSubpath()
        p.drawPath(shield)
        p.drawPolyline([QPointF(12.5, 16), QPointF(15, 18.5), QPointF(19.5, 13.5)])
    elif kind == 'key':
        p.drawEllipse(QRectF(7, 9, 9, 9))
        p.drawLine(QPointF(15, 15.5), QPointF(25, 21))
        p.drawLine(QPointF(21.5, 19), QPointF(20, 22))
        p.drawLine(QPointF(24, 20.5), QPointF(23, 23))
    elif kind == 'pulse':
        p.drawPolyline([QPointF(6, 17), QPointF(11, 17), QPointF(13.5, 10), QPointF(17, 23), QPointF(20, 14),
                        QPointF(22, 17), QPointF(26, 17)])
    elif kind in ('refresh', 'reset'):
        p.drawArc(QRectF(8, 8, 16, 16), 40 * 16, 280 * 16)
        p.drawPolyline([QPointF(22, 7), QPointF(22.5, 12), QPointF(17.5, 12)])
    elif kind == 'eye':
        eye = QPainterPath(QPointF(6, 16))
        eye.quadTo(16, 6, 26, 16)
        eye.quadTo(16, 26, 6, 16)
        p.drawPath(eye)
        p.drawEllipse(QPointF(16, 16), 3.2, 3.2)
    elif kind in ('database', 'data'):
        p.drawEllipse(QRectF(9, 7, 14, 5))
        p.drawLine(QPointF(9, 9.5), QPointF(9, 22.5))
        p.drawLine(QPointF(23, 9.5), QPointF(23, 22.5))
        p.drawArc(QRectF(9, 13.5, 14, 5), 180 * 16, 180 * 16)
        p.drawArc(QRectF(9, 20, 14, 5), 180 * 16, 180 * 16)
    elif kind == 'updates':
        p.drawArc(QRectF(7, 7, 18, 18), 120 * 16, 300 * 16)
        p.drawLine(QPointF(16, 11), QPointF(16, 20))
        p.drawPolyline([QPointF(12.5, 16.5), QPointF(16, 20), QPointF(19.5, 16.5)])
    elif kind in ('archive', 'restore'):
        p.drawRoundedRect(QRectF(7, 8, 18, 5), 1.5, 1.5)
        p.drawPolyline([QPointF(8.5, 13), QPointF(8.5, 24), QPointF(23.5, 24), QPointF(23.5, 13)])
        if kind == 'archive':
            p.drawLine(QPointF(13.5, 17), QPointF(18.5, 17))
        else:
            p.drawLine(QPointF(16, 22), QPointF(16, 16))
            p.drawPolyline([QPointF(13, 18.5), QPointF(16, 15.5), QPointF(19, 18.5)])
    elif kind == 'copy':
        p.drawRoundedRect(QRectF(11, 10, 12, 14), 2, 2)
        p.drawPolyline([QPointF(9, 20), QPointF(9, 8), QPointF(19, 8)])
    elif kind in ('info', 'about'):
        p.drawEllipse(QRectF(7, 7, 18, 18))
        p.drawLine(QPointF(16, 15), QPointF(16, 21))
        p.setBrush(tint)
        p.drawEllipse(QPointF(16, 11.3), 1.2, 1.2)
    elif kind == 'general':
        p.drawEllipse(QRectF(12, 12, 8, 8))
        for angle in range(0, 360, 45):
            p.save()
            p.translate(16, 16)
            p.rotate(angle)
            p.drawLine(QPointF(0, -6.5), QPointF(0, -9.5))
            p.restore()
    elif kind == 'coach':
        p.drawRoundedRect(QRectF(7, 8, 18, 13), 4, 4)
        p.drawPolyline([QPointF(12, 21), QPointF(11, 25), QPointF(16, 21)])
        for x in (12, 16, 20):
            p.drawPoint(QPointF(x, 14.5))
    elif kind == 'battles':
        for a, b, c, d in ((8, 8, 24, 24), (24, 8, 8, 24), (7, 20, 12, 25), (20, 25, 25, 20)):
            p.drawLine(QPointF(a, b), QPointF(c, d))
    elif kind == 'terminal':
        p.drawRoundedRect(QRectF(6, 8, 20, 16), 3, 3)
        p.drawPolyline([QPointF(10, 13), QPointF(13.5, 16), QPointF(10, 19)])
        p.drawLine(QPointF(16, 19.5), QPointF(21, 19.5))
    p.end()
    return QIcon(picture)
