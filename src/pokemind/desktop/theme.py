"""Local, code-drawn Pokédex styling; no downloaded artwork or fonts."""
import os
import tempfile
from pathlib import Path

from PySide6.QtCore import QDir, Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QIcon, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPalette


# BrainBall electric (owner, 2026-11-05): docs/design/pokemind-brainball/palette.json is the source of truth.
# Its tokens are copied here unchanged; the few derived tokens are marked and checked by the tests.
BRAND = dict(bleu_nuit='#001261', bleu_royal='#01339F', bleu_electrique='#004CCB', bleu_lumineux='#0793FA',
             cyan='#68D6F9', gold='#FECF4D', rouge_cerveau='#EE4B50', rouge_profond='#C32039', blanc_nacre='#FEFCFA')

PALETTES = {
    'dark': dict(background='#07142F', sidebar='#081E4A', surface='#102652', alternate='#16356D', input='#081C3E',
                 text='#F7FAFF', muted='#C3D8F4', border='#335A8E', hover='#1B4380', accent='#FFD54F',
                 primary='#0054C7', primary_hover='#074DB4', on_primary='#FFFFFF', link='#6FD5FF', focus='#FFDD5D',
                 red='#FF6B74', blue='#68BFFF', yellow='#FFD54F', success='#62D1B3', warning='#FFE493',
                 warning_bg='#392F24', selection='#0054C7', selection_text='#FFFFFF', hero_start='#00339F',
                 hero_end='#004CCB', hero_text='#FFFFFF', hero_kicker='#FFD54F', danger='#B72C43', on_danger='#FFFFFF',
                 neutral_chart='#90A9CF',
                 # derived
                 primary_pressed='#003F96', hero_muted='#DCE8FF', hero_border='#0793FA', nav_icon_selected='#FFD54F',
                 tooltip='#081E4A', tooltip_text='#F7FAFF', tooltip_border='#FFD54F', overlay='rgba(7,20,47,0.94)',
                 field_border='#4F79B0'),
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
                  field_border='#7088AD'),
}
DERIVED = ('primary_pressed', 'hero_muted', 'hero_border', 'nav_icon_selected', 'tooltip', 'tooltip_text',
           'tooltip_border', 'overlay',
           'field_border')  # palette.json borders are decorative (under 3:1 around inputs); fields get this one
# The same in both themes: the binder is a physical object (royal blue cover, navy pages, so the sleeves and the
# card names keep their contrast), and the terminal stays dark because console programs pick their ANSI colours
# for a dark background.
OBJECTS = dict(binder_start='#01339F', binder_end='#001261', binder_border='#0793FA', page_start='#132E63',
               page_end='#0B1D42', page_border='#06122B', spine_edge='#001261', spine_mid='#004CCB',
               terminal='#081C3E', terminal_text='#F7FAFF', gold_line='#FECF4D')


def colors(theme):
    return PALETTES['light' if theme == 'light' else 'dark']


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


def stylesheet(theme):
    c = dict(OBJECTS, **colors(theme))
    template = '''
QWidget { background:@background; color:@text; font-family:"Segoe UI"; font-size:14px; }
QMainWindow,QStackedWidget { background:@background; }
QWidget#motionOverlay { background:transparent; border:0; }
QLabel { background:transparent; }
QLabel#title { font-size:27px; font-weight:700; }
QLabel#muted { color:@muted; }
QFrame#sidebar { background:@sidebar; border-right:1px solid @border; }
QFrame#sidebar QLabel { color:@muted; }
QFrame#sidebar QLabel#brand { color:@accent; font-size:25px; font-weight:800; }
QFrame#sidebar QLabel#brandCaption { color:@muted; font-size:10px; font-weight:700; letter-spacing:1px; }
QListWidget { background:@sidebar; color:@text; border:0; padding:0; outline:0; }
QListWidget::item { padding:10px; border-radius:10px; margin:3px 0; border:1px solid transparent; }
QListWidget::item:hover { background:@hover; }
QListWidget::item:selected { background:@primary; color:@on_primary; border:1px solid @primary; }
QListWidget::item:focus { border:1px solid @focus; }
QFrame#hero { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 @hero_start,stop:1 @hero_end); border:1px solid @hero_border; border-radius:18px; }
QFrame#hero QLabel { color:@hero_text; }
QFrame#hero QLabel#heroKicker { font-size:11px; font-weight:700; letter-spacing:2px; color:@hero_kicker; }
QLabel#heroTitle { font-size:30px; font-weight:800; }
QLabel#heroDescription { font-size:13px; color:@hero_muted; }
QFrame#card { background:@surface; border:1px solid @border; border-top:3px solid @neutral_chart; border-radius:12px; }
QFrame#card[metricKind="wins"] { border-top-color:@blue; }
QFrame#card[metricKind="losses"] { border-top-color:@red; }
QFrame#card[metricKind="rival"] { border-top-color:@yellow; }
QFrame#card QLabel { background:transparent; }
QLabel#sectionTitle { font-size:18px; font-weight:700; color:@text; }
QLabel#smallCaption { color:@muted; font-size:12px; }
QPushButton#sidebarToggle { background:@surface; color:@accent; border:1px solid @border; padding:5px; }
QPushButton#favoriteButton:checked { color:@yellow; border-color:@yellow; background:@alternate; }
QPushButton#homeLink { text-align:left; padding:10px; font-weight:500; }
QPushButton#sourceToggle { font-size:12px; padding:5px; }
QLabel#battleBadge { color:@text; background:@surface; border:1px solid @border; border-left:4px solid @blue; border-radius:10px; font-size:16px; font-weight:700; padding:10px 14px; }
QLabel#tileValue { font-size:28px; font-weight:800; color:@accent; }
QFrame#card[metricKind="games"] QLabel#tileValue { color:@text; }
QFrame#card[metricKind="wins"] QLabel#tileValue { color:@blue; }
QFrame#card[metricKind="losses"] QLabel#tileValue { color:@red; }
QLabel#tileName { font-size:16px; font-weight:700; color:@yellow; }
QLabel#metric { font-size:35px; font-weight:800; color:@accent; }
QFrame#card[metricKind="games"] QLabel#metric { color:@text; }
QFrame#card[metricKind="wins"] QLabel#metric { color:@blue; }
QFrame#card[metricKind="losses"] QLabel#metric { color:@red; }
QLabel#corpusNote { color:@warning; padding:12px; background:@warning_bg; border:1px solid @border; border-radius:10px; }
QLabel[cardType="pokemon"] { color:@red; font-weight:700; }
QLabel[cardType="trainer"] { color:@blue; font-weight:700; }
QLabel[cardType="energy"] { color:@yellow; font-weight:700; }
QTextEdit,QTextBrowser,QLineEdit,QComboBox,QTableWidget { background:@input; color:@text; border:1px solid @border; border-radius:10px; padding:9px; selection-background-color:@selection; selection-color:@selection_text; }
QTextEdit,QLineEdit,QComboBox { border-color:@field_border; }
QTextEdit:focus,QTextBrowser:focus,QLineEdit:focus,QComboBox:focus,QTableWidget:focus { border:1px solid @focus; }
QLineEdit { min-height:25px; }
QComboBox { min-height:24px; padding-right:24px; }
QComboBox QAbstractItemView { background:@surface; color:@text; selection-background-color:@selection; selection-color:@selection_text; }
QPushButton { background:@surface; color:@text; border:1px solid @border; border-radius:10px; padding:10px 14px; font-weight:600; }
QPushButton:hover { background:@hover; border-color:@blue; }
QPushButton:pressed { background:@alternate; }
QPushButton:focus { border:2px solid @focus; padding:9px 13px; }
QPushButton#primary { background:@primary; color:@on_primary; border:1px solid @primary; font-weight:700; }
QPushButton#primary:hover { background:@primary_hover; border-color:@focus; }
QPushButton#compact { padding:6px 8px; font-size:13px; }
QPushButton#compact:focus { padding:5px 7px; }
QPushButton#primary:pressed { background:@primary_pressed; }
QPushButton[destructive="true"] { color:@red; }
QPushButton[destructive="true"]:hover { background:@danger; color:@on_danger; border-color:@danger; }
QPushButton:disabled { background:@alternate; color:@muted; border:1px solid @border; }
QPushButton#primary:disabled,QPushButton[destructive="true"]:disabled { background:@alternate; color:@muted; border:1px solid @border; }
QHeaderView::section { background:@surface; color:@muted; border:0; border-bottom:1px solid @border; padding:9px; font-weight:600; }
QTableWidget { gridline-color:@border; alternate-background-color:@alternate; }
QTabWidget::pane { border:0; }
QTabBar::tab { background:@surface; color:@muted; padding:10px 15px; margin-right:4px; border-bottom:3px solid transparent; }
QTabBar::tab:hover { color:@text; }
QTabBar::tab:selected { color:@text; border-bottom:3px solid @blue; }
QDockWidget::title { background:@sidebar; color:@accent; padding:12px; font-weight:700; }
QFrame#chatTitleBar { background:@sidebar; border-bottom:1px solid @border; }
QFrame#chatTitleBar QLabel { color:@accent; font-size:12px; font-weight:700; letter-spacing:1px; }
QWidget#chatBody { background:@surface; }
QWidget#chatBody QComboBox { padding:5px 8px; min-height:20px; }
QWidget#chatBody QPushButton { padding:7px 10px; }
QCheckBox { spacing:8px; padding:6px; }
QCheckBox::indicator { width:16px; height:16px; }
QProgressBar { background:@alternate; border:0; border-radius:4px; }
QProgressBar::chunk { background:@blue; border-radius:4px; }
QTextBrowser#chatTranscript { font-family:"Segoe UI Variable Text"; font-size:14px; padding:2px; }
QFrame#loadingBanner { background:@alternate; border:0; border-bottom:3px solid @blue; }
QFrame#loadingBanner QLabel { background:transparent; }
QFrame#loadingBanner QProgressBar { background:@surface; }
QFrame#updateBanner { background:@alternate; border:0; border-bottom:3px solid @success; }
QFrame#updateBanner QLabel { background:transparent; }
QFrame#updateBanner QProgressBar { background:@surface; }
QLabel#loadingTitle { color:@text; font-size:17px; font-weight:800; }
QLabel#loadingDetail { color:@muted; font-size:12px; }
QFrame#activityCard { background:transparent; border:1px solid transparent; border-radius:12px; }
QFrame#activityCard[busy="true"] { background:@alternate; border:1px solid @blue; }
QLabel#activityLabel { color:@muted; font-size:12px; }
QLabel#activityLabel[busy="true"] { color:@text; font-size:14px; font-weight:600; }
QLabel#activityClock { color:@muted; font-size:12px; }
QLabel#activityClock[busy="true"] { color:@accent; background:@sidebar; border-radius:9px; padding:2px 9px; font-weight:700; }
QLabel#permissionBadge { color:@warning; background:@warning_bg; border:1px solid @yellow; border-radius:10px; padding:3px 9px; font-size:12px; font-weight:600; }
QLabel#chatNotice { color:@warning; background:@warning_bg; border-radius:9px; padding:5px 9px; font-size:12px; }
QPushButton#chatExpand { background:transparent; color:@accent; border:1px solid @border; border-radius:8px; padding:3px 10px; font-size:12px; font-weight:600; }
QPushButton#chatExpand:hover { background:@hover; }
QFrame#settingRow { background:@surface; border:1px solid @border; border-radius:10px; }
QFrame#settingRow QLabel { background:transparent; }
QFrame#settingRow QCheckBox { background:transparent; padding:2px 0; font-weight:600; }
QFrame#binderEmpty { background:transparent; }
QFrame#binderNotice { background:@overlay; border:1px solid @yellow; border-radius:14px; }
QFrame#binderNotice QLabel { background:transparent; color:@text; }
QFrame#settingRow QRadioButton { background:transparent; padding:2px 0; font-weight:600; spacing:8px; }
QRadioButton::indicator { width:14px; height:14px; border-radius:9px; border:2px solid @field_border; background:@input; }
QRadioButton::indicator:checked { background:@primary; border:2px solid @focus; }
QLabel#settingTitle { font-weight:600; }
QLabel#settingHint { color:@muted; font-size:12px; }
QPushButton#settingsTab { background:@surface; color:@muted; border:1px solid @border; border-radius:9px; padding:8px 10px; text-align:center; }
QPushButton#settingsTab:hover { background:@hover; color:@text; }
QPushButton#settingsTab:checked { background:@primary; color:@on_primary; border:1px solid @primary; }
QPushButton#linkButton { background:transparent; border:0; color:@link; padding:2px 0; text-align:left; }
QPushButton#linkButton:hover { text-decoration:underline; }
QFrame#binderBook { background:qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 @binder_start, stop:1 @binder_end); border:1px solid @binder_border; border-radius:16px; }
QFrame#binderPage { background:qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 @page_start, stop:1 @page_end); border:1px solid @page_border; border-radius:10px; }
QFrame#binderSpine { background:qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 @spine_edge, stop:0.5 @spine_mid, stop:1 @spine_edge); border:0; }
QTabWidget#terminalTabs::pane { background:@terminal; border:1px solid @border; border-radius:12px; top:-1px; }
QTabWidget#terminalTabs QTabBar::tab { background:@surface; border-top-left-radius:9px; border-top-right-radius:9px; }
QTabWidget#terminalTabs QTabBar::tab:selected { background:@terminal; color:@terminal_text; }
QPushButton#terminalLaunch { padding:8px 14px; }
QPushButton#binderTurn { font-size:20px; font-weight:800; padding:2px 14px; border-radius:16px; }
QScrollArea { border:0; }
QScrollBar:vertical { background:@background; width:11px; margin:0; }
QScrollBar::handle:vertical { background:@field_border; min-height:25px; border-radius:5px; }
QScrollBar::handle:vertical:hover { background:@blue; }
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical { height:0; }
QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical { background:transparent; }
QScrollBar:horizontal { background:@background; height:11px; margin:0; }
QScrollBar::handle:horizontal { background:@field_border; min-width:25px; border-radius:5px; }
QScrollBar::handle:horizontal:hover { background:@blue; }
QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal { width:0; }
QScrollBar::add-page:horizontal,QScrollBar::sub-page:horizontal { background:transparent; }
QSplitter::handle { background:@border; }
QStatusBar { background:@surface; color:@muted; border-top:1px solid @border; }
QStatusBar::item { border:0; }
QToolTip { background:@tooltip; color:@tooltip_text; border:1px solid @tooltip_border; padding:6px; }
'''
    for key in sorted(c, key=len, reverse=True):
        template = template.replace('@' + key, c[key])
    return template + _combo_arrows(c)


def brain_path():
    """A 2D brain, two hemispheres made of rounded lobes, centred on (32, 32) of a 64 grid."""
    shape = QPainterPath()
    shape.addEllipse(QPointF(32, 32), 7, 8)
    for x, y, r in ((26.5, 28, 4.5), (25, 33, 4.2), (28.5, 36.5, 4), (30, 27, 4)):
        for cx in (x, 64 - x):
            lobe = QPainterPath()
            lobe.addEllipse(QPointF(cx, y), r, r)
            shape = shape.united(lobe)
    return shape


def logo_pixmap(size=64):
    """The PokeMind logo (original design): two fanned trading cards, the front one showing a brain."""
    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)
    p = QPainter(result)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(size / 64, size / 64)
    detailed = size >= 28  # folds and text lines only read from the window icon size upwards
    for angle, shift, top, bottom in ((-15, -7, '#5b8cf0', '#22397a'), (9, 5, '#f0485c', '#a01d34')):
        p.save()
        p.translate(32 + shift, 33)
        p.rotate(angle)
        shade = QLinearGradient(0, -21, 0, 21)
        shade.setColorAt(0, QColor(top))
        shade.setColorAt(1, QColor(bottom))
        p.setPen(QPen(QColor('#ffda62'), 2.6 if detailed else 3.4))
        p.setBrush(shade)
        p.drawRoundedRect(QRectF(-15, -21, 30, 42), 5, 5)
        p.restore()
    p.translate(37, 33)
    p.rotate(9)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor('#fff1f4'))
    p.drawRoundedRect(QRectF(-11, -16, 22, 21), 3.5, 3.5)  # the card's picture window
    if detailed:
        p.setPen(QPen(QColor('#ffda62'), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(-9, 10), QPointF(9, 10))
        p.drawLine(QPointF(-9, 14.5), QPointF(4, 14.5))
    p.translate(0, -5.5)
    p.scale(0.82, 0.82)
    p.translate(-32, -32)
    p.setPen(QPen(QColor('#7a1838'), 1.8))
    p.setBrush(QColor('#ff8fb2'))
    p.drawPath(brain_path())
    p.setPen(QPen(QColor('#7a1838'), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.setBrush(Qt.BrushStyle.NoBrush)
    fissure = QPainterPath(QPointF(32, 24.5))
    fissure.cubicTo(30.8, 28, 33.2, 32, 32, 39.5)
    p.drawPath(fissure)
    if detailed:
        for points in (((24, 31), (27, 30), (27.6, 33.4)), ((27.2, 25.2), (28.4, 28), (26, 29.6)),
                       ((28.8, 38.6), (28.8, 35.4), (31, 34.6))):
            for mirror in (False, True):
                (ax, ay), (bx, by), (cx, cy) = ((64 - x if mirror else x, y) for x, y in points)
                curve = QPainterPath(QPointF(ax, ay))
                curve.quadTo(bx, by, cx, cy)
                p.drawPath(curve)
    p.end()
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
        icon.addPixmap(logo_pixmap(size))
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
                 'coach': 'link', 'battles': 'yellow', 'data': 'success', 'about': 'blue'}


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
    p.end()
    return QIcon(picture)
