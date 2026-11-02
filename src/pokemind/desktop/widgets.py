"""Native visual controls; data and decisions remain in the existing services."""
from __future__ import annotations
from pokemind.desktop.i18n import T, J, display

from PySide6.QtCore import (Qt, Signal, QTimer, QElapsedTimer, QSize, QRectF, QRect,
                           Property, QPropertyAnimation, QEasingCurve)
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QIcon, QPalette
from PySide6.QtWidgets import (QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QFrame, QPushButton, QScrollArea, QGridLayout, QDialog, QSizePolicy,
    QCheckBox, QStyle, QStyleOptionButton, QStylePainter, QStyledItemDelegate, QStyleOptionViewItem,
    QApplication)
from pokemind.desktop.theme import colors
from pokemind.desktop.card_art import CardArt, ZoomImage
from pokemind.desktop.i18n import QWidget, QTextEdit, QLabel, QFrame, QPushButton, QDialog, QCheckBox, Painter as QPainter


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
        for offset, color in ((0, '#e3364b'), (180, '#ffcb05')):
            p.setPen(QPen(QColor(color), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawArc(bounds, int((offset - self.angle) * 16), 110 * 16)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor('#f4f6fa'))
        p.drawEllipse(QRectF(9.5, 9.5, 5, 5))
        p.end()


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


class RecordBarDelegate(QStyledItemDelegate):
    """Wins, losses and unknown results of a row as one coloured bar, with n beside it."""
    COLORS = ('#628be0', '#e3364b', '#e9bd4a')

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
        bar.setHeight(10)
        bar.moveLeft(item.rect.left() + 8)
        bar.moveTop(item.rect.center().y() - 5)
        track = QColor(item.palette.color(QPalette.ColorRole.Mid))
        track.setAlpha(90)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track)
        painter.drawRoundedRect(bar, 5, 5)
        if total and bar.width() > 4:
            left = bar.left()
            painter.setClipRect(bar)
            for value, color in zip(values, self.COLORS):
                share = bar.width() * value / total
                if share:
                    painter.setBrush(QColor(color))
                    painter.drawRoundedRect(QRectF(left, bar.top(), share, bar.height()), 5, 5)
                    left += share
            painter.setClipping(False)
        painter.setPen(item.palette.color(QPalette.ColorRole.Text))
        painter.drawText(QRectF(item.rect).adjusted(0, 0, -6, 0),
                         int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter), text)
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(160, 34)


def wrap_popup(combo, width=440):
    """The closed box stays narrow; its open list shows every entry in full."""
    combo.setItemDelegate(WrapItemDelegate(width, combo))
    view = combo.view()
    view.setMinimumWidth(width)
    view.setTextElideMode(Qt.TextElideMode.ElideNone)
    view.setWordWrap(True)


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
        self.setAccessibleName(T('Répartition du corpus enregistré et priorités par défaites; taux global inconnu'))

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
        series_colors = [theme['blue'], theme['red'], theme['yellow']]
        o = (self.report or {}).get('outcomes', {})
        values = [o.get(k, 0) for k in ('wins', 'losses', 'unknown')]
        total = sum(values)
        rect = QRectF(20, 27, 110, 110)
        p.setPen(QPen(QColor(theme['border']), 18))
        p.drawEllipse(rect)
        angle = 90 * 16
        if total:
            for value, color in zip(values, series_colors):
                span = -round(value / total * 360 * 16 * self._reveal)
                p.setPen(QPen(QColor(color), 18))
                p.drawArc(rect, angle, span)
                angle += span
        p.setPen(QColor(theme['text']))
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(total) + T('\nparties'))
        for i, (label, value, color) in enumerate(zip((T('Victoires'), T('Défaites'), T('Inconnues')), values, series_colors)):
            p.setPen(QColor(color))
            p.drawText(155, 42 + 28*i, label + ' : ' + str(value))
        p.setPen(QColor(theme['muted']))
        p.drawText(15, 172, T('Corpus enregistré · taux global inconnu'))
        groups = (self.report or {}).get('groups', [])[:4]
        if self.width() > 560:
            x, width = 330, max(40, self.width() - 350)
            p.drawText(x, 13, T('Défaites par famille'))
            maximum = max([g['losses'] for g in groups] or [1]) or 1
            for i, g in enumerate(groups):
                y = 27 + i * 36
                p.setPen(QColor(theme['text']))
                label = p.fontMetrics().elidedText(g['archetype'], Qt.TextElideMode.ElideRight, max(25, width - 110))
                p.drawText(x, y+12, label + T(' · D=') + str(g['losses']) + ' · n=' + str(g['n']))
                p.fillRect(x, y+19, width, 6, QColor(theme['border']))
                p.fillRect(x, y+19, round(width*g['losses']/maximum*self._reveal), 6, QColor(theme['red']))
        p.end()


class CardTile(QFrame):
    activated = Signal(object)

    def __init__(self, card):
        super().__init__()
        self.card, self.picture, self.provenance = card, QPixmap(), ''
        self.setObjectName('card')
        self.setMinimumWidth(160)
        self.setMaximumWidth(220)
        layout = QVBoxLayout(self)
        category = {'pokemon': 'POKÉMON', 'trainer': T('DRESSEUR'), 'energy': T('ÉNERGIE')}.get(card['category'], '')
        label = QLabel(str(card['quantity']) + ' ×  ' + category)
        label.setProperty('cardType', card['category'])
        layout.addWidget(label)
        self.art = CardArt('◇\n' + card['name'] + T('\nImage indisponible'))
        self.art.setMinimumHeight(230)
        self.art.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.art.setAccessibleName(T('Agrandir ') + card['name'])
        self.art.clicked.connect(lambda: self.activated.emit(self))
        layout.addWidget(self.art)
        self.name_label = QLabel(card['name'])
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)
        self.stamp_label = QLabel(card.get('printing', T('Impression inconnue')))
        self.stamp_label.setObjectName('muted')
        layout.addWidget(self.stamp_label)

    def reset(self, card):
        self.card, self.picture, self.provenance = card, QPixmap(), ''
        self.name_label.setText(card['name'])
        self.stamp_label.setText(card.get('printing', T('Impression inconnue')))
        self.art.setIcon(QIcon())
        self.art.setText('◇\n' + card['name'] + T('\nImage indisponible'))

    def set_image(self, result):
        picture = QPixmap()
        if result.get('data') and picture.loadFromData(result['data']):
            self.picture = picture
            self.provenance = result.get('source_url', '')
            self.art.setText('')
            self.art.setIcon(QIcon(picture))
            self.art.setIconSize(QSize(150, 210))
            self.art.setToolTip(T('TCGdex · illustration Pokémon · cache local\n') + self.provenance)

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
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.tiles, self.grids, self.generation = [], [], 0
        self.motion_enabled = True

    def set_motion_enabled(self, enabled):
        self.motion_enabled = enabled
        for tile in self.tiles:
            tile.art.set_motion_enabled(enabled)

    def populate(self, cards):
        self.generation += 1
        self.tiles, self.grids = [], []
        body = QWidget()
        layout = QVBoxLayout(body)
        for category, title in (('pokemon','Pokémon'), ('trainer',T('Dresseurs')), ('energy',T('Énergies'))):
            group = [c for c in cards if c['category'] == category]
            layout.addWidget(QLabel(title + ' · ' + str(sum(c['quantity'] for c in group)) + T(' cartes')))
            grid = QGridLayout()
            tiles = [CardTile(c) for c in group]
            for tile in tiles:
                tile.art.set_motion_enabled(self.motion_enabled)
                tile.activated.connect(lambda value: value.enlarge())
            self.grids.append((grid, tiles))
            self.tiles.extend(tiles)
            layout.addLayout(grid)
        layout.addStretch()
        self.setWidget(body)
        self.reflow()

    def reflow(self):
        columns = max(1, self.viewport().width() // 210)
        for grid, tiles in self.grids:
            while grid.count():
                grid.takeAt(0)
            for index, tile in enumerate(tiles):
                grid.addWidget(tile, index//columns, index%columns)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reflow()
