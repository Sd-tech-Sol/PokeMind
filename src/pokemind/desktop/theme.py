"""Local, code-drawn Pokédex styling; no downloaded artwork or fonts."""
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPalette


PALETTES = {
    'dark': dict(background='#141820', surface='#1e2430', input='#191f29',
                 text='#f3f5fa', muted='#acb7ca', border='#374255',
                 hover='#303b4d', alternate='#242d3b', accent='#ffd45a',
                 link='#8ebcff', warning='#fff0b3', warning_bg='#37301e',
                 red='#ff8493', blue='#9cbdff', yellow='#ffda73'),
    'light': dict(background='#f1f3f8', surface='#ffffff', input='#ffffff',
                  text='#202b40', muted='#526078', border='#ccd4e2',
                  hover='#e8edf7', alternate='#f4f6fb', accent='#324f98',
                  link='#214fa4', warning='#684b09', warning_bg='#fff4d4',
                  red='#b62743', blue='#3155a0', yellow='#795400'),
}


def colors(theme):
    return PALETTES['light' if theme == 'light' else 'dark']


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
                        (QPalette.ColorRole.Highlight, '#b92b43'),
                        (QPalette.ColorRole.HighlightedText, '#ffffff')):
        value.setColor(role, QColor(color))
    return value


def stylesheet(theme):
    c = colors(theme)
    template = '''
QWidget { background:@background; color:@text; font-family:"Segoe UI"; font-size:14px; }
QMainWindow,QStackedWidget { background:@background; }
QWidget#motionOverlay { background:transparent; border:0; }
QLabel { background:transparent; }
QLabel#title { font-size:27px; font-weight:700; }
QLabel#muted { color:@muted; }
QFrame#sidebar { background:#1b2335; border-right:1px solid #34415b; }
QFrame#sidebar QLabel { color:#b9c7e2; }
QFrame#sidebar QLabel#brand { color:#ffda62; font-size:25px; font-weight:800; }
QFrame#sidebar QLabel#brandCaption { color:#b9c7e2; font-size:10px; font-weight:700; letter-spacing:1px; }
QListWidget { background:#1b2335; color:#c5cfe3; border:0; padding:0; outline:0; }
QListWidget::item { padding:10px; border-radius:10px; margin:3px 0; border:1px solid transparent; }
QListWidget::item:hover { background:#2b3852; }
QListWidget::item:selected { background:#c73148; color:white; border:1px solid #ed5368; }
QListWidget::item:focus { border:1px solid #ffda62; }
QFrame#hero { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ba2440,stop:1 #e34450); border:1px solid #ee6672; border-radius:18px; }
QFrame#hero QLabel { color:white; }
QFrame#hero QLabel#heroKicker { font-size:11px; font-weight:700; letter-spacing:2px; color:#ffe39a; }
QLabel#heroTitle { font-size:30px; font-weight:800; }
QLabel#heroDescription { font-size:13px; color:#fff0f2; }
QFrame#card { background:@surface; border:1px solid @border; border-top:3px solid #d84559; border-radius:12px; }
QFrame#card[metricKind="wins"] { border-top-color:#628be0; }
QFrame#card[metricKind="losses"] { border-top-color:#e9bd4a; }
QFrame#card QLabel { background:transparent; }
QLabel#sectionTitle { font-size:18px; font-weight:700; color:@text; }
QLabel#smallCaption { color:@muted; font-size:12px; }
QPushButton#sidebarToggle { background:#26334c; color:#ffda62; border:1px solid #394a69; padding:5px; }
QPushButton#favoriteButton:checked { color:@yellow; border-color:#e9bd4a; background:@alternate; }
QPushButton#homeLink { text-align:left; padding:10px; font-weight:500; }
QPushButton#sourceToggle { font-size:12px; padding:5px; }
QLabel#battleBadge { color:@text; background:@surface; border:1px solid @border; border-left:4px solid #d84559; border-radius:10px; font-size:16px; font-weight:700; padding:10px 14px; }
QLabel#tileValue { font-size:28px; font-weight:800; color:@accent; }
QFrame#card[metricKind="games"] QLabel#tileValue { color:@text; }
QFrame#card[metricKind="wins"] QLabel#tileValue { color:@blue; }
QFrame#card[metricKind="losses"] QLabel#tileValue { color:@red; }
QLabel#tileName { font-size:16px; font-weight:700; color:@yellow; }
QFrame#card[metricKind="rival"] { border-top-color:#9b6bff; }
QLabel#metric { font-size:35px; font-weight:800; color:@accent; }
QLabel#corpusNote { color:@warning; padding:12px; background:@warning_bg; border:1px solid @border; border-radius:10px; }
QLabel#permissionBadge { color:@warning; font-weight:700; }
QLabel[cardType="pokemon"] { color:@red; font-weight:700; }
QLabel[cardType="trainer"] { color:@blue; font-weight:700; }
QLabel[cardType="energy"] { color:@yellow; font-weight:700; }
QTextEdit,QTextBrowser,QLineEdit,QComboBox,QTableWidget { background:@input; color:@text; border:1px solid @border; border-radius:10px; padding:9px; selection-background-color:#b92b43; selection-color:white; }
QTextEdit:focus,QTextBrowser:focus,QLineEdit:focus,QComboBox:focus,QTableWidget:focus { border:1px solid #d84559; }
QLineEdit { min-height:25px; }
QComboBox { min-height:24px; padding-right:24px; }
QComboBox QAbstractItemView { background:@surface; color:@text; selection-background-color:#b92b43; selection-color:white; }
QPushButton { background:@surface; color:@text; border:1px solid @border; border-radius:10px; padding:10px 14px; font-weight:600; }
QPushButton:hover { background:@hover; border-color:#d84559; }
QPushButton:pressed { background:@alternate; }
QPushButton:focus { border:2px solid #d84559; padding:9px 13px; }
QPushButton#primary { background:#bd2c43; color:white; border:1px solid #ee6376; font-weight:700; }
QPushButton#primary:hover { background:#a31f35; border-color:#ffcc55; }
QPushButton#primary:pressed { background:#851b2d; }
QPushButton:disabled { background:@alternate; color:@muted; border:1px solid @border; }
QPushButton#primary:disabled { background:@alternate; color:@muted; border:1px solid @border; }
QHeaderView::section { background:@surface; color:@muted; border:0; border-bottom:1px solid @border; padding:9px; font-weight:600; }
QTableWidget { gridline-color:@border; alternate-background-color:@alternate; }
QTabWidget::pane { border:0; }
QTabBar::tab { background:@surface; color:@muted; padding:10px 15px; margin-right:4px; border-bottom:3px solid transparent; }
QTabBar::tab:selected { color:@text; border-bottom:3px solid #df455b; }
QDockWidget::title { background:#26334c; color:#ffda62; padding:12px; font-weight:700; }
QFrame#chatTitleBar { background:#26334c; }
QFrame#chatTitleBar QLabel { color:#ffda62; font-size:12px; font-weight:700; letter-spacing:1px; }
QWidget#chatBody { background:@surface; }
QWidget#chatBody QComboBox { padding:5px 8px; min-height:20px; }
QWidget#chatBody QPushButton { padding:7px 10px; }
QCheckBox { spacing:8px; padding:6px; }
QCheckBox::indicator { width:16px; height:16px; }
QProgressBar { background:@alternate; border:0; border-radius:4px; }
QProgressBar::chunk { background:#d84559; border-radius:4px; }
QFrame#activityCard { background:transparent; border:1px solid transparent; border-radius:12px; }
QFrame#activityCard[busy="true"] { background:@alternate; border:1px solid #d84559; }
QLabel#activityLabel { color:@muted; font-size:12px; }
QLabel#activityLabel[busy="true"] { color:@text; font-size:14px; font-weight:600; }
QLabel#activityClock { color:@muted; font-size:12px; }
QLabel#activityClock[busy="true"] { color:#ffda62; background:#26334c; border-radius:9px; padding:2px 9px; font-weight:700; }
QLabel#permissionBadge { color:#ffda62; background:#2b2a22; border:1px solid #5a4d22; border-radius:10px; padding:3px 9px; font-size:12px; font-weight:600; }
QLabel#chatNotice { color:@warning; background:@warning_bg; border-radius:9px; padding:5px 9px; font-size:12px; }
QPushButton#chatExpand { background:transparent; color:#ffda62; border:1px solid #4a5a7a; border-radius:8px; padding:3px 10px; font-size:12px; font-weight:600; }
QPushButton#chatExpand:hover { background:#34466a; }
QFrame#settingRow { background:@surface; border:1px solid @border; border-radius:10px; }
QFrame#settingRow QLabel { background:transparent; }
QFrame#settingRow QCheckBox { background:transparent; padding:2px 0; font-weight:600; }
QFrame#binderEmpty { background:transparent; }
QFrame#binderNotice { background:rgba(14,18,27,0.92); border:1px solid #c8a24a; border-radius:14px; }
QFrame#binderNotice QLabel { background:transparent; color:#e8ecf4; }
QFrame#settingRow QRadioButton { background:transparent; padding:2px 0; font-weight:600; spacing:8px; }
QRadioButton::indicator { width:14px; height:14px; border-radius:9px; border:2px solid @border; background:@input; }
QRadioButton::indicator:checked { background:#d84559; border:2px solid #ffda62; }
QLabel#settingTitle { font-weight:600; }
QLabel#settingHint { color:@muted; font-size:12px; }
QPushButton#settingsTab { background:@surface; color:@muted; border:1px solid @border; border-radius:9px; padding:8px 10px; text-align:center; }
QPushButton#settingsTab:hover { background:@hover; color:@text; }
QPushButton#settingsTab:checked { background:#c73148; color:white; border:1px solid #ed5368; }
QPushButton#linkButton { background:transparent; border:0; color:@link; padding:2px 0; text-align:left; }
QPushButton#linkButton:hover { text-decoration:underline; }
QFrame#binderBook { background:qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7a1c2c, stop:1 #4a101b); border:1px solid #9b2c40; border-radius:16px; }
QFrame#binderPage { background:qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #232c3d, stop:1 #1a2130); border:1px solid #11161f; border-radius:10px; }
QFrame#binderSpine { background:qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3a0d16, stop:0.5 #8a2234, stop:1 #3a0d16); border:0; }
QTabWidget#terminalTabs::pane { background:#151a24; border:1px solid @border; border-radius:12px; top:-1px; }
QTabWidget#terminalTabs QTabBar::tab { background:@surface; border-top-left-radius:9px; border-top-right-radius:9px; }
QTabWidget#terminalTabs QTabBar::tab:selected { background:#151a24; color:@text; }
QPushButton#terminalLaunch { padding:8px 14px; }
QPushButton#binderTurn { font-size:20px; font-weight:800; padding:2px 14px; border-radius:16px; }
QScrollArea { border:0; }
QScrollBar:vertical { background:@background; width:11px; margin:0; }
QScrollBar::handle:vertical { background:@border; min-height:25px; border-radius:5px; }
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical { height:0; }
QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical { background:transparent; }
QSplitter::handle { background:@border; }
QStatusBar { background:@surface; color:@muted; border-top:1px solid @border; }
QStatusBar::item { border:0; }
QToolTip { background:#26334c; color:white; border:1px solid #ffcc55; padding:6px; }
'''
    for key in sorted(c, key=len, reverse=True):
        template = template.replace('@' + key, c[key])
    return template


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


def expand_icon(collapse=False):
    """Four corner arrows pointing out (expand) or in (bring back)."""
    picture = QPixmap(32, 32)
    picture.fill(Qt.GlobalColor.transparent)
    p = QPainter(picture)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor('#ffda62'), 2.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
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


def navigation_icon(index):
    if index == 0:
        return logo_icon()
    picture = QPixmap(32, 32)
    picture.fill(Qt.GlobalColor.transparent)
    p = QPainter(picture)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor('#ffda73'), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
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
    return QIcon(picture)


SETTING_TINTS = {'theme': '#b79cff', 'language': '#7cc4ff', 'motion': '#7be0c3', 'images': '#ffb86b',
                 'cloud': '#8ebcff', 'share': '#7be0c3', 'folder': '#ffda73', 'shield': '#ff8493',
                 'key': '#ffda73', 'pulse': '#7be0c3', 'refresh': '#7cc4ff', 'eye': '#b79cff',
                 'database': '#ffb86b', 'copy': '#8ebcff', 'info': '#7cc4ff', 'general': '#ffda73',
                 'coach': '#ff8493', 'battles': '#ffb86b', 'data': '#7be0c3', 'about': '#7cc4ff'}


def setting_icon(kind, size=32):
    """Windows-like settings glyph: a coloured line drawing on a soft rounded tile."""
    tint = QColor(SETTING_TINTS.get(kind, '#ffda73'))
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
    elif kind == 'refresh':
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
