"""Native visual controls; data and decisions remain in the existing services."""
from __future__ import annotations
from pokemind.desktop.i18n import T, J, Text, display

import math

from PySide6.QtCore import (Qt, Signal, QTimer, QElapsedTimer, QSize, QRectF, QRect, QEvent, QPointF, QPoint,
                           Property, QPropertyAnimation, QEasingCurve)
from PySide6.QtGui import (QColor, QPainter, QPen, QPixmap, QIcon, QPalette, QAbstractTextDocumentLayout, QTextTable,
                           QTextBlockFormat, QFontMetricsF,
                           QFont, QFontMetrics, QLinearGradient, QPainterPath, QBrush)
from PySide6.QtWidgets import (QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QFrame, QPushButton, QScrollArea, QGridLayout, QDialog, QSizePolicy,
    QCheckBox, QStyle, QStyleOptionButton, QStylePainter, QStyledItemDelegate, QStyleOptionViewItem,
    QApplication, QLayout, QToolTip, QTabBar, QAbstractButton, QStyleOption)
import html
import re

from PySide6.QtGui import QImage, QTextDocument
from pokemind.desktop.theme import BRAND, colors, theme_of, idea_font
from pokemind.desktop.card_art import CardArt, ZoomImage
from pokemind.desktop.insights import losses_text, opponent_name
from pokemind.desktop.i18n import QWidget, QTextEdit, QTextBrowser, QLabel, QFrame, QPushButton, QDialog, QCheckBox, Painter as QPainter


class WrapCheckBox(QCheckBox):
    """Keep full native checkbox labels readable in a narrow settings page."""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        bounds = self.fontMetrics().boundingRect(QRect(0, 0, max(20, width - 36), 10000),
            Qt.TextFlag.TextWordWrap, self.text())
        return max(30, bounds.height() + 14)

    def sizeHint(self):
        return QSize(300, self.heightForWidth(300))

    def minimumSizeHint(self):
        return QSize(160, 30)

    def hitButton(self, position):
        return self.rect().contains(position)

    def paintEvent(self, event):
        option = QStyleOptionButton()
        self.initStyleOption(option)
        contents = self.style().subElementRect(QStyle.SubElement.SE_CheckBoxContents, option, self)
        option.text = ''
        p = QStylePainter(self)
        p.drawControl(QStyle.ControlElement.CE_CheckBox, option)
        group = QPalette.ColorGroup.Active if self.isEnabled() else QPalette.ColorGroup.Disabled
        p.setPen(self.palette().color(group, QPalette.ColorRole.WindowText))
        p.drawText(contents, Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignVCenter, self.text())
        p.end()


class WrapPushButton(QPushButton):
    """A long button label wraps instead of widening a narrow settings page."""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        bounds = self.fontMetrics().boundingRect(QRect(0, 0, max(20, width - 24), 10000),
            Qt.TextFlag.TextWordWrap, self.text())
        return max(34, bounds.height() + 16)

    def sizeHint(self):
        return QSize(300, self.heightForWidth(300))

    def minimumSizeHint(self):
        return QSize(120, 34)

    def paintEvent(self, event):
        option = QStyleOptionButton()
        self.initStyleOption(option)
        option.text = ''
        p = QStylePainter(self)
        p.drawControl(QStyle.ControlElement.CE_PushButton, option)
        contents = self.style().subElementRect(QStyle.SubElement.SE_PushButtonContents, option, self)
        group = QPalette.ColorGroup.Active if self.isEnabled() else QPalette.ColorGroup.Disabled
        p.setPen(self.palette().color(group, QPalette.ColorRole.ButtonText))
        p.drawText(contents, Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter, self.text())
        p.end()


class ChatInput(QTextEdit):
    send_requested = Signal()
    files_dropped = Signal(object)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.send_requested.emit()
            event.accept()
        else:
            super().keyPressEvent(event)

    @staticmethod
    def local_files(mime):
        urls = mime.urls() if mime.hasUrls() else []
        return [u.toLocalFile() for u in urls] if urls and all(u.isLocalFile() and u.toLocalFile().casefold().endswith(('.txt', '.log')) for u in urls) else []

    def insertFromMimeData(self, source):
        if source.hasUrls() and any(u.isLocalFile() for u in source.urls()):
            self.files_dropped.emit(self.local_files(source))
        elif source.hasText():
            self.insertPlainText(source.text())

    def dragEnterEvent(self, event):
        if self.local_files(event.mimeData()):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if self.local_files(event.mimeData()):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if paths := self.local_files(event.mimeData()):
            self.files_dropped.emit(paths)
            event.acceptProposedAction()
        elif event.mimeData().hasUrls() and any(u.isLocalFile() for u in event.mimeData().urls()):
            event.ignore()
        else:
            super().dropEvent(event)


class Spinner(QWidget):
    """Two rotating arcs, red and yellow, around a white core while the coach works."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(QSize(24, 24))
        self.angle, self.motion = 0, True
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.step)

    def start(self):
        self.show()
        if self.motion:
            self.timer.start()

    def stop(self):
        self.timer.stop()
        self.hide()

    def step(self):
        self.angle = (self.angle + 10) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = QRectF(3, 3, 18, 18)
        for offset, color in ((0, BRAND['bleu_lumineux']), (180, BRAND['gold'])):
            p.setPen(QPen(QColor(color), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawArc(bounds, int((offset - self.angle) * 16), 110 * 16)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(BRAND['bleu_electrique']))
        p.drawEllipse(QRectF(9.5, 9.5, 5, 5))
        p.end()


class RoundedTranscript(QTextBrowser):
    """Native rounded backgrounds behind the existing selectable rich-text document.

    QTextBrowser keeps keyboard/copy, hit testing, safe links, translation and scrolling. Only
    painting changes: transparent message tables lay out text; QPainter supplies real 12px curves.
    https://doc.qt.io/qt-6/qabstracttextdocumentlayout.html (draw / PaintContext / blockBoundingRect)
    """
    PADDING, GAP, WIDTH = 12, 10, 85  # text inside its box, space between boxes, widest box in % (owner, 2026-11-18)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bubble_roles = []
        self.chat_theme = 'dark'
        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)

    def bubble_rects(self):
        """Each message's box: the blocks of its cell, plus the cell padding all round.

        The table's own bounding rectangle is not the bubble: it spans both columns and, with the
        document margin, ran past the right edge; the label then sat on the painted border.
        """
        document = self.document()
        layout = document.documentLayout()
        frames = [f for f in document.rootFrame().childFrames() if isinstance(f, QTextTable)]
        right = document.textWidth() - document.documentMargin() / 2
        result = []
        for frame, role in zip(frames, self.bubble_roles):
            cell = frame.cellAt(0, 1 if role == 'user' else 0)
            block, last = cell.firstCursorPosition().block(), cell.lastCursorPosition().block()
            rect = layout.blockBoundingRect(block)
            while block.isValid() and block != last:
                block = block.next()
                rect = rect.united(layout.blockBoundingRect(block))
            rect = rect.adjusted(-self.PADDING, -self.PADDING, self.PADDING, self.PADDING)
            rect.setRight(min(rect.right(), right))
            result.append((role, rect.adjusted(.5, .5, -.5, -.5)))
        return result

    def space_bubbles(self):
        """Exactly GAP pixels between two boxes: no table margin, a one-pixel paragraph between tables, and
        no paragraph or list margin above the first or below the last line of a message."""
        for frame in self.document().rootFrame().childFrames():
            if isinstance(frame, QTextTable):
                shape = frame.format()
                shape.setTopMargin(0)
                shape.setBottomMargin(self.GAP - 1)  # the separator paragraph is the last pixel
                shape.setLeftMargin(0)
                shape.setRightMargin(0)
                frame.setFormat(shape)
                for column in range(frame.columns()):
                    cell = frame.cellAt(0, column)
                    for cursor, edge in ((cell.firstCursorPosition(), 'setTopMargin'),
                                         (cell.lastCursorPosition(), 'setBottomMargin')):
                        block = cursor.blockFormat()
                        getattr(block, edge)(0)
                        cursor.setBlockFormat(block)
                    # An answer's paragraphs have 140 % line height: the extra leading under the last line is
                    # inside the cell but not in its blocks' rectangles. Take it from the bottom padding.
                    last = cell.lastCursorPosition().block()
                    shape = last.blockFormat()
                    leading = 0.0
                    if (shape.lineHeightType() == QTextBlockFormat.LineHeightTypes.ProportionalHeight.value
                            and shape.lineHeight() > 100):
                        font = last.charFormat().font().resolve(self.document().defaultFont())
                        leading = QFontMetricsF(font).lineSpacing() * (shape.lineHeight() - 100) / 100
                    padding = cell.format().toTableCellFormat()
                    padding.setBottomPadding(max(0.0, self.PADDING - leading))
                    cell.setFormat(padding)

    def paintEvent(self, event):
        # Read-only, so the document has selections but no blinking insertion caret.
        c = colors(self.chat_theme)
        painter = QPainter(self.viewport())
        painter.setClipRect(event.rect())
        painter.fillRect(event.rect(), QColor(c['input']))
        painter.translate(-self.horizontalScrollBar().value(), -self.verticalScrollBar().value())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for role, rect in self.bubble_rects():
            painter.setPen(QPen(QColor(c['border']), 1))
            painter.setBrush(QColor(c['alternate'] if role == 'user' else c['surface']))
            painter.drawRoundedRect(rect, 12, 12)
        context = QAbstractTextDocumentLayout.PaintContext()
        context.palette = self.palette()
        context.clip = QRectF(event.rect()).translated(self.horizontalScrollBar().value(), self.verticalScrollBar().value())
        cursor = self.textCursor()
        if cursor.hasSelection():
            selection = QAbstractTextDocumentLayout.Selection()
            selection.cursor = cursor
            selection.format.setBackground(self.palette().brush(QPalette.ColorRole.Highlight))
            selection.format.setForeground(self.palette().brush(QPalette.ColorRole.HighlightedText))
            context.selections = [selection]
        self.document().documentLayout().draw(painter, context)
        painter.end()


class Activity(QFrame):
    """What the coach is doing, right above the message box: a card while it works."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('activityCard')
        self.setProperty('busy', False)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 7, 10, 7)
        outer.setSpacing(5)
        row = QHBoxLayout()
        row.setSpacing(8)
        self.spinner = Spinner()
        self.spinner.hide()
        self.label = QLabel(T('Prêt'))
        self.label.setObjectName('activityLabel')
        self.label.setWordWrap(True)
        self.label.setAccessibleName(T('Activité du coach et temps écoulé'))
        self.clock = QLabel('')
        self.clock.setObjectName('activityClock')
        row.addWidget(self.spinner)
        row.addWidget(self.label, 1)
        row.addWidget(self.clock)
        outer.addLayout(row)
        self.animation = QProgressBar()
        self.animation.setRange(0, 0)
        self.animation.setTextVisible(False)
        self.animation.setFixedHeight(4)
        outer.addWidget(self.animation)
        self.elapsed, self.timer = QElapsedTimer(), QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.tick)
        self.stage = T('Prêt')
        self.animation.hide()

    def _busy(self, value):
        for widget in (self, self.label, self.clock):
            widget.setProperty('busy', value)
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def start(self, stage):
        self.elapsed.start()
        self.stage = stage
        self._busy(True)
        self.spinner.start()
        self.animation.show()
        self.timer.start()
        self.tick()

    def set_stage(self, stage):
        self.stage = stage
        self.tick()

    def tick(self):
        seconds = self.elapsed.elapsed() // 1000 if self.elapsed.isValid() else 0
        self.label.setText(self.stage)
        self.clock.setText(str(seconds) + ' s' if self.elapsed.isValid() else '')

    def finish(self, stage=T('Terminé')):
        self.stage = stage
        self.timer.stop()
        self.spinner.stop()
        self.animation.hide()
        self._busy(False)
        self.tick()


class WrapItemDelegate(QStyledItemDelegate):
    """Whole entries on several lines in a drop-down list, never cut with '…'."""
    def __init__(self, width, parent=None):
        super().__init__(parent)
        self.width = width

    def sizeHint(self, option, index):
        bounds = option.fontMetrics.boundingRect(QRect(0, 0, self.width - 28, 10000),
            Qt.TextFlag.TextWordWrap, str(index.data() or ''))
        return QSize(self.width, bounds.height() + 16)

    def paint(self, painter, option, index):
        item = QStyleOptionViewItem(option)
        self.initStyleOption(item, index)
        text, item.text = item.text, ''
        style = item.widget.style() if item.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, item, painter, item.widget)
        selected = bool(item.state & QStyle.StateFlag.State_Selected)
        painter.save()
        painter.setPen(item.palette.color(QPalette.ColorRole.HighlightedText if selected else QPalette.ColorRole.Text))
        painter.drawText(item.rect.adjusted(12, 8, -12, -8),
                         int(Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignVCenter), text)
        painter.restore()


class RowDelegate(QStyledItemDelegate):
    """The selected row of a table: the soft fill comes from the style sheet; a lit edge marks its left end."""
    EDGE = 3

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if index.column() == 0 and option.state & QStyle.StateFlag.State_Selected:
            theme = window_theme(option.widget) if option.widget is not None else theme_of(option.palette)
            painter.save()
            painter.fillRect(QRectF(option.rect.left(), option.rect.top() + 5, self.EDGE, option.rect.height() - 10),
                             QColor(colors(theme)['neon']))
            painter.restore()


BAR_ROLES = ('blue', 'red', 'yellow')  # win, loss, unknown in the active theme
BAR_HEIGHT, BAR_GAP, BAR_TRACK_ALPHA = 10, 2, 90  # the Combats bar: thickness, space between segments, track
BAR_MIN = 2  # px: the narrowest segment drawn, so that a value never disappears


def paint_bar(p, rect, values, theme, *, scale=None, reveal=1.0, roles=BAR_ROLES, track=True):
    """The one results bar of the application (owner, 2026-11-19), drawn as the Combats table drew it: a faint
    rounded track, then each value as a segment with rounded ends in its theme colour (blue wins, red losses,
    yellow unknown), with a small gap between two segments.

    `rect` is the whole track; its height is the thickness (BAR_HEIGHT everywhere). `scale` is the value that
    fills the track: the values' own total by default (one row's share), the largest row for a chart that
    compares rows. `reveal` (0 → 1) grows the segments from the left."""
    c = colors(theme)
    radius = rect.height() / 2
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    if track:
        shade = QColor(c['border'])
        shade.setAlpha(BAR_TRACK_ALPHA)
        p.setBrush(shade)
        p.drawRoundedRect(rect, radius, radius)
    shown = [(value, role) for value, role in zip(values or (), roles) if value and value > 0]
    total = scale or sum(value for value, role in shown)
    if shown and total and reveal > 0 and rect.width() > 0:
        edges, left = [], rect.left()
        for value, role in shown:
            right = left + rect.width() * min(1.0, value / total) * reveal
            edges.append([left, right, role])
            left = right
        for number, (start, end, role) in enumerate(edges):
            start += BAR_GAP / 2 if number else 0  # the gap is taken half from each side of a join
            end -= BAR_GAP / 2 if number < len(edges) - 1 else 0
            width = min(max(end - start, BAR_MIN), rect.right() - start)  # a tiny value is still seen
            if width <= 0:
                continue
            corner = min(radius, width / 2)
            p.setBrush(QColor(c[role]))
            p.drawRoundedRect(QRectF(start, rect.top(), width, rect.height()), corner, corner)
    p.restore()


BAR_SCHEME = 'pokemind-bar'


def bar_image(values, theme, width, scale=None, ratio=2):
    """paint_bar as a picture, for the rich text of a page (a bar inside an HTML table): sharp at 200 %."""
    image = QImage(round(width * ratio), round(BAR_HEIGHT * ratio), QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    image.setDevicePixelRatio(ratio)
    p = QPainter(image)
    paint_bar(p, QRectF(0, 0, width, BAR_HEIGHT), values, theme, scale=scale)
    p.end()
    return image


def parse_bar_url(url):
    """« pokemind-bar:dark/1-4-1/220 » → ('dark', (1, 4, 1), 220); None for anything else."""
    found = re.fullmatch(r'(dark|light)/(\d{1,5}(?:-\d{1,5}){0,2})/(\d{1,4})', url.path()) if url.scheme() == BAR_SCHEME else None
    if not found:
        return None
    return found[1], tuple(int(v) for v in found[2].split('-')), max(1, min(2000, int(found[3])))


class PageBrowser(QTextBrowser):
    """A page's rich text. Its « pokemind-bar: » pictures are drawn by paint_bar (the HTML only names the values)."""
    def loadResource(self, kind, url):
        image = getattr(kind, 'value', kind) == QTextDocument.ResourceType.ImageResource.value
        bar = parse_bar_url(url) if image else None
        if bar:
            theme, values, width = bar
            return bar_image(values, theme, width)
        return super().loadResource(kind, url)


def _reading_paragraphs(text):
    lines = [html.escape(line, quote=False) for line in str(text).split('\n')]
    return ''.join('<p style="margin-top:0px; margin-bottom:' + ('0' if last else '4') + 'px;">' + line + '</p>'
                   for last, line in ((n == len(lines) - 1, line) for n, line in enumerate(lines)))


class ReadingLabel(QLabel):
    """Running text set like the Coach's idea buttons (owner, 2026-11-19): their face, size, weight and colour
    from the style sheet (QLabel#readingText), on the left, one paragraph per line of the text. text() gives the
    text back as it was set, line breaks included."""
    def __init__(self, text='', parent=None):
        super().__init__(parent)
        self.setObjectName('readingText')
        self.setWordWrap(True)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._plain = ''
        if text:
            self.setText(text)

    def setText(self, value):
        self._plain = value
        super().setText(Text(_reading_paragraphs(value.fr), _reading_paragraphs(value.en)) if isinstance(value, Text)
                        else _reading_paragraphs(value))

    def text(self):
        return display(self._plain)


def text_bubble(*rows):
    """A block of text in a frame like the Coach's idea buttons: the `panel_start` → `panel_end` gradient, a 1 px
    `neon_soft` line, 10 px corners, 9 × 12 px inside. `rows` are widgets or layouts, top to bottom."""
    frame = QFrame()
    frame.setObjectName('textBubble')
    box = QVBoxLayout(frame)
    box.setContentsMargins(12, 9, 12, 9)
    box.setSpacing(6)
    for row in rows:
        (box.addLayout if isinstance(row, QLayout) else box.addWidget)(row)
    return frame


class RecordBarDelegate(RowDelegate):
    """Wins, losses and unknown results of a row as one coloured bar (paint_bar), with n beside it."""
    ROLES = BAR_ROLES

    def paint(self, painter, option, index):
        item = QStyleOptionViewItem(option)
        self.initStyleOption(item, index)
        item.text = ''
        style = item.widget.style() if item.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, item, painter, item.widget)
        values = []
        for column in (1, 2, 3):
            try:
                values.append(max(0, int(index.siblingAtColumn(column).data() or 0)))
            except (TypeError, ValueError):
                values.append(0)
        total = sum(values)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        text = str(index.data() if index.data() is not None else total)
        width = option.fontMetrics.horizontalAdvance(text) + 12
        bar = QRectF(item.rect.adjusted(8, 0, -width, 0))
        bar.setHeight(BAR_HEIGHT)
        bar.moveLeft(item.rect.left() + 8)
        bar.moveTop(item.rect.center().y() - BAR_HEIGHT / 2)
        if bar.width() > 4:
            paint_bar(painter, bar, values, theme_of(item.palette))
        painter.setPen(item.palette.color(QPalette.ColorRole.Text))
        painter.drawText(QRectF(item.rect).adjusted(0, 0, -6, 0),
                         int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter), text)
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(160, 34)


class TabCloseButton(QAbstractButton):
    """The style's own tab close mark, drawn like Qt's, but inside a holder that keeps it off the tab border."""
    def __init__(self, bar):
        super().__init__()
        self.bar = bar
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def sizeHint(self):
        style = self.bar.style()
        return QSize(style.pixelMetric(QStyle.PixelMetric.PM_TabCloseIndicatorWidth, None, self.bar),
                     style.pixelMetric(QStyle.PixelMetric.PM_TabCloseIndicatorHeight, None, self.bar))

    def enterEvent(self, event):
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        option = QStyleOption()
        option.initFrom(self)
        option.state |= QStyle.StateFlag.State_AutoRaise
        if self.isEnabled() and self.underMouse() and not self.isDown():
            option.state |= QStyle.StateFlag.State_Raised
        if self.isDown():
            option.state |= QStyle.StateFlag.State_Sunken
        current = self.bar.currentIndex()
        if current >= 0 and self.parentWidget() in (self.bar.tabButton(current, side) for side in
                                                    (QTabBar.ButtonPosition.LeftSide, QTabBar.ButtonPosition.RightSide)):
            option.state |= QStyle.StateFlag.State_Selected
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_IndicatorTabClose, option, painter, self)
        painter.end()


class ClosableTabBar(QTabBar):
    """Closable tabs whose × keeps clear of the rounded border. Qt places the close button on the tab's outer
    edge and ignores margins given to QTabBar::close-button in a style sheet: each button sits in a holder with
    a margin on the border side, and a click still emits tabCloseRequested with the tab's current index."""
    MARGIN = 8

    def tabInserted(self, index):
        super().tabInserted(index)
        if not self.tabsClosable():
            return
        side = QTabBar.ButtonPosition(self.style().styleHint(QStyle.StyleHint.SH_TabBar_CloseButtonPosition, None, self))
        native = self.tabButton(index, side)
        if native is None or native.property('tabCloseHolder'):
            return
        holder = QWidget()
        holder.setProperty('tabCloseHolder', True)
        holder.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QHBoxLayout(holder)
        left = side == QTabBar.ButtonPosition.LeftSide
        layout.setContentsMargins(self.MARGIN if left else 2, 0, 2 if left else self.MARGIN, 0)
        button = TabCloseButton(self)
        button.setToolTip(native.toolTip())
        button.setAccessibleName(native.accessibleName())
        layout.addWidget(button)
        button.clicked.connect(lambda checked=False, h=holder: self.close_holder(h))
        self.setTabButton(index, side, holder)  # hides Qt's own button
        native.deleteLater()

    def close_holder(self, holder):
        for index in range(self.count()):
            if holder in (self.tabButton(index, QTabBar.ButtonPosition.LeftSide),
                          self.tabButton(index, QTabBar.ButtonPosition.RightSide)):
                self.tabCloseRequested.emit(index)
                return


def closable_tabs(tabs):
    """Give a QTabWidget closable tabs with the clear × above; use it for every closable tab bar."""
    tabs.setTabBar(ClosableTabBar())
    tabs.setTabsClosable(True)
    return tabs


def wrap_popup(combo, width=440):
    """The closed box stays narrow; its open list shows every entry in full."""
    combo.setItemDelegate(WrapItemDelegate(width, combo))
    view = combo.view()
    view.setMinimumWidth(width)
    view.setTextElideMode(Qt.TextElideMode.ElideNone)
    view.setWordWrap(True)


def paint_glow(painter, rect, radius, color, spread=10, strength=1.0):
    """A soft light outside a rounded rectangle: stacked translucent strokes. A style sheet has no shadow and a
    QGraphicsEffect would re-render whole panels; the caller keeps `spread` pixels free around `rect`."""
    painter.save()
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for step in range(spread, 0, -1):
        tint = QColor(color)
        tint.setAlphaF(min(1.0, strength * .2 * (1 - step / (spread + 1)) ** 2))
        painter.setPen(QPen(tint, 2 * step))
        painter.drawRoundedRect(rect, radius, radius)
    painter.restore()


def window_theme(widget):
    """Theme of the window a widget sits in: a transparent widget's own palette no longer tells it."""
    return theme_of(widget.window().palette())


def glow_strength(theme):
    return 1.0 if theme == 'dark' else .55  # the same light reads stronger on a pale background


class GlowPanel(QFrame):
    """A large rounded panel: fill, neon line and outer glow painted here, in the active theme.

    `open_top` / `open_bottom` leave that side without a line, so a dock title bar and its body read as one panel.
    The layout of the panel keeps `spread` pixels and a little more free on the closed sides."""
    def __init__(self, parent=None, *, fill='background', radius=18, spread=10, open_top=False, open_bottom=False,
                 underline=False):
        super().__init__(parent)
        self.fill, self.radius, self.spread = fill, radius, spread
        self.open_top, self.open_bottom, self.underline = open_top, open_bottom, underline

    def frame_rect(self):
        room = self.spread + .5
        rect = QRectF(self.rect()).adjusted(room, room, -room, -room)
        reach = self.radius + self.spread + 4
        if self.open_top:
            rect.setTop(-reach)
        if self.open_bottom:
            rect.setBottom(self.height() + reach)
        return rect

    def paintEvent(self, event):
        theme = theme_of(self.palette())
        c = colors(theme)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.frame_rect()
        paint_glow(p, rect, self.radius, c['neon'], self.spread, glow_strength(theme))
        if self.fill == 'panel':
            brush = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            brush.setColorAt(0, QColor(c['panel_start']))
            brush.setColorAt(1, QColor(c['panel_end']))
        else:
            brush = QColor(c[self.fill])
        p.setPen(QPen(QColor(c['neon']), 1.4))
        p.setBrush(brush)
        p.drawRoundedRect(rect, self.radius, self.radius)
        if self.underline:  # a title bar: a quiet line between it and the body
            p.setPen(QPen(QColor(c['neon_soft']), 1))
            p.drawLine(QPointF(rect.left() + 1, self.height() - .5), QPointF(rect.right() - 1, self.height() - .5))
        p.end()


class GlowFrame(QWidget):
    """The lit rounded frame of the page area, laid over a widget it does not own.

    The pages keep their geometry: the frame is drawn in their outer margin (`ROOM` pixels), and what lies
    outside its rounded line is covered with the window colour. Mouse and keyboard go through."""
    ROOM, RADIUS = 10, 18

    def __init__(self, target):
        super().__init__(target.parentWidget())
        self.target, self._cache, self._key = target, QPixmap(), None
        self.setObjectName('glowFrame')
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        target.installEventFilter(self)
        self.follow()

    def eventFilter(self, watched, event):
        if watched is self.target and event.type() in (QEvent.Type.Resize, QEvent.Type.Move, QEvent.Type.Show):
            self.follow()
        return False

    def follow(self):
        self.setGeometry(self.target.geometry())
        self.raise_()

    def paintEvent(self, event):
        theme = window_theme(self)
        ratio = self.devicePixelRatioF()
        key = (self.width(), self.height(), theme, ratio)
        if key != self._key:  # redrawn only when the size or the theme changes
            self._key, c = key, colors(theme)
            self._cache = QPixmap(self.size() * ratio)
            self._cache.setDevicePixelRatio(ratio)
            self._cache.fill(Qt.GlobalColor.transparent)
            p = QPainter(self._cache)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            room = self.ROOM + .5
            rect = QRectF(self.rect()).adjusted(room, room, -room, -room)
            outside = QPainterPath()
            outside.addRect(QRectF(self.rect()))
            line = QPainterPath()
            line.addRoundedRect(rect, self.RADIUS, self.RADIUS)
            outside = outside.subtracted(line)
            p.fillPath(outside, QColor(c['background']))
            p.setClipPath(outside)
            paint_glow(p, rect, self.RADIUS, c['neon'], self.ROOM, glow_strength(theme))
            p.setClipping(False)
            p.setPen(QPen(QColor(c['neon']), 1.4))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(rect, self.RADIUS, self.RADIUS)
            p.end()
        p = QPainter(self)
        p.drawPixmap(0, 0, self._cache)
        p.end()


class NavigationDelegate(QStyledItemDelegate):
    """The main menu rows, painted here so the active one is lit from outside (glow, not only a border)."""
    ROW, SIDE, GAP, RADIUS = 50, 8, 3, 12
    SHORT = 44  # a low window (with the short « Deck actif » card): the whole menu still shows, without a bar
    row = ROW

    def sizeHint(self, option, index):
        return QSize(40, self.row)

    def box(self, rect):
        return QRectF(rect).adjusted(self.SIDE, self.GAP, -self.SIDE, -self.GAP)

    def paint(self, painter, option, index):
        item = QStyleOptionViewItem(option)
        self.initStyleOption(item, index)
        theme = window_theme(item.widget) if item.widget else theme_of(item.palette)
        c = colors(theme)
        selected = bool(item.state & QStyle.StateFlag.State_Selected)
        box = self.box(item.rect)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # The light of the active row is wider than the row. Each row paints, inside its own rectangle only, the
        # part of that light that falls on it: whatever Qt repaints, the menu shows the same picture, and no light
        # of a former selection is left on a neighbour (« Vue d’ensemble » looked still lit: owner, 2026-11-16).
        painter.setClipRect(item.rect, Qt.ClipOperation.IntersectClip)
        view = item.widget
        lit = [box] if selected else []
        if view is not None and hasattr(view, 'selectionModel') and view.selectionModel() is not None:
            for step in (-1, 1):
                neighbour = index.siblingAtRow(index.row() + step)
                if neighbour.isValid() and view.selectionModel().isSelected(neighbour):
                    lit.append(self.box(view.visualRect(neighbour)))
        for glow in lit:
            paint_glow(painter, glow, self.RADIUS, c['neon'], self.SIDE, glow_strength(theme) * 1.25)
        if selected:
            fill = QLinearGradient(box.topLeft(), box.topRight())
            fill.setColorAt(0, QColor(c['primary']))
            fill.setColorAt(1, QColor(c['primary_glow']))
            painter.setPen(QPen(QColor(c['neon_hi']), 1.2))
            painter.setBrush(fill)
            painter.drawRoundedRect(box, self.RADIUS, self.RADIUS)
        elif item.state & QStyle.StateFlag.State_MouseOver:
            painter.setPen(QPen(QColor(c['neon_soft']), 1))
            painter.setBrush(QColor(c['hover']))
            painter.drawRoundedRect(box, self.RADIUS, self.RADIUS)
        if item.state & QStyle.StateFlag.State_HasFocus:
            painter.setPen(QPen(QColor(c['focus']), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(box.adjusted(.5, .5, -.5, -.5), self.RADIUS, self.RADIUS)
        size = item.decorationSize
        picture = item.icon.pixmap(size, QIcon.Mode.Selected if selected else QIcon.Mode.Normal)
        if item.text:
            left = box.left() + 12
            painter.drawPixmap(QRectF(left, box.center().y() - size.height() / 2, size.width(), size.height()).toRect(), picture)
            font = idea_font(item.font)  # every row, selected or not (owner, 2026-11-19)
            painter.setFont(font)
            painter.setPen(QColor(c['on_primary'] if selected else c['text']))
            room = QRectF(left + size.width() + 10, box.top(), box.right() - left - size.width() - 16, box.height())
            text = QFontMetrics(font).elidedText(item.text, Qt.TextElideMode.ElideRight, int(room.width()))
            painter.drawText(room, int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft), text)
        else:  # folded menu: the glyph alone, centred
            painter.drawPixmap(QRectF(box.center().x() - size.width() / 2, box.center().y() - size.height() / 2,
                                      size.width(), size.height()).toRect(), picture)
        painter.restore()


class InfoButton(QPushButton):
    """« ⓘ » beside a title: a caution that used to be printed on the page, shown on hover, click or keyboard.

    Drawn here (a circle and an « i ») so it follows the theme and needs no symbol font."""
    def __init__(self, tip='', parent=None):
        super().__init__(parent)
        self.setObjectName('infoButton')
        self.setFixedSize(24, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setAccessibleName(T('Plus d’information', en='More information'))
        self.clicked.connect(self.show_tip)
        self.set_tip(tip)

    def set_tip(self, tip):
        self.setToolTip(tip)
        self.setAccessibleDescription(tip)

    def show_tip(self):
        QToolTip.showText(self.mapToGlobal(QPoint(0, self.height() + 2)), self.toolTip(), self)

    def paintEvent(self, event):
        c = colors(window_theme(self))
        hot = self.underMouse() or self.hasFocus()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(3.5, 3.5, -3.5, -3.5)
        p.setPen(QPen(QColor(c['focus' if self.hasFocus() else 'neon' if hot else 'muted']), 1.4))
        p.setBrush(QColor(c['hover']) if hot else Qt.BrushStyle.NoBrush)
        p.drawEllipse(rect)
        p.setFont(idea_font(self.font()))
        p.setPen(QColor(c['text' if hot else 'muted']))
        p.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), 'i')
        p.end()


def title_row(label, info, wrap=False):
    """A title and its « ⓘ » on one line; `wrap` gives a long, word-wrapped title the whole row."""
    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(8)
    row.addWidget(label, 1 if wrap else 0)
    row.addWidget(info, 0, Qt.AlignmentFlag.AlignTop if wrap else Qt.AlignmentFlag.AlignVCenter)
    if not wrap:
        row.addStretch(1)
    return row


class ClampLabel(QWidget):
    """Plain text on at most `lines` lines; the last one ends with « … » instead of being cut. Set like the idea
    buttons (owner, 2026-11-19); `title` (pixel size, weight) only for a title, which then has a name of
    theme.TITLE_NAMES. `fit`: as tall as the lines the text takes at its width (at most `lines`), so that a longer
    text in the semibold face wraps instead of ending in « … »."""
    def __init__(self, role='text', lines=1, *, title=None, fit=False, align=Qt.AlignmentFlag.AlignLeft, parent=None):
        super().__init__(parent)
        self.role, self.align, self._text, self.title, self.fit = role, align, '', title, fit
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.set_lines(lines)

    def text_font(self):
        font = idea_font(self.font())
        if self.title:
            font.setPixelSize(self.title[0])
            font.setWeight(QFont.Weight(self.title[1]))
        return font

    def step(self):
        return QFontMetrics(self.text_font()).lineSpacing()

    def height_for(self, width, lines=None):
        """The height of the text at `width`: every line it takes, up to `lines` (by default its own)."""
        lines = lines or self.lines
        taken = len(self.rows(width, lines)) if self.fit else lines
        return self.step() * max(1, taken) + 2

    def refit(self):
        self.setFixedHeight(self.height_for(max(1, self.width())))
        self.update()

    def set_lines(self, lines):
        self.lines = lines
        self.refit()

    def setText(self, text):
        self._text = text
        self.refit()

    def text(self):
        return display(self._text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.fit and event.size().width() != event.oldSize().width():
            self.refit()

    def rows(self, width, lines=None, text=None):
        """The lines drawn at `width` (at most `lines`, by default its own); `text` instead of its own text."""
        lines = lines or self.lines
        rows, cut = [], False
        metrics = QFontMetrics(self.text_font())
        for paragraph in (self.text() if text is None else text).split('\n'):  # a line break in the text is kept
            words = paragraph.split()
            while words and len(rows) < lines:
                row = words.pop(0)
                while words and metrics.horizontalAdvance(row + ' ' + words[0]) <= width:
                    row += ' ' + words.pop(0)
                rows.append(row)
            cut = cut or bool(words)
        if rows:
            rows[-1] = metrics.elidedText(rows[-1] + (' …' if cut else ''), Qt.TextElideMode.ElideRight, width)
        return rows

    def paintEvent(self, event):
        p = QPainter(self)
        p.setFont(self.text_font())
        p.setPen(QColor(colors(window_theme(self))[self.role]))
        step = self.step()
        for index, row in enumerate(self.rows(self.width())):
            p.drawText(QRect(0, index * step, self.width(), step), int(self.align | Qt.AlignmentFlag.AlignVCenter), row)
        p.end()


RING_ROLES = ('blue', 'red', 'yellow')  # win, loss, unknown in the active theme


def paint_donut(p, rect, values, theme, *, stroke, reveal=1.0, number=None, label=None, glow=True):
    """A thick results ring: rounded ends, a small gap between segments, a light gradient along each one and a
    soft glow in its own palette colour; a large number and a small word in the middle (never a percentage).
    `rect` is the circle through the middle of the stroke; `reveal` (0 → 1) fills it clockwise from the top."""
    c = colors(theme)
    radius = rect.width() / 2
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(Qt.BrushStyle.NoBrush)
    track = QColor(c['border'])
    track.setAlpha(150)
    p.setPen(QPen(track, stroke))
    p.drawEllipse(rect)
    shown = [(value, role) for value, role in zip(values or (), RING_ROLES) if value > 0]
    total = sum(value for value, role in shown)
    if total and reveal > 0:
        gap = 0.0 if len(shown) == 1 else math.degrees(max(3.0, stroke * .35) / radius)  # a few pixels on the ring
        cap = math.degrees(stroke / 2 / radius)  # how far a rounded end reaches past its angle
        start = 90.0
        strength = glow_strength(theme)
        for value, role in shown:
            span = value / total * 360 * reveal
            colour = QColor(c[role])
            if len(shown) == 1 and reveal >= 1:
                segments = [(90.0, -360.0, Qt.PenCapStyle.FlatCap)]
            else:
                inner = span - gap - 2 * cap
                middle = start - span / 2
                segments = [(start - gap / 2 - cap, -inner, Qt.PenCapStyle.RoundCap)] if inner > 0 else \
                    [(middle, 0.0, Qt.PenCapStyle.RoundCap)] if span >= gap else []
            for begin, length, cap_style in segments:
                if glow:
                    for step in range(4, 0, -1):
                        halo = QColor(colour)
                        halo.setAlphaF(min(1.0, strength * .07 * (5 - step) / 4))
                        p.setPen(QPen(halo, stroke + step * 3, Qt.PenStyle.SolidLine, cap_style))
                        draw_ring_arc(p, rect, begin, length)
                head = arc_point(rect, begin)
                tail = arc_point(rect, begin + length)
                whole = abs(length) >= 359.9  # one result only: the light runs across the ring, not along it
                shade = QLinearGradient(rect.topLeft(), rect.bottomRight()) if whole else QLinearGradient(head, tail)
                shade.setColorAt(0, colour.lighter(128))
                shade.setColorAt(1, colour)
                p.setPen(QPen(QBrush(shade), stroke, Qt.PenStyle.SolidLine, cap_style))
                draw_ring_arc(p, rect, begin, length)
            start -= span
    if number is not None:
        big = QFont(p.font())
        big.setPixelSize(max(12, round(radius * (.62 if label else .7))))
        big.setWeight(QFont.Weight.Bold)
        small = idea_font(p.font())  # the word under the number: the text of the application
        high = QFontMetricsF(big).height()
        low = QFontMetricsF(small).height() if label else 0
        top = rect.center().y() - (high + low) / 2
        p.setFont(big)
        p.setPen(QColor(c['text']))
        p.drawText(QRectF(rect.left(), top, rect.width(), high), int(Qt.AlignmentFlag.AlignCenter), str(number))
        if label:
            p.setFont(small)
            p.setPen(QColor(c['text']))
            p.drawText(QRectF(rect.left() - stroke, top + high - 2, rect.width() + 2 * stroke, low),
                       int(Qt.AlignmentFlag.AlignCenter), label)
    p.restore()


def games_word(total):
    return T('partie', en='game') if total == 1 else T('parties', en='games')


def arc_point(rect, degrees):
    angle = math.radians(degrees)
    return QPointF(rect.center().x() + rect.width() / 2 * math.cos(angle),
                   rect.center().y() - rect.height() / 2 * math.sin(angle))


def draw_ring_arc(p, rect, begin, length):
    """A zero-length arc with a rounded pen is a dot: a value too small for a segment still shows."""
    if abs(length) < .01:
        p.drawPoint(arc_point(rect, begin))
    else:
        p.drawArc(rect, round(begin * 16), round(length * 16))


class RingFill:
    """The ring fills from 0 when it first shows its numbers; at once with « Réduire les animations »."""
    def __init__(self, widget, duration=650):
        self.widget, self.value, self.motion_enabled = widget, 1.0, True
        self.animation = QPropertyAnimation(widget, b'reveal', widget)
        self.animation.setDuration(duration)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def start(self):
        self.animation.stop()
        if self.motion_enabled and self.widget.isVisible():
            self.animation.setStartValue(0.0)
            self.animation.setEndValue(1.0)
            self.animation.start()
        else:
            self.widget.set_reveal(1.0)

    def set_motion_enabled(self, enabled):
        self.motion_enabled = enabled
        if not enabled:
            self.animation.stop()
            self.widget.set_reveal(1.0)


class RecordRing(QWidget):
    """Recorded wins, losses and unknown results as a ring. Counts only: PokeMind infers no global win rate."""
    ROLES = RING_ROLES

    def __init__(self, parent=None):
        super().__init__(parent)
        self.values = None  # (wins, losses, unknown), or None before any report
        self._reveal = 1.0
        self.fill = RingFill(self)
        self.setFixedSize(92, 92)

    def set_reveal(self, value):
        self._reveal = value
        self.update()

    reveal = Property(float, lambda self: self._reveal, set_reveal)

    def set_motion_enabled(self, enabled):
        self.fill.set_motion_enabled(enabled)

    def set_values(self, values):
        changed = values != self.values
        self.values = values
        if changed and values:
            self.fill.start()
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        if self.values:
            self.fill.start()

    def hideEvent(self, event):
        self.fill.animation.stop()
        self.set_reveal(1.0)
        super().hideEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        side = min(self.width(), self.height())
        stroke = max(7.0, side * .15)
        room = stroke / 2 + (5 if side >= 80 else 2)  # the glow stays inside the widget
        rect = QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side).adjusted(room, room, -room, -room)
        # The small ring of the short sidebar leaves its numbers to the caption.
        total = sum(self.values) if self.values else None
        number = (total if total is not None else '—') if side >= 80 else None
        paint_donut(p, rect, self.values, window_theme(self), stroke=stroke, reveal=self._reveal, number=number,
                    label=games_word(total) if side >= 80 else None, glow=side >= 80)
        p.end()


class ActiveDeckCard(QFrame):
    """Sidebar card: the deck open in Deck Lab, with the recorded results of the season shown.

    It only displays what the window already knows: a deck row, a picture the gallery fetched, report counts."""
    activated = Signal()
    ROOM = 8  # glow room around the painted box

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('activeDeck')
        self.compact, self.record, self.this_deck = False, None, False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(T('Ouvrir ce deck dans Deck Lab', en='Open this deck in Deck Lab'))
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(self.ROOM + 12, self.ROOM + 10, self.ROOM + 12, self.ROOM + 12)
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(7)
        self.title = QLabel(T('Deck actif', en='Active deck'))
        self.title.setObjectName('activeDeckTitle')
        self.cover = QLabel()
        self.cover.setFixedSize(44, 62)
        self.cover.setObjectName('activeDeckCover')
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Set like the rest of the text (owner, 2026-11-19): each line wraps whole, the card as tall as it needs.
        self.name = ClampLabel('text', 2, fit=True)
        self.detail = ClampLabel('text', 2, fit=True)
        self.words = QVBoxLayout()
        self.words.setSpacing(2)
        self.words.addStretch()
        self.words.addWidget(self.name)
        self.words.addWidget(self.detail)
        self.words.addStretch()
        self.ring = RecordRing()
        self.caption = ClampLabel('text', 3, fit=True, align=Qt.AlignmentFlag.AlignHCenter)
        self.picture = QPixmap()
        self.set_record(None)  # its tooltip says what the ring counts
        self.set_deck(None)
        self.set_cover(None)
        self.arrange()

    def arrange(self):
        for item in (self.title, self.cover, self.ring, self.caption):
            self.grid.removeWidget(item)
        self.grid.removeItem(self.words)
        self.grid.addWidget(self.title, 0, 0, 1, 2)
        if self.compact:  # short window: ring beside the name, the counts and whose games they are under it
            self.ring.setFixedSize(50, 50)
            self.grid.addWidget(self.ring, 1, 0)
            self.grid.addLayout(self.words, 1, 1)
            self.caption.align = Qt.AlignmentFlag.AlignLeft
            self.caption.set_lines(2)
            self.grid.addWidget(self.caption, 2, 0, 1, 2)
        else:
            self.ring.setFixedSize(92, 92)
            self.grid.addWidget(self.cover, 1, 0)
            self.grid.addLayout(self.words, 1, 1)
            self.grid.addWidget(self.ring, 2, 0, 1, 2, Qt.AlignmentFlag.AlignHCenter)
            self.caption.align = Qt.AlignmentFlag.AlignHCenter
            self.caption.set_lines(3)
            self.grid.addWidget(self.caption, 3, 0, 1, 2)
        self.cover.setVisible(not self.compact)
        self.grid.setColumnStretch(1, 1)
        self.show_record()

    def set_compact(self, compact):
        if compact != self.compact:
            self.compact = compact
            self.arrange()

    def set_deck(self, name, detail=''):
        self.name.setText(name if name else T('Aucun deck', en='No deck'))
        self.detail.setText(detail if name else T('Ajoute-le dans Deck Lab', en='Add it in Deck Lab'))
        self.setAccessibleName(T('Deck actif : ', en='Active deck: ') + (name or T('aucun', en='none')))

    def set_cover(self, picture):
        """A card picture the gallery already holds (ImageCache); a plain sleeve when there is none."""
        self.picture = show_cover(self.cover, picture)

    def set_record(self, outcomes, this_deck=False):
        """`this_deck`: the counts are the games known to be played with this deck; otherwise all the games."""
        self.record = (tuple(max(0, int(outcomes.get(key, 0) or 0)) for key in ('wins', 'losses', 'unknown'))
                       if outcomes else None)
        self.this_deck = bool(this_deck and self.record is not None)
        self.ring.setToolTip(
            T('Parties jouées avec ce deck, quand le journal le dit.\nNombres observés seulement : aucun taux de victoire inféré.',
              en='Games played with this deck, when the log says so.\nObserved counts only: no win rate is inferred.')
            if self.this_deck else
            T('Toutes les parties enregistrées de la saison affichée, pas seulement ce deck : tes journaux ne disent pas '
              'avec quel deck chaque partie a été jouée.\nNombres observés seulement : aucun taux de victoire inféré.',
              en='Every recorded game of the season shown, not only this deck: your logs do not say which deck each '
                 'game was played with.\nObserved counts only: no win rate is inferred.'))
        self.show_record()

    def _record(self):
        """Whose games the ring counts, the wins and losses, and the games without result, in words."""
        wins, losses, unknown = self.record
        scope = (T('Parties avec ce deck', en='Games with this deck') if self.this_deck
                 else T('Toutes mes parties, tous decks', en='All my games, every deck'))
        extra = (str(unknown) + T(' sans résultat', en=' without result')) if unknown else ''
        counts = str(wins) + ' ' + T('V', en='W') + ' · ' + str(losses) + ' ' + T('D', en='L')
        return scope, counts, extra

    def record_words(self, compact):
        """The words under the ring (tall form) or under the name (short form)."""
        if self.record is None:
            return T('Aucune partie enregistrée', en='No recorded game')
        # Without a game known to be played with this deck, the words say these are all the games, whatever the deck.
        scope, counts, extra = self._record()
        if compact:  # the counts, then whose games they are, each on its own line
            return counts + '\n' + (T('Avec ce deck', en='With this deck') if self.this_deck
                                    else T('Toutes mes parties', en='All my games'))
        # The ring holds the number of games; its wins and losses are written under it.
        return counts + (' · ' + extra if extra else '') + '\n' + scope

    def tall_height(self, width=None):
        """The card's height in its tall form at `width` (its own by default): the window compares it with the
        room the menu leaves."""
        margins, gap = self.grid.contentsMargins(), self.grid.verticalSpacing()
        inner = max(1, (width or self.width()) - margins.left() - margins.right())
        words = max(1, inner - self.cover.width() - self.grid.horizontalSpacing())
        caption = self.caption.step() * max(1, len(self.caption.rows(inner, 3, display(self.record_words(False))))) + 2
        return (margins.top() + margins.bottom() + self.title.sizeHint().height() + gap
                + max(self.cover.height(), self.name.height_for(words) + self.words.spacing()
                      + self.detail.height_for(words)) + gap + 92 + gap + caption)

    def show_record(self):
        self.ring.set_values(self.record)
        self.caption.setText(self.record_words(self.compact))
        if self.record is None:
            self.ring.setAccessibleName(T('Aucune partie enregistrée', en='No recorded game'))
            return
        scope, counts, extra = self._record()
        self.ring.setAccessibleName(scope + ' · ' + str(sum(self.record)) + ' · ' + counts + (' · ' + extra if extra else ''))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.activated.emit()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        theme = window_theme(self)
        c = colors(theme)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        room = self.ROOM + .5
        rect = QRectF(self.rect()).adjusted(room, room, -room, -room)
        paint_glow(p, rect, 14, c['neon'], self.ROOM, glow_strength(theme) * .8)
        fill = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        fill.setColorAt(0, QColor(c['panel_start']))
        fill.setColorAt(1, QColor(c['panel_end']))
        p.setPen(QPen(QColor(c['neon_soft']), 1.2))
        p.setBrush(fill)
        p.drawRoundedRect(rect, 14, 14)
        p.end()


class CorpusChart(QWidget):
    def __init__(self):
        super().__init__()
        self.report = None
        self.theme = 'dark'
        self.motion_enabled, self._reveal = True, 1.0
        self.animation = QPropertyAnimation(self, b'reveal', self)
        self.animation.setDuration(600)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.setMinimumHeight(180)
        self.setAccessibleName(T('Répartition de tes parties enregistrées et défaites par deck adverse'))

    def set_report(self, report):
        self.report = report
        self.animate_report()
        self.update()

    def set_reveal(self, value):
        self._reveal = value
        self.update()

    reveal = Property(float, lambda self: self._reveal, set_reveal)

    def animate_report(self):
        self.animation.stop()
        if self.motion_enabled and self.isVisible() and self.report:
            self.animation.setStartValue(0.0)
            self.animation.setEndValue(1.0)
            self.animation.start()
        else:
            self.set_reveal(1.0)

    def set_motion_enabled(self, enabled):
        self.motion_enabled = enabled
        if not enabled:
            self.animation.stop()
            self.set_reveal(1.0)

    def showEvent(self, event):
        super().showEvent(event)
        self.animate_report()

    def hideEvent(self, event):
        self.animation.stop()
        self.set_reveal(1.0)
        super().hideEvent(event)

    def set_theme(self, theme):
        self.theme = theme
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        theme = colors(self.theme)
        o = (self.report or {}).get('outcomes', {})
        values = [max(0, int(o.get(k, 0) or 0)) for k in ('wins', 'losses', 'unknown')]
        total = sum(values)
        rect = QRectF(31, 38, 104, 104)  # through the middle of a 24 px ring, with room for its glow
        paint_donut(p, rect, values, self.theme, stroke=24, reveal=self._reveal, number=total,
                    label=games_word(total))
        # The tiles above already give the wins and the losses in figures: the ring only shows their share.
        groups = (self.report or {}).get('groups', [])[:4]
        if self.width() > 400:
            # Labels like the Coach's idea buttons, bars drawn by paint_bar like the Combats table (owner, 2026-11-19).
            x, width = 180, max(40, self.width() - 200)
            p.setFont(idea_font(self.font()))
            p.setPen(QColor(theme['muted']))
            p.drawText(QRectF(x, 0, width, 20), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                       display(T('Défaites par deck adverse')))  # the caption of the bars: grey, same face
            metrics = p.fontMetrics()
            maximum = max([g['losses'] for g in groups] or [1]) or 1
            for i, g in enumerate(groups):
                y = 24 + i * 38
                p.setPen(QColor(theme['text']))
                record = display(losses_text(g['losses'], g['n']))
                label = metrics.elidedText(display(opponent_name(g['archetype'])), Qt.TextElideMode.ElideRight,
                                           max(25, width - metrics.horizontalAdvance(' · ' + record)))
                p.drawText(QRectF(x, y, width, 20), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                           label + ' · ' + record)
                paint_bar(p, QRectF(x, y + 22, width, BAR_HEIGHT), (0, g['losses']), self.theme, scale=maximum,
                          reveal=self._reveal)
        p.end()


class Pill(QWidget):
    """A small rounded label for one real attribute of the deck shown; a text too long ends with « … »."""
    def __init__(self, role='text', parent=None):
        super().__init__(parent)
        self.role, self._text = role, ''
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def text_font(self):
        return idea_font(self.font())

    def setText(self, text):
        self._text = text
        self.setToolTip(text)
        self.setAccessibleName(text)
        self.updateGeometry()
        self.update()

    def text(self):
        return display(self._text)

    def sizeHint(self):
        metrics = QFontMetrics(self.text_font())
        return QSize(metrics.horizontalAdvance(self.text()) + 24, metrics.height() + 6)

    def minimumSizeHint(self):
        return QSize(44, self.sizeHint().height())

    def _retranslate(self):
        super()._retranslate()
        self.updateGeometry()

    def paintEvent(self, event):
        c = colors(window_theme(self))
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        p.setPen(QPen(QColor(c['neon_soft']), 1))
        p.setBrush(QColor(c['input']))
        p.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        font = self.text_font()
        p.setFont(font)
        p.setPen(QColor(c[self.role]))
        room = self.rect().adjusted(11, 0, -11, 0)
        p.drawText(room, int(Qt.AlignmentFlag.AlignCenter),
                   QFontMetrics(font).elidedText(self.text(), Qt.TextElideMode.ElideRight, room.width()))
        p.end()


class FlowLayout(QLayout):
    """Items in a row that wraps; one wider than the row is given the row (its text is then elided).
    Below `drop_below` pixels of width, the widgets listed in `optional` are left out to save rows."""
    def __init__(self, spacing=5, drop_below=0):
        super().__init__()
        self.items, self.optional, self.drop_below = [], [], drop_below
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(spacing)

    def addItem(self, item):
        self.items.append(item)
        self.invalidate()

    def count(self):
        return len(self.items)

    def itemAt(self, index):
        return self.items[index] if 0 <= index < len(self.items) else None

    def takeAt(self, index):
        return self.items.pop(index) if 0 <= index < len(self.items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def shown(self):
        return [item for item in self.items if not (item.widget() and item.widget().isHidden())]

    def sizeHint(self):
        sizes = [item.sizeHint() for item in self.shown()]
        return QSize(sum(s.width() for s in sizes) + self.spacing() * max(0, len(sizes) - 1),
                     max((s.height() for s in sizes), default=0))

    def minimumSize(self):
        sizes = [item.minimumSize() for item in self.shown()]
        return QSize(max((s.width() for s in sizes), default=0), max((s.height() for s in sizes), default=0))

    def heightForWidth(self, width):
        return self.arrange(QRect(0, 0, width, 0), False)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.arrange(rect, True)

    def arrange(self, rect, apply):
        x, y, row, gap = rect.x(), rect.y(), 0, self.spacing()
        for item in self.shown():
            if rect.width() < self.drop_below and item.widget() in self.optional:
                if apply:
                    item.setGeometry(QRect(rect.x(), rect.y(), 0, 0))
                continue
            size = item.sizeHint()
            width = min(size.width(), rect.width())
            if x > rect.x() and x + width > rect.x() + rect.width():
                x, y, row = rect.x(), y + row + gap, 0
            if apply:
                item.setGeometry(QRect(x, y, width, size.height()))
            x, row = x + width + gap, max(row, size.height())
        return y + row - rect.y()


class WrapRow(QWidget):
    """A row of buttons that goes to the next line rather than cut their words (FlowLayout), taller as needed.
    It still asks for the width of the whole row, as the plain row did: that width sets how wide the pages are
    beside the Coach (the Deck Lab gallery counts on it), so nothing moves at the usual size. It wraps only when
    the window leaves the page less than that (1100 × 700), where a plain row cut the words."""
    def __init__(self, spacing=6):
        super().__init__()
        self.flow = FlowLayout(spacing)
        self.setLayout(self.flow)

    def hasHeightForWidth(self):
        return False

    def sizeHint(self):
        return self.flow.sizeHint()

    def minimumSizeHint(self):
        return QSize(self.flow.sizeHint().width(), self.flow.minimumSize().height())

    def event(self, event):
        handled = super().event(event)
        if event.type() == QEvent.Type.LayoutRequest:  # a button's words changed (language): new width for the page
            self.updateGeometry()
        return handled

    def resizeEvent(self, event):
        super().resizeEvent(event)
        height = self.flow.heightForWidth(self.width())
        if height != self.minimumHeight():
            self.setMinimumHeight(height)


def wanted_width(widget):
    """The width a control needs to show its words in full: a list box its longest choice (padding and arrow
    as in fit_combo), anything else its size hint."""
    from PySide6.QtWidgets import QComboBox
    if isinstance(widget, QComboBox):
        metrics = widget.fontMetrics()
        widest = max((metrics.horizontalAdvance(widget.itemText(i)) for i in range(widget.count())), default=0)
        return max(widest + 66, widget.minimumSizeHint().width())
    return widget.sizeHint().width()


class StackRow(QWidget):
    """A row whose last controls go to a second line when the page is too narrow to show every word (1100 × 700
    in French, Coach docked: owner, 2026-11-19), rather than cutting them or making the page scroll sideways.
    Wide enough, it is the plain row: `leading` and `trailing` are (widget, stretch) pairs, left to right."""
    def __init__(self, leading, trailing, spacing=6):
        super().__init__()
        self.leading, self.trailing = leading, trailing
        self.box = QVBoxLayout(self)
        self.box.setContentsMargins(0, 0, 0, 0)
        self.top, self.bottom = QHBoxLayout(), QHBoxLayout()
        for line in (self.top, self.bottom):
            line.setContentsMargins(0, 0, 0, 0)
            line.setSpacing(spacing)
            self.box.addLayout(line)
        for widget, stretch in leading + trailing:
            self.top.addWidget(widget, stretch)
        self.bottom.addStretch(1)
        self.spacing, self.two_lines = spacing, False
        self.box.setSpacing(0)

    def shown(self, pairs):
        return [widget for widget, _ in pairs if not widget.isHidden()]

    def wide_width(self):
        widgets = self.shown(self.leading + self.trailing)
        return sum(wanted_width(w) for w in widgets) + self.spacing * max(0, len(widgets) - 1)

    def minimumSizeHint(self):
        def least(widgets):
            return sum(max(w.minimumSizeHint().width(), w.minimumWidth()) for w in widgets) + self.spacing * max(0, len(widgets) - 1)
        return QSize(max(least(self.shown(self.leading)), least(self.shown(self.trailing))), super().minimumSizeHint().height())

    def place(self, two):
        if two == self.two_lines:
            return
        self.two_lines = two
        for index, (widget, stretch) in enumerate(self.trailing):
            (self.top if two else self.bottom).removeWidget(widget)
            if two:
                self.bottom.insertWidget(index, widget, stretch)
            else:
                self.top.addWidget(widget, stretch)
        self.box.setSpacing(self.spacing if two else 0)
        self.updateGeometry()

    def refit(self):
        if self.width() > 0:
            self.place(self.width() < self.wide_width())

    def event(self, event):
        handled = super().event(event)
        if event.type() == QEvent.Type.LayoutRequest:  # new words (language) or new choices: one line or two again
            self.refit()
        return handled

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refit()


def paint_energy(p, rect, zone, theme, radius=13):
    """The Deck Lab banner: a panel with abstract flames and energy arcs in `zone`, its right part.
    Code-drawn and static: no illustration, no character, nothing that moves."""
    c, dark = colors(theme), theme == 'dark'
    shape = QPainterPath()
    shape.addRoundedRect(rect, radius, radius)
    p.save()
    p.setClipPath(shape)
    base = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    base.setColorAt(0, QColor(c['panel_start']))
    base.setColorAt(1, QColor(c['panel_end']))
    p.fillRect(rect, base)
    if zone.width() >= 90:
        tall = zone.height() >= rect.height() - 1  # flames need the whole height to stand on the bottom edge
        hot, clear = QColor(BRAND['rouge_profond']), QColor(BRAND['rouge_profond'])
        hot.setAlphaF(.5 if dark else .14)
        clear.setAlphaF(0)
        wash = QLinearGradient(zone.topLeft(), zone.topRight())
        wash.setColorAt(0, clear)
        wash.setColorAt(1, hot)
        p.fillRect(zone, wash)
        count = max(3, int(zone.width() // 30))
        if not tall:  # a line of heat under the fire, so it does not look cut by the description below
            line = QLinearGradient(zone.bottomLeft(), zone.bottomRight())
            glow = QColor(BRAND['gold'])
            glow.setAlphaF(.8 if dark else .6)
            line.setColorAt(0, clear)
            line.setColorAt(1, glow)
            p.fillRect(QRectF(zone.left(), zone.bottom() - 1, zone.width(), 1.5), line)
        p.setClipRect(zone, Qt.ClipOperation.IntersectClip)
        p.setPen(Qt.PenStyle.NoPen)
        for layer, (color, scale, alpha) in enumerate(((BRAND['rouge_cerveau'], 1.0, .65), (BRAND['gold'], .62, .9))):
            for k in range(count):
                t = (k + .5) / count  # 0 at the left of the zone, 1 at the right: the fire rises to the right
                wobble = .6 + .4 * abs(math.sin(k * 2.1 + layer * 1.3 + .7))
                height = zone.height() * 1.55 * (.18 + .82 * t) * wobble * scale
                width = zone.width() / count * (1.9 if layer == 0 else 1.25)
                x, bottom = zone.left() + t * zone.width(), zone.bottom() + 2
                lean = width * .4 * math.sin(k * 1.3 + layer)
                tongue = QPainterPath(QPointF(x - width / 2, bottom))
                tongue.cubicTo(x - width * .55, bottom - height * .45, x - width * .05 + lean, bottom - height * .6,
                               x + lean, bottom - height)
                tongue.cubicTo(x + width * .12 + lean, bottom - height * .55, x + width * .55, bottom - height * .4,
                               x + width / 2, bottom)
                tongue.closeSubpath()
                fill = QLinearGradient(QPointF(x, bottom), QPointF(x, bottom - height))
                low, high = QColor(color), QColor(color)
                low.setAlphaF(alpha * (1 if dark else .75) * (.3 + .7 * t))
                high.setAlphaF(0)
                fill.setColorAt(0, low)
                fill.setColorAt(1, high)
                p.fillPath(tongue, fill)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for k, (color, alpha) in enumerate(((c['neon_hi'], .75), (BRAND['gold'], .6), (c['neon'], .5))):
            line = QColor(color)
            line.setAlphaF(alpha * (1 if dark else .7))
            p.setPen(QPen(line, 1.7 - k * .3))
            arc = QPainterPath(QPointF(zone.left() + zone.width() * (.02 + .13 * k), zone.bottom() + 4))
            arc.cubicTo(zone.left() + zone.width() * (.3 + .1 * k), zone.top() + zone.height() * (.8 - .2 * k),
                        zone.left() + zone.width() * (.6 + .08 * k), zone.top() + zone.height() * (.12 + .25 * k),
                        zone.right() + 6, zone.top() + zone.height() * (.06 + .22 * k))
            p.drawPath(arc)
        p.setPen(Qt.PenStyle.NoPen)
        for k in range(count * 2):  # embers, placed by a fixed sequence
            t, u = (k * .618034 + .2) % 1, (k * .37 + .15) % 1
            ember = QColor(BRAND['gold'])
            ember.setAlphaF((.35 + .55 * t) * (1 if dark else .8))
            p.setBrush(ember)
            size = 1 + 1.4 * ((k * .29) % 1)
            p.drawEllipse(QPointF(zone.left() + t * zone.width(), zone.top() + u * zone.height() * .85), size, size)
    p.restore()
    p.setPen(QPen(QColor(c['inner_line']), 1))  # a frame inside the lit page panel: the quiet line
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(rect.adjusted(.5, .5, -.5, -.5), radius, radius)


def show_cover(label, picture):
    """A deck's first card in a small fixed frame; a plain sleeve « ◇ » when there is no picture."""
    picture = picture if picture is not None else QPixmap()
    ratio = label.devicePixelRatioF()
    if picture.isNull():
        label.setPixmap(QPixmap())
        label.setText('◇')
    else:
        scaled = picture.scaled(label.size() * ratio, Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation)
        scaled.setDevicePixelRatio(ratio)
        label.setText('')
        label.setPixmap(scaled)
    return picture


class DeckHeading(QWidget):
    """Deck Lab: the deck shown is the title of its strip, its first card beside its name, and what is known
    of it as pills under the name (owner, 2026-11-18). Display only."""
    def __init__(self, pills):
        super().__init__()
        self.setObjectName('deckHeading')
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)
        self.cover = QLabel()
        self.cover.setObjectName('deckCover')
        self.cover.setFixedSize(36, 50)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name = ClampLabel('text', 1, title=(20, 700))  # the title of the strip
        self.name.setObjectName('deckTitle')
        words = QVBoxLayout()
        words.setSpacing(5)
        words.addStretch()
        words.addWidget(self.name)
        words.addLayout(pills)
        words.addStretch()
        row.addWidget(self.cover, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addLayout(words, 1)
        self.picture = show_cover(self.cover, None)
        self.set_deck(None)

    def set_deck(self, name):
        self.name.setText(name if name else T('Aucun deck', en='No deck'))
        self.setAccessibleName(T('Deck affiché : ', en='Deck shown: ') + (name or T('aucun', en='none')))

    def set_cover(self, picture):
        self.picture = show_cover(self.cover, picture)


class CountPill(QLabel):
    """« ×N » on a card in the gallery: a pill with round ends, painted (owner, 2026-11-18); the style sheet
    gives its font and padding."""
    def paintEvent(self, event):
        c = colors(window_theme(self))
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        p.setPen(QPen(QColor(c['neon_hi']), 1))
        p.setBrush(QColor(c['surface']))
        p.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        p.setPen(QColor(c['text']))
        p.setFont(idea_font(self.font()))
        p.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), self.text())
        p.end()


class DeckLabPage(QWidget):
    """The Deck Lab page. It paints the energy banner behind its title and a panel behind the deck controls,
    which stay its own children (their layout is the page's)."""
    EDGE = 14  # just inside the lit frame of the page area

    def __init__(self):
        super().__init__()
        self.setObjectName('deckLabPage')
        self.heading, self.strip = None, None  # (title label, description label) and the layout of the strip

    def paintEvent(self, event):
        theme = window_theme(self)
        c = colors(theme)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.heading:
            title, sub = self.heading
            rect = QRectF(self.EDGE, self.EDGE, self.width() - 2 * self.EDGE, sub.geometry().bottom() + 9 - self.EDGE)
            written = QFontMetrics(title.font()).horizontalAdvance(title.text())
            one_line = QFontMetrics(sub.font()).horizontalAdvance(sub.text())
            left = title.x() + max(written, one_line) + 34
            zone = QRectF(left, rect.top(), rect.right() - left, rect.height())
            if zone.width() < 170:  # no room beside the description: the fire keeps to the title row, above it
                left = title.x() + written + 34
                zone = QRectF(left, rect.top(), rect.right() - left, title.geometry().bottom() + 2 - rect.top())
            paint_energy(p, rect, zone, theme)
        if self.strip is not None:
            rect = QRectF(self.strip.geometry()).adjusted(.5, .5, -.5, -.5)
            p.setPen(QPen(QColor(c['inner_line']), 1))  # inside the lit page panel: surface and the quiet line
            p.setBrush(QColor(c['surface']))
            p.drawRoundedRect(rect, 14, 14)
        p.end()


class GalleryBody(QWidget):
    """The scrolled page of the gallery. A tile cannot paint outside itself, so the gold light around the
    selected card is painted here, under the tiles, in the gaps of the grid."""
    def __init__(self, gallery):
        super().__init__()
        self.gallery = gallery

    def paintEvent(self, event):
        tile = self.gallery.selected_tile
        if tile is None or tile.parentWidget() is not self:
            return
        theme = window_theme(self)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        paint_glow(p, QRectF(tile.geometry()).adjusted(1, 1, -1, -1), 12, BRAND['gold'], 12,
                   1.7 if theme == 'dark' else 3.6)
        p.end()


class CardTile(QFrame):
    activated = Signal(object)
    selected = Signal(object)
    pictured = Signal(object)  # its picture arrived or was withdrawn

    def __init__(self, card, *, gallery=False):
        super().__init__()
        self.card, self.picture, self.provenance = card, QPixmap(), ''
        self.gallery = gallery
        self.setObjectName('card')
        self.setProperty('galleryTile', gallery)
        self.setProperty('selected', False)
        self.setMinimumWidth(0 if gallery else 160)
        self.setMaximumWidth(DeckGallery.TILE_MAX if gallery else 220)
        layout = QVBoxLayout(self)
        if gallery:  # compact: four or five cards a row; the section heading already says the category
            layout.setContentsMargins(7, 7, 7, 8)
            layout.setSpacing(4)
        else:
            category = {'pokemon': 'Pokémon', 'trainer': T('Dresseur', en='Trainer'),
                        'energy': T('Énergie', en='Energy')}.get(card['category'], '')
            label = QLabel(str(card['quantity']) + ' ×  ' + category)
            label.setProperty('cardType', card['category'])
            layout.addWidget(label)
        self.badge = None
        self.art = CardArt('◇\n' + card['name'] + T('\nImage indisponible'))
        self.art.setProperty('galleryArt', gallery)
        self.art.setProperty('pictured', False)  # a frame only while the picture is missing
        if gallery:
            self.art.animation.setDuration(220)
            self.art.animation.valueChanged.connect(lambda _: self.update())
            self.art.installEventFilter(self)
        self.art.setMinimumHeight(230)
        self.art.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.art.setAccessibleName(T('Agrandir ') + card['name'])
        self.art.clicked.connect(lambda: self.activated.emit(self))
        layout.addWidget(self.art)
        self.name_label = QLabel(card['name'])
        self.name_label.setWordWrap(True)
        if gallery:
            self.name_label.setObjectName('galleryCardName')
        layout.addWidget(self.name_label)
        self.stamp_label = QLabel(card.get('printing', T('Impression inconnue')))
        self.stamp_label.setObjectName('galleryStamp' if gallery else 'muted')
        self.stamp_label.setWordWrap(gallery)
        layout.addWidget(self.stamp_label)
        if gallery:  # the column sets the width, as for the picture: a long word must not have the layout measure
            for label in (self.name_label, self.stamp_label):  # the height at a width the label does not get
                label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        if gallery:  # « ×N » on the bottom of the picture, outside the layout
            self.badge = CountPill(self)
            self.badge.setObjectName('countBadge')
            self.badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self.show_count()

    def show_count(self):
        if self.badge is not None:
            count = str(self.card['quantity'])
            self.badge.setText('×' + count)
            self.badge.setAccessibleName(count + T(' exemplaires', en=' copies'))
            self.place_badge()

    def place_badge(self):
        if self.badge is not None:
            self.badge.ensurePolished()  # its size depends on the style sheet, known once the tile is in a window
            self.badge.adjustSize()
            art = self.art.geometry()
            self.badge.move(art.center().x() - self.badge.width() // 2, art.bottom() - self.badge.height() - 7)
            self.badge.raise_()

    def show_picture_frame(self, pictured):
        """A bare card when its picture is here; the plain frame of « Image indisponible » otherwise."""
        if self.art.property('pictured') != pictured:
            self.art.setProperty('pictured', pictured)
            self.art.style().unpolish(self.art)
            self.art.style().polish(self.art)
            self.art.update()

    def set_selected(self, selected):
        self.setProperty('selected', selected)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def eventFilter(self, watched, event):
        if watched is self.art and event.type() == QEvent.Type.FocusIn:
            self.selected.emit(self)
        if watched is self.art and event.type() in (QEvent.Type.Resize, QEvent.Type.Move):
            self.place_badge()
        return super().eventFilter(watched, event)

    def fit_height(self):
        if self.gallery:
            margins = self.layout().contentsMargins()
            width = self.contentsRect().width() - margins.left() - margins.right() - 14
            # Reserve a normal card's aspect ratio, including CardArt's safe inset.
            # The painter still fits each actual image with KeepAspectRatio.
            height = round(max(1, width) * 1.4) + 16
            if self.art.height() != height:
                self.art.setFixedHeight(height)
                self.layout().activate()  # name and set code under the new picture now, not one event loop later
            # Nested grid layouts can compress a word-wrapped label against the
            # fixed-height artwork. Reserve its actual height at this width/font.
            height = max(0, self.layout().totalHeightForWidth(self.width()))
            if self.minimumHeight() != height:
                self.setMinimumHeight(height)
            self.place_badge()

    def event(self, event):
        if event.type() == QEvent.Type.LayoutRequest:
            self.fit_height()
        return super().event(event)

    def resizeEvent(self, event):
        self.fit_height()
        super().resizeEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        # The existing artwork animation drives the tile's outline too: no second
        # animation, graphics effect, snapshot or geometry change per card.
        if self.gallery and self.art.hover and not self.property('selected'):
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            tint = QColor(colors(theme_of(self.palette()))['blue'])
            tint.setAlpha(round(210 * self.art.hover))
            p.setPen(QPen(tint, 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 12, 12)
            p.end()

    def reset(self, card):
        self.card, self.picture, self.provenance = card, QPixmap(), ''
        self.name_label.setText(card['name'])
        self.stamp_label.setText(card.get('printing', T('Impression inconnue')))
        self.art.setIcon(QIcon())
        self.art.setText('◇\n' + card['name'] + T('\nImage indisponible'))
        self.art.set_pending(False)
        self.show_picture_frame(False)
        self.show_count()
        self.pictured.emit(self)

    def set_pending(self, pending=True):
        """Its picture is on its way: a dark card silhouette instead of the « Image indisponible » frame."""
        if self.picture.isNull():
            self.art.set_pending(pending)
            self.show_picture_frame(pending)

    def set_image(self, result, fade=False):
        """`result` holds a decoded `picture` (QPixmap, from the memory cache) or raw PNG `data`. No picture:
        the « Image indisponible » frame. `fade` fades it in (150 ms) unless motion is reduced."""
        picture = result.get('picture') if isinstance(result.get('picture'), QPixmap) else QPixmap()
        if picture.isNull() and result.get('data'):
            picture.loadFromData(result['data'])
        if picture.isNull():
            self.set_pending(False)
            return
        self.picture = picture
        self.provenance = result.get('source_url', '')
        self.art.setText('')
        self.art.setIcon(QIcon(picture))
        self.art.setIconSize(QSize(150, 210))
        self.art.set_pending(False)
        self.show_picture_frame(True)
        self.art.setToolTip(T('TCGdex · illustration Pokémon · cache local\n') + self.provenance)
        if fade:
            self.art.fade.start(self.art.motion_enabled)
        self.pictured.emit(self)

    def enlarge(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(self.card['name'])
        layout = QVBoxLayout(dialog)
        if not self.picture.isNull():
            art = ZoomImage(self.picture, motion=self.art.motion_enabled)
        else:
            art = QLabel(self.card['name'] + T('\nImage absente ou non autorisée; texte local conservé.'))
            art.setAlignment(Qt.AlignmentFlag.AlignCenter)
            art.setMinimumSize(300, 200)
        layout.addWidget(art, 1)
        source = QLabel(T('Source : ') + (self.provenance or T('aucune image')) + T('\nIllustrations © Pokémon / Nintendo / Creatures / GAME FREAK. Usage personnel local, aucune redistribution.'))
        source.setWordWrap(True)
        source.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(source)
        close = QPushButton(T('Fermer'))
        close.clicked.connect(dialog.accept)
        layout.addWidget(close)
        dialog.resize(520, min(740, dialog.screen().availableGeometry().height()-70) if not self.picture.isNull() else 340)
        dialog.exec()


class DeckGallery(QScrollArea):
    cover_changed = Signal(object)  # first loaded picture of the deck shown, or an empty pixmap
    # Four or five cards a row at 1500 px beside the Coach, and two rows in sight (owner, 2026-11-16).
    TILE_MIN, TILE_MAX, GAP, SIDE, COLUMNS = 140, 220, 12, 12, 5

    def __init__(self):
        super().__init__()
        self.setObjectName('deckGallery')
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setWidgetResizable(True)
        self.tiles, self.grids, self.generation = [], [], 0
        self.motion_enabled = True
        self._columns, self.selected_tile = 0, None
        self._tile_width = 0
        self._cover = None

    def refresh_cover(self, tile=None):
        """Tell the sidebar which picture stands for this deck: its first card that has one (Pokémon come first)."""
        picture = next((t.picture for t in self.tiles if not t.picture.isNull()), QPixmap())
        key = None if picture.isNull() else picture.cacheKey()
        if key != self._cover or tile is None:
            self._cover = key
            self.cover_changed.emit(picture)

    def set_motion_enabled(self, enabled):
        self.motion_enabled = enabled
        for tile in self.tiles:
            tile.art.set_motion_enabled(enabled)

    def populate(self, cards):
        self.generation += 1
        self.selected_tile, self._columns = None, 0
        self.tiles, self.grids = [], []
        body = GalleryBody(self)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(self.SIDE, 6, self.SIDE, 14)
        layout.setSpacing(8)
        for category, title in (('pokemon','Pokémon'), ('trainer',T('Dresseurs')), ('energy',T('Énergies'))):
            group = [c for c in cards if c['category'] == category]
            heading = QLabel(title + ' · ' + str(sum(c['quantity'] for c in group)) + T(' cartes'))
            heading.setObjectName('gallerySection')
            heading.setWordWrap(True)
            heading.setMinimumWidth(1)  # a narrow gallery wraps the heading instead of scrolling sideways
            layout.addWidget(heading)
            grid = QGridLayout()
            grid.setSpacing(self.GAP)
            grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            tiles = [CardTile(c, gallery=True) for c in group]
            for tile in tiles:
                tile.art.set_motion_enabled(self.motion_enabled)
                tile.selected.connect(self.select_tile)
                tile.activated.connect(self.select_tile)
                tile.activated.connect(lambda value: value.enlarge())
                tile.pictured.connect(self.refresh_cover)
            self.grids.append((grid, tiles))
            self.tiles.extend(tiles)
            layout.addLayout(grid)
        layout.addStretch()
        self.setWidget(body)
        self.reflow()
        self.refresh_cover()

    def select_tile(self, tile):
        if self.selected_tile is tile:
            return
        if self.selected_tile is not None:
            self.selected_tile.set_selected(False)
        self.selected_tile = tile
        tile.set_selected(True)
        self.widget().update()  # the gold light follows the selection

    def reflow(self):
        available = max(1, self.viewport().width() - 2 * self.SIDE)
        # As many sleeves of at least TILE_MIN as the room allows, five at most; they then share the row.
        columns = max(1, min(self.COLUMNS, (available + self.GAP) // (self.TILE_MIN + self.GAP)))
        tile_width = min(self.TILE_MAX, max(1, (available - (columns - 1) * self.GAP) // columns))
        if (columns, tile_width) == (self._columns, self._tile_width):
            return
        for grid, tiles in self.grids:
            while grid.count():
                grid.takeAt(0)
            # Clear obsolete columns when narrowing, so a short group starts at
            # the same left edge as a full row rather than floating in its centre.
            for column in range(max(self._columns, columns)):
                grid.setColumnStretch(column, 0)
                grid.setColumnMinimumWidth(column, tile_width if column < columns else 0)
            for index, tile in enumerate(tiles):
                tile.setFixedWidth(tile_width)
                grid.addWidget(tile, index//columns, index%columns)
        self._columns, self._tile_width = columns, tile_width
        if self.widget() is not None:
            self.widget().update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reflow()
