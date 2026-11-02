"""Native count charts over existing report aggregates and observed traces."""
from pokemind.desktop.i18n import T, J, display
from PySide6.QtCore import Qt, Signal, QRectF, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import (QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout,
                              QComboBox, QTabWidget, QSizePolicy)
from pokemind.desktop.theme import colors
from pokemind.desktop.insights import project_statistics
from pokemind.desktop.i18n import QWidget, QFrame, QLabel, QComboBox, QTabWidget, Painter as QPainter


class CountChart(QWidget):
    selected = Signal(str)

    def __init__(self, *, grouped=False):
        super().__init__()
        self.rows, self.regions = [], []
        self.grouped, self.hovered, self.theme = grouped, -1, 'dark'
        self.motion_enabled, self._reveal = True, 1.0
        self.setMinimumHeight(245)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(T('Effectifs observés par famille') if grouped else T('Effectifs des traces disponibles'))
        self.animation = QPropertyAnimation(self, b'reveal', self)
        self.animation.setDuration(500)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def set_reveal(self, value):
        self._reveal = value
        self.update()

    reveal = Property(float, lambda self: self._reveal, set_reveal)

    def animate(self):
        self.animation.stop()
        if self.motion_enabled and self.isVisible() and self.rows:
            self.animation.setStartValue(0.0)
            self.animation.setEndValue(1.0)
            self.animation.start()
        else:
            self.set_reveal(1.0)

    def set_rows(self, rows):
        self.rows, self.hovered = rows[:8], -1
        self.setToolTip('')
        self.setAccessibleDescription(J('; ',(self.description(r) for r in self.rows)) or T('Aucune donnée disponible'))
        self.animate()

    def description(self, row):
        values = row['values']
        if self.grouped:
            return row['label'] + ' : ' + J(', ',(str(v) + ' ' + label for v, label in zip(values, (T('victoires'), T('défaites'), T('issues inconnues'))))) + '; n=' + str(sum(values))
        return row['label'] + ' : ' + str(sum(values))

    def set_theme(self, theme):
        self.theme = theme
        self.update()

    def set_motion_enabled(self, enabled):
        self.motion_enabled = enabled
        if not enabled:
            self.animation.stop()
            self.set_reveal(1.0)

    def showEvent(self, event):
        super().showEvent(event)
        self.animate()

    def hideEvent(self, event):
        self.animation.stop()
        self.set_reveal(1.0)
        super().hideEvent(event)

    def paintEvent(self, event):
        c = colors(self.theme)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(c['surface']))
        self.regions = []
        if not self.rows:
            p.setPen(QColor(c['muted']))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, T('Aucune trace disponible pour cette vue.'))
            p.end()
            return
        left, right, top, bottom = (174 if self.width() >= 600 else 135), 44, 12, self.height() - 26
        width = max(30, self.width() - left - right)
        maximum = max(sum(r['values']) for r in self.rows) or 1
        height = (bottom - top) / len(self.rows)
        for tick in sorted({round(maximum * i / 4) for i in range(5)}):
            x = left + width * tick / maximum
            p.setPen(QPen(QColor(c['border']), 1))
            p.drawLine(round(x), top, round(x), bottom)
            p.setPen(QColor(c['muted']))
            p.drawText(QRectF(x - 16, bottom + 5, 32, 19), Qt.AlignmentFlag.AlignCenter, str(tick))
        series = [c['blue'], c['red'], c['yellow']] if self.grouped else [c['blue']]
        for index, row in enumerate(self.rows):
            y = top + index * height
            hit = QRectF(0, y, self.width(), height)
            self.regions.append(hit)
            if index == self.hovered:
                p.fillRect(hit, QColor(c['alternate']))
            p.setPen(QColor(c['text']))
            label = display(T('Famille inconnue') if row['label'] == 'unknown' else row['label'])
            label = p.fontMetrics().elidedText(label, Qt.TextElideMode.ElideRight, left - 17)
            p.drawText(QRectF(8, y, left - 14, height), Qt.AlignmentFlag.AlignVCenter, label)
            x = float(left)
            for value, color in zip(row['values'], series):
                length = width * value / maximum * self._reveal
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(color))
                p.drawRoundedRect(QRectF(x, y + height * .26, length, height * .48), 3, 3)
                x += length
            p.setPen(QColor(c['text']))
            p.drawText(QRectF(left + width + 7, y, right - 7, height), Qt.AlignmentFlag.AlignVCenter, str(sum(row['values'])))
        if self.hasFocus():
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(c['accent']), 1))
            p.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 5, 5)
        p.end()

    def mouseMoveEvent(self, event):
        self.hovered = next((i for i, rect in enumerate(self.regions) if rect.contains(event.position())), -1)
        self.setToolTip(self.description(self.rows[self.hovered]) if self.hovered >= 0 else '')
        self.setCursor(Qt.CursorShape.PointingHandCursor if self.grouped and self.hovered >= 0 else Qt.CursorShape.ArrowCursor)
        self.update()

    def leaveEvent(self, event):
        self.hovered = -1
        self.update()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.grouped:
            index = next((i for i, rect in enumerate(self.regions) if rect.contains(event.position())), -1)
            if index >= 0:
                self.selected.emit(self.rows[index]['label'])
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if self.rows and event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            self.hovered = (self.hovered + (1 if event.key() == Qt.Key.Key_Down else -1)) % len(self.rows)
            self.setToolTip(self.description(self.rows[self.hovered]))
            self.update()
        elif self.grouped and self.hovered >= 0 and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.selected.emit(self.rows[self.hovered]['label'])
        else:
            super().keyPressEvent(event)


class StatisticsPanel(QFrame):
    group_selected = Signal(str)

    def __init__(self, bilan):
        super().__init__()
        self.setObjectName('card')
        self.report, self.theme = None, 'dark'
        self.bilan = bilan
        layout = QVBoxLayout(self)
        heading = QLabel(T('Tes statistiques, en images'))
        heading.setObjectName('sectionTitle')
        layout.addWidget(heading)
        controls = QHBoxLayout()
        controls.addWidget(QLabel(T('Vues détaillées')))
        self.scope_filter = QComboBox()
        for label, key in ((T('Tous les résultats'),'all'), (T('Victoires'),'wins'), (T('Défaites'),'losses'), (T('Issues inconnues'),'unknown')):
            self.scope_filter.addItem(label, key)
        self.scope_filter.currentIndexChanged.connect(self.refresh)
        controls.addWidget(self.scope_filter, 1)
        layout.addLayout(controls)
        self.summary = QLabel()
        self.summary.setObjectName('muted')
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.tabs = QTabWidget()
        self.tabs.addTab(bilan, T('Bilan'))
        self.matchups = CountChart(grouped=True)
        self.turns, self.events = CountChart(), CountChart()
        self.matchups.selected.connect(self.group_selected)
        for chart, label in ((self.matchups, T('Adversaires')), (self.turns, T('Tours')), (self.events, 'Actions')):
            self.tabs.addTab(chart, label)
        self.tabs.currentChanged.connect(self.describe)
        layout.addWidget(self.tabs)
        self.legend = QLabel()
        self.legend.setWordWrap(True)
        layout.addWidget(self.legend)
        self.note = QLabel()
        self.note.setWordWrap(True)
        self.note.setObjectName('muted')
        layout.addWidget(self.note)
        self.refresh()

    def set_report(self, report):
        self.report = report
        self.bilan.set_report(report)
        self.refresh()

    def refresh(self, *args):
        self.model = project_statistics(self.report, self.scope_filter.currentData())
        for chart, key in ((self.matchups, 'groups'), (self.turns, 'turns'), (self.events, 'events')):
            chart.set_rows(self.model[key])
        self.describe()

    def describe(self, *args):
        index, model = self.tabs.currentIndex(), self.model
        self.scope_filter.setEnabled(index != 0)
        self.summary.setText(T('Corpus conservé : n=') + str(model['total']) +
            (T(' · vue sélectionnée : n=') + str(model['scope_n']) + T(' · détails disponibles : ') + str(model['details_n']) if index else T(' · bilan descriptif, taux global inconnu')))
        if not self.report:
            self.summary.setText(T('Aucun rapport conservé disponible; aucun résultat calculé.'))
        notes = (T('Résultats du corpus enregistré; représentativité non établie.'),
                 T('Jusqu’à 8 familles affichées. Classification hypothétique; cliquer une barre pour ouvrir les combats.'),
                 T('Dernier tour visible dans chaque trace, pas la durée complète. Les tours inconnus restent séparés.'),
                 T('Occurrences consignées dans les traces disponibles, pas toutes les actions jouées. Une prise peut concerner plusieurs Récompenses.'))
        self.note.setText(notes[index])
        c = colors(self.theme)
        self.legend.setText(J(' · ',('<span style="color:' + c[color] + '">● ' + label + '</span>'
            for color, label in (('blue',T('Victoires')), ('red',T('Défaites')), ('yellow',T('Issues inconnues'))))) if index in (0, 1) else T('Effectifs absolus · survoler pour le détail'))

    def set_theme(self, theme):
        self.theme = theme
        for chart in (self.matchups, self.turns, self.events):
            chart.set_theme(theme)
        self.describe()

    def set_motion_enabled(self, enabled):
        for chart in (self.matchups, self.turns, self.events):
            chart.set_motion_enabled(enabled)
