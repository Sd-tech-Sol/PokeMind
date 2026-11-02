"""A card binder drawn in code: a cover that opens onto sleeved pages, one or two at a time."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QRect, QRectF, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QSizePolicy, QVBoxLayout

from pokemind.desktop.i18n import QFrame, QLabel, QPushButton, QWidget, T
from pokemind.desktop.theme import logo_pixmap

CATEGORY_COLORS = {'pokemon': ('#e3364b', '#7a1f2c'), 'trainer': ('#4f7fe0', '#253f7a'),
                   'energy': ('#e9bd4a', '#7a5f1c')}
SLOTS_PER_PAGE = 9


class BinderSlot(QWidget):
    """One plastic sleeve: the card art when cached, else a coloured card with its name."""
    activated = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.card, self.picture, self.hover = None, None, False
        self.setMinimumSize(QSize(70, 98))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

    def set_card(self, card):
        self.card, self.picture = card, None
        self.setToolTip(str(card.get('name') or '') + ' · ' + str(card.get('tcgdex_id') or '') if card else '')
        self.setAccessibleName(str(card.get('name') or '') if card else T('Pochette vide'))
        self.update()

    def set_image(self, result, identity):
        picture = QPixmap()
        if self.card and self.card.get('tcgdex_id') == identity and result.get('data') and picture.loadFromData(result['data']):
            self.picture = picture
            self.update()

    def card_rect(self):
        area = QRectF(self.rect()).adjusted(4, 4, -4, -4)
        width = min(area.width(), area.height() * 0.716)  # a TCG card is 63 x 88 mm
        height = width / 0.716
        return QRectF(area.center().x() - width / 2, area.center().y() - height / 2, width, height)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        sleeve = self.card_rect().adjusted(-3, -3, 3, 3)
        p.setPen(QPen(QColor(255, 255, 255, 34), 1))
        p.setBrush(QColor(255, 255, 255, 10))
        p.drawRoundedRect(sleeve, 7, 7)
        card = self.card_rect()
        if self.card and self.picture is not None:
            p.save()
            p.setClipRect(card)
            p.drawPixmap(card.toRect(), self.picture)
            p.restore()
        elif self.card:
            top, bottom = CATEGORY_COLORS.get(self.card.get('category'), CATEGORY_COLORS['pokemon'])
            fill = QLinearGradient(card.topLeft(), card.bottomRight())
            fill.setColorAt(0, QColor(top))
            fill.setColorAt(1, QColor(bottom))
            p.setPen(QPen(QColor('#f2d36b'), 2))
            p.setBrush(fill)
            p.drawRoundedRect(card, 6, 6)
            p.setPen(QColor('white'))
            font = p.font()
            font.setPointSizeF(max(7.0, card.width() / 12))
            font.setBold(True)
            p.setFont(font)
            p.drawText(card.adjusted(6, 6, -6, -6).toRect(), int(Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter),
                       str(self.card.get('name') or ''))
            font.setBold(False)
            font.setPointSizeF(max(6.0, card.width() / 16))
            p.setFont(font)
            p.drawText(card.adjusted(4, 4, -4, -4).toRect(), int(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter),
                       str(self.card.get('tcgdex_id') or ''))
        else:
            p.setPen(QPen(QColor(255, 255, 255, 22), 1, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(card, 6, 6)
        if self.hover and self.card:
            p.setPen(QPen(QColor('#ffda62'), 2.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(card.adjusted(-1, -1, 1, 1), 7, 7)
        p.end()

    def enterEvent(self, event):
        self.hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hover = False
        self.update()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.card:
            self.activated.emit(self.card)
        super().mouseReleaseEvent(event)


class BinderCover(QWidget):
    """The closed binder: red cover, gold border and the logo; it slides open once."""
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        fill = QLinearGradient(bounds.topLeft(), bounds.bottomRight())
        fill.setColorAt(0, QColor('#c4283f'))
        fill.setColorAt(1, QColor('#6d1424'))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(fill)
        p.drawRoundedRect(bounds, 14, 14)
        p.setPen(QPen(QColor('#f2d36b'), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(bounds.adjusted(10, 10, -10, -10), 10, 10)
        side = int(min(bounds.width(), bounds.height()) * 0.32)
        if side > 24:
            p.drawPixmap(int(bounds.center().x() - side / 2), int(bounds.center().y() - side * 0.75), logo_pixmap(side))
        p.setPen(QColor('#ffe9a8'))
        font = p.font()
        font.setPointSize(16)
        font.setBold(True)
        p.setFont(font)
        p.drawText(QRect(0, int(bounds.center().y() + side * 0.35), self.width(), 40),
                   int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop), 'PokeMind')
        p.end()


class CardBinder(QWidget):
    """Shows `per_spread()` cards at a time; asks the window for another offset."""
    page_requested = Signal(int)
    card_activated = Signal(object)
    download_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.offset, self.total, self.motion_enabled, self.opened = 0, 0, True, False
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        self.title = QLabel(T('Classeur'))
        self.title.setObjectName('sectionTitle')
        bar.addWidget(self.title)
        bar.addStretch()
        self.previous = QPushButton('‹')
        self.previous.setObjectName('binderTurn')
        self.previous.setToolTip(T('Page précédente'))
        self.previous.clicked.connect(lambda: self.turn(-1))
        self.page_label = QLabel('—')
        self.page_label.setObjectName('smallCaption')
        self.next = QPushButton('›')
        self.next.setObjectName('binderTurn')
        self.next.setToolTip(T('Page suivante'))
        self.next.clicked.connect(lambda: self.turn(1))
        for widget in (self.previous, self.page_label, self.next):
            bar.addWidget(widget)
        outer.addLayout(bar)
        self.book = QFrame()
        self.book.setObjectName('binderBook')
        spread = QHBoxLayout(self.book)
        spread.setContentsMargins(12, 12, 12, 12)
        spread.setSpacing(0)
        self.pages, self.slots = [], []
        for side in range(2):
            page = QFrame()
            page.setObjectName('binderPage')
            grid = QGridLayout(page)
            grid.setContentsMargins(10, 10, 10, 10)
            grid.setSpacing(6)
            for index in range(SLOTS_PER_PAGE):
                slot = BinderSlot()
                slot.activated.connect(self.card_activated)
                grid.addWidget(slot, index // 3, index % 3)
                self.slots.append(slot)
            self.pages.append(page)
            spread.addWidget(page, 1)
            if side == 0:
                self.spine = QFrame()
                self.spine.setObjectName('binderSpine')
                self.spine.setFixedWidth(16)
                spread.addWidget(self.spine)
        outer.addWidget(self.book, 1)
        self.cover = BinderCover(self.book)
        self.cover.setAccessibleName(T('Couverture du classeur'))
        self.animation = QPropertyAnimation(self.cover, b'geometry', self)
        self.animation.setDuration(650)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.finished.connect(self.cover.hide)
        self.empty = QFrame(self.book)
        self.empty.setObjectName('binderEmpty')
        centre = QVBoxLayout(self.empty)
        centre.addStretch()
        notice = QFrame()
        notice.setObjectName('binderNotice')
        notice.setFixedWidth(440)  # a fixed width lets the wrapped text compute its real height
        centre.addWidget(notice, 0, Qt.AlignmentFlag.AlignCenter)
        centre.addStretch()
        message = QVBoxLayout(notice)
        message.setContentsMargins(22, 18, 22, 18)
        message.setSpacing(12)
        self.empty_text = QLabel(T('Catalogue local absent : synchronise d’abord le catalogue public.'))
        self.empty_text.setObjectName('smallCaption')
        self.empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_text.setWordWrap(True)
        self.empty_text.setMinimumHeight(60)  # three wrapped lines: a centred frame does not ask the label
        message.addWidget(self.empty_text)
        self.download = QPushButton(T('Télécharger le catalogue (environ 25 Mo)'))
        self.download.setObjectName('primary')
        self.download.clicked.connect(self.download_requested)
        self.download.hide()
        message.addWidget(self.download, 0, Qt.AlignmentFlag.AlignCenter)
        self.empty.hide()
        self.apply_spread()

    def set_motion_enabled(self, enabled):
        self.motion_enabled = enabled

    def two_pages(self):
        return self.width() >= 760

    def per_spread(self):
        return SLOTS_PER_PAGE * (2 if self.two_pages() else 1)

    def apply_spread(self):
        two = self.two_pages()
        self.pages[1].setVisible(two)
        self.spine.setVisible(two)

    def set_cards(self, cards, offset, total):
        self.offset, self.total = offset, total
        visible = self.per_spread()
        for index, slot in enumerate(self.slots):
            slot.set_card(cards[index] if index < len(cards) and index < visible else None)
        pages = max(1, -(-total // visible))
        self.page_label.setText(T('Page ') + str(offset // visible + 1) + ' / ' + str(pages) + ' · ' + str(total)
                                + T(' cartes'))
        self.previous.setEnabled(offset > 0)
        self.next.setEnabled(offset + visible < total)
        self.empty.setVisible(not total)
        self.empty.setGeometry(self.book.rect())

    def show_unavailable(self, message, offer=False):
        self.set_cards([], 0, 0)
        self.empty_text.setText(message)
        self.download.setVisible(offer)

    def turn(self, step):
        target = max(0, self.offset + step * self.per_spread())
        if target != self.offset and target < max(1, self.total):
            self.page_requested.emit(target)

    def open_cover(self):
        """Slide the cover off to the left the first time the binder appears."""
        if self.opened:
            return
        self.opened = True
        start = self.book.rect()
        self.cover.setGeometry(start)
        self.cover.show()
        self.cover.raise_()
        if not self.motion_enabled:
            self.cover.hide()
            return
        self.animation.setStartValue(start)
        self.animation.setEndValue(QRect(start.left(), start.top(), 0, start.height()))
        self.animation.start()

    def showEvent(self, event):
        super().showEvent(event)
        if not self.opened:
            self.cover.setGeometry(self.book.rect())
            self.cover.raise_()

    def resizeEvent(self, event):
        before = SLOTS_PER_PAGE * (2 if event.oldSize().width() >= 760 else 1)
        super().resizeEvent(event)
        self.apply_spread()
        if self.cover.isVisible() and self.animation.state() != QPropertyAnimation.State.Running:
            self.cover.setGeometry(self.book.rect())
        self.empty.setGeometry(self.book.rect())
        if self.per_spread() != before and self.total:
            self.page_requested.emit(self.offset - self.offset % self.per_spread())
