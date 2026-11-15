"""Native count charts over existing report aggregates and observed traces."""
from pokemind.desktop.i18n import T, J, display
from PySide6.QtCore import Qt, Signal, QRectF, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import (QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout,
                              QComboBox, QTabWidget, QSizePolicy, QToolButton)
from pokemind.desktop.theme import colors
from pokemind.desktop.insights import project_statistics, project_public_stats, PUBLIC_REFRESH
from pokemind.desktop.i18n import QWidget, QFrame, QLabel, QComboBox, QTabWidget, QPushButton, Painter as QPainter


class CountChart(QWidget):
    selected = Signal(str)

    def __init__(self, *, grouped=False, series=None, interactive=True, accessible=None, empty=None):
        super().__init__()
        self.rows, self.regions = [], []
        self.grouped, self.hovered, self.theme = grouped, -1, 'dark'
        # Deck Lab › Statistiques reuses this chart for public counts (wins/losses/ties, placements).
        self.series = series or (T('victoires'), T('défaites'), T('issues inconnues'))
        self.interactive = grouped and interactive
        self.empty = empty or T('Aucune trace disponible pour cette vue.')
        self.motion_enabled, self._reveal = True, 1.0
        self.setMinimumHeight(245)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(accessible or (T('Effectifs observés par famille') if grouped else T('Effectifs des traces disponibles')))
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
        if row.get('description'):
            return row['description']
        if self.grouped:
            return row['label'] + ' : ' + J(', ',(str(v) + ' ' + label for v, label in zip(values, self.series))) + '; n=' + str(sum(values))
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
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, display(self.empty))
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
        self.setCursor(Qt.CursorShape.PointingHandCursor if self.interactive and self.hovered >= 0 else Qt.CursorShape.ArrowCursor)
        self.update()

    def leaveEvent(self, event):
        self.hovered = -1
        self.update()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.interactive:
            index = next((i for i, rect in enumerate(self.regions) if rect.contains(event.position())), -1)
            if index >= 0:
                self.selected.emit(self.rows[index]['label'])
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if self.rows and event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            self.hovered = (self.hovered + (1 if event.key() == Qt.Key.Key_Down else -1)) % len(self.rows)
            self.setToolTip(self.description(self.rows[self.hovered]))
            self.update()
        elif self.interactive and self.hovered >= 0 and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
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


class PublicStatsPanel(QFrame):
    """Deck Lab › Statistiques: public archetype figures, dated and sourced (PM-DECKLAB-PUBLIC-STATS-001).

    Read-only presentation of Services.deck_public_stats; the window owns jobs, tokens and refreshes.
    Every chart has a text twin (accessible description and the summary labels)."""
    refresh_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName('card')
        self.view, self.theme = None, 'dark'
        self._status_message = ''
        layout = QVBoxLayout(self)
        heading = QLabel(T('Statistiques publiques · par archétype', en='Public statistics · by archetype'))
        heading.setObjectName('sectionTitle')
        heading.setWordWrap(True)
        heading.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        layout.addWidget(heading)
        selectable = Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard
        self.identity = QLabel(T('Choisis un deck, puis ouvre cet onglet.', en='Choose a deck, then open this tab.'))
        self.identity.setWordWrap(True)
        self.identity.setTextFormat(Qt.TextFormat.PlainText)
        self.identity.setTextInteractionFlags(selectable)
        layout.addWidget(self.identity)
        controls = QHBoxLayout()
        self.mode = QComboBox()
        self.mode.setAccessibleName(T('Mode de match publié (BO1 ou BO3, jamais fusionnés)',
                                      en='Published match mode (BO1 or BO3, never merged)'))
        self.mode.currentIndexChanged.connect(self.render)
        controls.addWidget(self.mode, 1)
        self.refresh_button = QPushButton(T('Actualiser', en='Refresh'))
        self.refresh_button.setToolTip(T('Collecte publique bornée (quelques requêtes Limitless, sans clé, sans ta liste). '
                                         'Limitée par jour pour protéger le fournisseur.',
                                         en='Bounded public collection (a few keyless Limitless requests, never your list). '
                                         'Limited per day to protect the provider.'))
        self.refresh_button.clicked.connect(self.refresh_requested)
        controls.addWidget(self.refresh_button)
        layout.addLayout(controls)
        self.status = QLabel()
        self.status.setObjectName('muted')
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setTextInteractionFlags(selectable)
        layout.addWidget(self.status)
        self.rate_title = QLabel()
        self.rate_title.setWordWrap(True)
        layout.addWidget(self.rate_title)
        kpi = QHBoxLayout()
        self.value = QLabel('—')
        font = QFont(self.font())
        font.setPointSize(28)
        font.setBold(True)
        self.value.setFont(font)
        self.value.setStyleSheet('font-size: 32px; font-weight: 700;')
        self.value.setTextInteractionFlags(selectable)
        kpi.addWidget(self.value)
        self.sample = QLabel()
        self.sample.setWordWrap(True)
        self.sample.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.sample.setMinimumWidth(90)
        kpi.addWidget(self.sample)
        kpi.addStretch()
        layout.addLayout(kpi)
        self.availability = QLabel()
        self.availability.setWordWrap(True)
        layout.addWidget(self.availability)
        self.period = QLabel()
        self.period.setWordWrap(True)
        self.period.setTextInteractionFlags(selectable)
        layout.addWidget(self.period)
        self.chart_title = QLabel()
        self.chart_title.setWordWrap(True)
        layout.addWidget(self.chart_title)
        self.tabs = QTabWidget()
        self.matchups = CountChart(grouped=True, interactive=False,
            series=(T('victoires', en='wins'), T('défaites', en='losses'), T('nuls', en='ties')),
            accessible=T('Matchups publics de l’archétype : victoires, défaites, nuls par adversaire',
                         en='Public matchups of the archetype: wins, losses, ties per opponent'),
            empty=T('Aucun matchup public à afficher (archétype non identifié ou aucun match admissible).',
                    en='No public matchup to show (archetype not identified or no admissible match).'))
        self.meta = CountChart(accessible=T('Méta publique générale : placements classifiés par archétype',
                                            en='General public meta: classified placements per archetype'),
                               empty=T('Aucun instantané public.', en='No public snapshot.'))
        self.history = QLabel()
        self.history.setWordWrap(True)
        self.history.setTextFormat(Qt.TextFormat.PlainText)
        self.history.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.history.setTextInteractionFlags(selectable)
        self.tabs.addTab(self.matchups, T('Matchups', en='Matchups'))
        self.tabs.addTab(self.meta, T('Méta publique', en='Public meta'))
        self.tabs.addTab(self.history, T('Évolution', en='Trend'))
        layout.addWidget(self.tabs, 1)
        self.tabs.currentChanged.connect(self.render)
        self.legend = QLabel()
        self.legend.setWordWrap(True)
        layout.addWidget(self.legend)
        self.details_toggle = QToolButton()
        self.details_toggle.setCheckable(True)
        self.details_toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.details_toggle.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.details_toggle.toggled.connect(self.show_details)
        layout.addWidget(self.details_toggle)
        self.details = QFrame()
        details_layout = QVBoxLayout(self.details)
        details_layout.setContentsMargins(0, 4, 0, 0)
        self.identity_detail = QLabel()
        self.summary = QLabel()
        self.source = QLabel()
        self.source.setObjectName('muted')
        for label in (self.identity_detail, self.summary, self.source):
            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setTextInteractionFlags(selectable)
            label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            details_layout.addWidget(label)
        self.method = QLabel(T('Pourcentage seulement si n ≥ 10 par adversaire, ≥ 20 pour le taux global; '
            'BO1 et BO3 séparés. Méta : part seulement si ≥ 20 placements classifiés. ↑/↓ : détail des barres.',
            en='Percentage only with n ≥ 10 per opponent, ≥ 20 overall; BO1 and BO3 kept separate. '
            'Meta: share only with ≥ 20 classified placements. ↑/↓: bar details.'))
        self.method.setWordWrap(True)
        self.method.setTextInteractionFlags(selectable)
        details_layout.addWidget(self.method)
        note = QLabel(T('Tes statistiques personnelles restent dans Vue d’ensemble et Combats; elles ne sont jamais mélangées '
                        'à ces chiffres publics.', en='Your personal statistics stay in Overview and Battles; they are never '
                        'mixed with these public figures.'))
        note.setObjectName('muted')
        note.setWordWrap(True)
        note.setTextInteractionFlags(selectable)
        details_layout.addWidget(note)
        layout.addWidget(self.details)
        self.show_details(False)
        self.render()

    def show_details(self, expanded):
        self.details.setVisible(expanded)
        self.details_toggle.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)
        self.details_toggle.setAccessibleDescription(T('Développé' if expanded else 'Replié',
                                                       en='Expanded' if expanded else 'Collapsed'))

    def set_view(self, view):
        self.view = view
        self._status_message = ''
        self.details_toggle.setChecked(False)
        model = project_public_stats(view, self.mode.currentData())
        self.mode.blockSignals(True)
        self.mode.clear()
        for key, n in model['modes']:
            self.mode.addItem(key + ' · n=' + str(n), key)
        index = self.mode.findData(model['mode'])
        self.mode.setCurrentIndex(index if index >= 0 else 0)
        self.mode.setEnabled(self.mode.count() > 1)
        self.mode.blockSignals(False)
        self.render()

    def set_busy(self, busy, message=''):
        self.refresh_button.setEnabled(not busy)
        self._status_message = message
        if message:
            self.status.setText(message)

    def render(self, *args):
        model = project_public_stats(self.view, self.mode.currentData())
        self.details_toggle.setText(display(T('Sources et détails', en='Sources and details')))
        self.details_toggle.setAccessibleName(T('Sources et détails', en='Sources and details'))
        if self.view is None:
            self.identity.setText(T('Choisis un deck, puis ouvre cet onglet.', en='Choose a deck, then open this tab.'))
            self.source.setText('')
        else:
            identity = self.view.get('identity') or {}
            self.identity.setText((T('Archétype public : ', en='Public archetype: ') + str(identity['archetype_name'])
                                   + ' · PTCGL Standard') if identity.get('status') == 'IDENTIFIED' else model['identity'])
            self.source.setText(model['source'])
        self.identity_detail.setText(model['identity'])
        self.summary.setText(model['summary'])
        # Formatting only: use the chosen, already-computed mode; never combine populations.
        data = ((self.view or {}).get('archetype') or {}).get('modes', {}).get(model['mode'], {})
        fraction = data.get('win_fraction')
        number = f'{fraction * 100:.1f}' if fraction is not None else None
        self.rate_title.setText(T('Taux de victoire PUBLIC ', en='PUBLIC win rate ') + (model['mode'] or 'BO1 / BO3'))
        self.value.setText(T(number.replace('.', ',') + ' %', en=number + '%') if number is not None else '—')
        self.sample.setText('n=' + str(data['n']) + T(' matchs', en=' matches') if 'n' in data else T('n inconnu', en='n unknown'))
        self.availability.setText(T('Données insuffisantes', en='Insufficient data') if fraction is None
                                  else T('Taux de l’archétype, pas de tes 60 cartes ni de tes résultats.',
                                         en='Archetype rate, not your exact 60 cards or your results.'))
        window = (self.view or {}).get('window') or {}
        self.period.setText('Limitless · ' + str(window.get('since', '—')) + ' → ' + str(window.get('until', '—')))
        self.matchups.set_rows(model['matchup_rows'])
        self.meta.set_rows(model['meta_rows'])
        self.history.setText(model['history'])
        refresh = (self.view or {}).get('refresh') or {}
        outcome = ((self.view or {}).get('refresh_outcome') or refresh.get('last_outcome') or {}).get('status')
        message = model['refresh'] or (PUBLIC_REFRESH.get(outcome, str(outcome)) if outcome else '')
        stamp = (self.view or {}).get('last_success_at')
        self.status.setText(self._status_message or message or (T('Instantané : ', en='Snapshot: ') + str(stamp)[:10] if stamp
                                       else T('Aucun instantané public', en='No public snapshot')))
        c = colors(self.theme)
        if self.tabs.currentIndex() == 1:
            self.chart_title.setText(T('Méta publique · placements classifiés', en='Public meta · classified placements'))
            self.legend.setText(T('● Placements par archétype · population la plus large',
                                  en='● Placements per archetype · largest population'))
            return
        self.chart_title.setText(T('Matchups publics · nombre de victoires / défaites / nuls',
                                  en='Public matchups · wins / losses / ties'))
        if self.tabs.currentIndex() == 2:
            self.chart_title.setText(T('Évolution · part par tournoi', en='Trend · share per tournament'))
            self.legend.setText(T('Placements classifiés, pas résultats de matchs', en='Classified placements, not match outcomes'))
            return
        self.legend.setText(J(' · ', ('<span style="color:' + c[color] + '">● ' + display(label) + '</span>'
            for color, label in (('blue', T('Victoires', en='Wins')), ('red', T('Défaites', en='Losses')),
                                 ('yellow', T('Nuls', en='Ties'))))))

    def _retranslate(self):
        super()._retranslate()
        self.show_details(self.details_toggle.isChecked())
        self.render()

    def set_theme(self, theme):
        self.theme = theme
        self.matchups.set_theme(theme)
        self.meta.set_theme(theme)
        self.render()

    def set_motion_enabled(self, enabled):
        self.matchups.set_motion_enabled(enabled)
        self.meta.set_motion_enabled(enabled)
