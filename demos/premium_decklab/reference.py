"""Private reference study: actual Qt dock/layout vocabulary, no production services.

python demos/premium_decklab/reference.py
The production MainWindow constructs Store, Services, jobs and history at startup;
this deliberately small presentation adapter never constructs that object.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtCore import Qt, QTimer, QSize, QRectF, QEvent
from PySide6.QtGui import QFont, QPixmap, QColor, QPainter, QPainterPath, QLinearGradient, QRadialGradient, QPen
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QLabel,
    QHBoxLayout, QVBoxLayout, QGridLayout, QDockWidget, QComboBox, QCheckBox,
    QPushButton, QScrollArea, QTabBar, QTextBrowser, QListWidget, QSizePolicy)
from pokemind.desktop.theme import colors, palette, BRAND, logo_pixmap, navigation_icon
from pokemind.desktop.motion import AnimatedStack
from pokemind.desktop.widgets import ChatInput
from demo import DemoCard, label, DemoWindow
from artwork import CARDS, render_card, creature

C = colors('dark')
NAVIGATION = ('Vue d’ensemble', 'Combats', 'Deck Lab', 'Cartes & méta',
              'Apprentissage', 'Réglages', 'Terminal')


def inactive(text):
    button = QPushButton(text)
    button.setEnabled(False)
    button.setToolTip('Commande du vrai PokeMind · indisponible dans cet aperçu isolé')
    return button


def combo(items):
    value = QComboBox()
    value.addItems(items)
    value.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
    value.setMinimumContentsLength(8)
    value.setEnabled(False)
    return value


class DeckBanner(QFrame):
    """Cached panoramic original art, independent of the concept reference pixels."""
    def __init__(self, picture):
        super().__init__()
        self.picture = picture
        self.setObjectName('referenceHero')
        self.scene = QPixmap(1100, 220)
        self.scene.fill(QColor(C['input']))
        p = QPainter(self.scene)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        backdrop = QLinearGradient(0, 0, 1100, 220)
        for stop, color in ((0, C['sidebar']), (.5, C['surface']), (1, BRAND['bleu_royal'])):
            backdrop.setColorAt(stop, QColor(color))
        p.fillRect(self.scene.rect(), backdrop)
        for x, tint in ((850, BRAND['cyan']), (1080, BRAND['gold'])):
            glow = QRadialGradient(x, 90, 310)
            color = QColor(tint); color.setAlpha(110)
            glow.setColorAt(0, color); glow.setColorAt(1, QColor(0, 0, 0, 0))
            p.fillRect(self.scene.rect(), glow)
        # Separate transparent sprite: preserve aspect ratio at either window width.
        # Bounds include every dragon stroke, wings, crest and tail (artwork.py).
        self.creature_bounds = QRectF(39, 116, 330, 296)
        self.sprite = QPixmap(330, 296)
        self.sprite.fill(Qt.GlobalColor.transparent)
        art = QPainter(self.sprite)
        art.setRenderHint(QPainter.RenderHint.Antialiasing)
        art.translate(-39, -116)
        creature(art, CARDS[0]); art.end()
        p.setPen(QPen(QColor(104, 214, 249, 65), 1))
        for i in range(6):
            p.drawArc(QRectF(590+i*19, -160+i*8, 500, 430), 200*16, 100*16)
        fade = QLinearGradient(250, 0, 800, 0)
        fade.setColorAt(0, QColor(C['sidebar'])); fade.setColorAt(1, QColor(8, 30, 74, 0))
        p.fillRect(self.scene.rect(), fade)
        p.end()

    def art_rect(self):
        safe = QRectF(self.width()-172, 7, 156, self.height()-14)
        scale = min(safe.width()/self.sprite.width(), safe.height()/self.sprite.height())
        width, height = self.sprite.width()*scale, self.sprite.height()*scale
        return QRectF(safe.center().x()-width/2, safe.center().y()-height/2, width, height)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath(); path.addRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 14, 14)
        p.setClipPath(path)
        p.drawPixmap(self.rect(), self.scene)
        p.drawPixmap(self.art_rect(), self.sprite, QRectF(self.sprite.rect()))
        p.setClipping(False)
        for thickness, alpha in ((7, 18), (3, 40), (1, 210)):
            p.setPen(QPen(QColor(7, 147, 250, alpha), thickness))
            p.drawPath(path)
        p.setPen(QPen(QColor(BRAND['gold']), 2))
        p.drawLine(20, self.height()-2, 150, self.height()-2)
        p.end()


class StudySurface(QWidget):
    """Quiet electric edge and ambient light, behind native child widgets."""
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(C['background']))
        light = QRadialGradient(self.width()*.7, 100, self.width()*.85)
        light.setColorAt(0, QColor(7, 147, 250, 38))
        light.setColorAt(1, QColor(7, 20, 47, 0))
        p.fillRect(self.rect(), light)
        bounds = QRectF(self.rect()).adjusted(3, 3, -3, -3)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for thickness, alpha in ((6, 12), (3, 24), (1, 150)):
            p.setPen(QPen(QColor(7, 147, 250, alpha), thickness))
            p.drawRoundedRect(bounds, 16, 16)
        p.end()


class GallerySleeve(QFrame):
    """Reserve wrapped label height, as the production CardTile does."""
    def fit_height(self):
        if self.layout():
            height = max(0, self.layout().totalHeightForWidth(self.width()))
            if height != self.minimumHeight():
                self.setMinimumHeight(height)

    def resizeEvent(self, event):
        self.fit_height()
        super().resizeEvent(event)

    def event(self, event):
        if event.type() == QEvent.Type.LayoutRequest:
            self.fit_height()
        return super().event(event)


class ReferenceWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PokeMind · Coach & Deck Lab — aperçu privé')
        self.setObjectName('referenceRoot')
        self.setMinimumSize(1100, 900)
        self.resize(1500, 970)
        self.setFont(QFont('Segoe UI', 10))
        self.setPalette(palette('dark'))
        self.setStyleSheet(self.css())
        self.pictures = [QPixmap.fromImage(render_card(i)) for i in range(6)]
        self.selected_index = 0
        self.columns = 0
        central = QWidget()
        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.sidebar = QFrame()
        self.sidebar.setObjectName('referenceSidebar')
        self.sidebar.setFixedWidth(178)
        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(12, 24, 12, 18)
        emblem = label('')
        emblem.setPixmap(logo_pixmap(82))
        emblem.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side.addWidget(emblem)
        brand = label('PokeMind', 'brand')
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side.addWidget(brand)
        caption = label('TON COMPAGNON TCG', 'eyebrow')
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side.addWidget(caption)
        side.addSpacing(24)
        self.navigation = QListWidget()
        self.navigation.setAccessibleName('Navigation principale · aperçu Deck Lab seulement')
        self.navigation.setIconSize(QSize(20, 20))
        for i, text in enumerate(NAVIGATION):
            self.navigation.addItem(text)
            self.navigation.item(i).setIcon(navigation_icon(i))
            if i != 2:
                self.navigation.item(i).setFlags(Qt.ItemFlag.NoItemFlags)
        self.navigation.setCurrentRow(2)
        self.navigation.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        side.addWidget(self.navigation, 1)
        side.addWidget(label('DECK DE DÉMONSTRATION', 'eyebrow', True))
        side.addWidget(label('Orage astral', 'detailName'))
        side.addWidget(label('60 cartes imaginaires\nAucune légalité TCG établie', 'muted', True))
        side.addSpacing(18)
        side.addWidget(label('FR-CA  ·  Sombre\nAperçu hors ligne', 'muted', True))
        outer.addWidget(self.sidebar)
        content = StudySurface()
        main = QVBoxLayout(content)
        main.setContentsMargins(16, 14, 16, 10)
        main.setSpacing(8)
        title = QHBoxLayout()
        title.addWidget(label('Deck Lab', 'pageTitle'))
        title.addStretch()
        self.reduced = QCheckBox('Réduire les animations')
        self.reduced.toggled.connect(self.reduce_motion)
        title.addWidget(self.reduced)
        main.addLayout(title)
        hero = DeckBanner(self.pictures[0])
        self.hero = hero
        hl = QVBoxLayout(hero)
        hl.setContentsMargins(20, 8, 180, 8)
        hl.setSpacing(4)
        hl.addWidget(label('APERÇU HORS LIGNE', 'heroKicker'))
        hl.addWidget(label('Orage astral', 'deckTitle'))
        hl.addWidget(label('60 cartes imaginaires · non jouable', 'heroDescription', True))
        main.addWidget(hero)
        picker = QHBoxLayout()
        self.deck_picker = combo(['Orage astral · v1 fictive'])
        picker.addWidget(self.deck_picker, 1)
        picker.addWidget(inactive('☆ Favori'))
        picker.addWidget(inactive('☆ Deck principal'))
        main.addLayout(picker)
        # Same three views as MainWindow._decks; no invented simulator or optimizer.
        self.tabs = QTabBar()
        self.tabs.setExpanding(False)
        for text in ('Galerie · 60/60', 'Liste texte', 'Statistiques'):
            self.tabs.addTab(text)
        main.addWidget(self.tabs)
        self.pages = AnimatedStack()
        self.pages.transition.animation.setDuration(180)
        self.gallery_scroll = QScrollArea()
        self.gallery_scroll.setWidgetResizable(True)
        self.gallery_scroll.setFrameShape(QFrame.Shape.NoFrame)
        gallery = QWidget()
        gl = QVBoxLayout(gallery)
        gl.setContentsMargins(0, 4, 0, 8)
        gl.setSpacing(5)
        gl.addWidget(label('ILLUSTRATIONS FICTIVES  ·  24 CARTES', 'sectionTitle'))
        self.grid = QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(12)
        self.grid.setVerticalSpacing(14)
        self.cards = []
        self.tiles = []
        for i, picture in enumerate(self.pictures):
            cell = GallerySleeve()
            cell.setObjectName('gallerySleeve')
            cell.setMinimumWidth(190)
            cell.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            cl = QVBoxLayout(cell)
            cl.setContentsMargins(5, 2, 5, 9)
            cl.setSpacing(0)
            card = DemoCard(i, picture)
            card.setMinimumSize(180, 280)
            card.setFixedHeight(330)
            card.clicked.connect(lambda checked=False, i=i: self.select_card(i))
            cl.addWidget(card)
            name = label(CARDS[i]['name'] + '  ×4', 'cardCaption', True)
            name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(name)
            subtitle = label(CARDS[i]['title'], 'cardSubtitle', True)
            subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(subtitle)
            self.cards.append(card)
            self.tiles.append(cell)
        gl.addLayout(self.grid)
        gl.addWidget(label('ÉNERGIES FICTIVES  ·  36 CARTES', 'sectionTitle'))
        gl.addWidget(label('36 × Énergie de l’horizon · sans image officielle, sans cache utilisateur', 'muted', True))
        gl.addStretch()
        self.gallery_scroll.setWidget(gallery)
        self.pages.addWidget(self.gallery_scroll)
        text = QTextBrowser()
        text.setPlainText('ORAGE ASTRAL — EXEMPLE NON JOUABLE\n\n' +
            '\n'.join('4 × ' + c['name'] for c in CARDS) +
            '\n36 × Énergie de l’horizon\n\n60 cartes imaginaires. Aucune liste Pokémon TCG légale.')
        self.pages.addWidget(text)
        stats = QTextBrowser()
        stats.setPlainText('STATISTIQUES PUBLIQUES\n\nDonnées insuffisantes.\n\nAucune collecte dans cet aperçu.\nAucun taux de victoire ni impact estimé.\n\nDans PokeMind : données publiques datées par archétype,\navec taille d’échantillon et limites explicites.')
        self.pages.addWidget(stats)
        main.addWidget(self.pages, 1)
        self.tabs.currentChanged.connect(self.pages.setCurrentIndex)
        self.details = AnimatedStack()
        self.details.setFixedHeight(80)
        self.details.transition.animation.setDuration(180)
        self.details.setObjectName('selectionPanel')
        for i, card in enumerate(CARDS):
            page = QWidget()
            row = QHBoxLayout(page)
            row.setContentsMargins(12, 4, 12, 4)
            thumb = label('')
            thumb.setPixmap(self.pictures[i].scaled(43, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            row.addWidget(thumb)
            words = QVBoxLayout()
            words.addWidget(label(card['name'] + '  ·  ×4', 'detailName', True))
            words.addWidget(label(card['title'] + ' · illustration fictive', 'muted', True))
            row.addLayout(words, 1)
            self.details.addWidget(page)
        self.detail_toggle = QPushButton()
        self.detail_toggle.setCheckable(True)
        self.detail_toggle.setFixedHeight(32)
        self.detail_toggle.setObjectName('detailToggle')
        self.detail_toggle.setAccessibleName('Afficher ou masquer les détails de la carte sélectionnée')
        self.detail_toggle.toggled.connect(self.details.setVisible)
        main.addWidget(self.detail_toggle)
        main.addWidget(self.details)
        self.details.hide()
        main.addWidget(label('Données de démonstration · Survol / clic / Tab / Espace · Collection et légalité distinctes', 'footer', True))
        outer.addWidget(content, 1)
        self.setCentralWidget(central)
        self._coach()
        self.select_card(0)
        self.reflow()

    def _coach(self):
        self.chat_dock = QDockWidget('Assistant PokeMind', self)
        self.chat_dock.setObjectName('referenceCoach')
        self.chat_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.chat_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        title = QFrame()
        title.setObjectName('coachTitle')
        row = QHBoxLayout(title)
        row.setContentsMargins(16, 16, 16, 16)
        icon = label('')
        icon.setPixmap(logo_pixmap(44))
        row.addWidget(icon)
        title_words = QVBoxLayout()
        title_words.addWidget(label('Coach IA', 'coachHeading'))
        title_words.addWidget(label('POKEMIND  /  TON COMPAGNON TCG', 'eyebrow', True))
        row.addLayout(title_words, 1)
        self.chat_dock.setTitleBarWidget(title)
        body = QWidget()
        body.setMinimumWidth(355)  # exact minimum used by MainWindow._chat
        body.setMaximumWidth(355)
        body.setObjectName('coachBody')
        layout = QVBoxLayout(body)
        layout.setContentsMargins(15, 15, 15, 16)
        layout.setSpacing(9)
        layout.addWidget(combo(['Codex · session CLI', 'Claude Code · session CLI', 'Ollama · local']))
        layout.addWidget(label('●  APERÇU HORS LIGNE  ·  Données de démonstration', 'permissionBadge', True))
        history = QHBoxLayout()
        history.addWidget(combo(['Historique des discussions']), 1)
        history.addWidget(inactive('Nouveau'))
        layout.addLayout(history)
        self.transcript = QTextBrowser()
        self.transcript.setObjectName('coachWelcome')
        self.transcript.setFixedHeight(154)
        self.transcript.setOpenExternalLinks(False)
        self.transcript.setHtml('<p style="margin:0 0 8px 0;color:'+C['blue']+';font-size:12px"><b>ESPACE DE DISCUSSION</b></p>'
            '<p style="margin:0;font-size:24px"><b>Un autre regard<br>sur ton deck.</b></p>')
        layout.addStretch(1)
        layout.addWidget(self.transcript)
        for number, heading, description in (
            ('01', 'Ton moteur, ton choix', 'Codex, Claude Code ou Ollama.'),
            ('02', 'Une discussion à la demande', 'Aucune réponse IA simulée ici.'),
            ('03', 'Tu gardes le contrôle', 'Aucun compte connecté. Aucun envoi.')):
            panel = GallerySleeve(); panel.setObjectName('coachCard')
            line = QHBoxLayout(panel); line.setContentsMargins(12, 8, 12, 8)
            marker = label(number, 'coachNumber'); marker.setFixedWidth(28)
            line.addWidget(marker, 0, Qt.AlignmentFlag.AlignTop)
            words = QVBoxLayout(); words.setSpacing(5)
            words.addWidget(label(heading, 'coachCardTitle', True))
            words.addWidget(label(description, 'coachDescription', True))
            line.addLayout(words, 1)
            layout.addWidget(panel)
        layout.addStretch(1)
        layout.addWidget(label('Connexion au premier message dans l’application réelle', 'muted', True))
        self.chat_input = ChatInput()
        self.chat_input.setPlaceholderText('Écris ta question ou colle ton journal TCG Live…')
        self.chat_input.setAccessibleName('Message à PokeMind · désactivé pour cet aperçu')
        self.chat_input.setFixedHeight(85)
        self.chat_input.setEnabled(False)
        layout.addWidget(self.chat_input)
        tools = QHBoxLayout()
        tools.addWidget(combo(['Idées de questions']), 1)
        tools.addWidget(inactive('Joindre un journal'))
        layout.addLayout(tools)
        actions = QHBoxLayout()
        actions.addWidget(combo(['Coach', 'Recherche web']), 1)
        actions.addWidget(inactive('Envoyer ↵'))
        actions.addWidget(inactive('Arrêter'))
        layout.addLayout(actions)
        self.chat_dock.setWidget(body)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.chat_dock)

    @staticmethod
    def css():
        return DemoWindow.css() + '''
QMainWindow#referenceRoot {background:@background;}
QFrame#referenceSidebar {background:@sidebar;border-right:1px solid @border;}
QListWidget {background:transparent;border:0;outline:0;font-size:12px;}
QListWidget::item {padding:13px 3px;border-radius:8px;margin-bottom:5px;}
QListWidget::item:selected {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 @primary,stop:1 @sidebar);color:@text;border:1px solid @blue;}
QListWidget::item:disabled {color:@muted;}
QFrame#referenceHero {background:@surface;border:1px solid @blue;border-radius:12px;}
QLabel#pageTitle {font-size:34px;}
QLabel#muted, QLabel#footer, QLabel#eyebrow, QCheckBox {font-size:12px;}
QLabel#heroKicker {font-size:12px;letter-spacing:1px;}
QPushButton#detailToggle {text-align:left;padding:5px 10px;font-size:13px;background:@surface;border-color:@accent;}
QPushButton#detailToggle:focus {border:2px solid @accent;}

QLabel#deckTitle {font-size:30px;font-weight:800;}
QLabel#heroDescription {font-size:13px;}
QLabel#sectionTitle {color:@text;font-size:13px;font-weight:700;padding:8px 4px;border-bottom:1px solid @border;}
QLabel#cardCaption {color:@text;font-size:17px;font-weight:700;padding:2px 0;}
QLabel#cardSubtitle {color:@muted;font-size:13px;padding:1px 3px;}
QFrame#gallerySleeve {background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 @surface,stop:0.5 @input,stop:1 @background);border:1px solid @border;border-radius:14px;}
QFrame#gallerySleeve[selected="true"] {border-color:@accent;}
QWidget#selectionPanel {background:@surface;border:1px solid @accent;border-radius:10px;}
QFrame#coachTitle {background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 @surface,stop:1 @sidebar);border:1px solid @blue;border-radius:12px;}
QLabel#coachHeading {font-size:25px;font-weight:800;}
QWidget#coachBody {background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 @input,stop:0.6 @background,stop:1 @sidebar);border-left:1px solid @blue;}
QLabel#permissionBadge {color:@accent;background:@surface;border:1px solid @border;border-radius:8px;padding:10px;font-size:12px;}
QTextBrowser#coachWelcome {background:transparent;border:0;padding:3px;}
QFrame#coachCard {background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 @surface,stop:1 @input);border:1px solid @border;border-radius:12px;}
QLabel#coachNumber {color:@blue;font-size:16px;font-weight:700;padding-top:2px;}
QLabel#coachCardTitle {font-size:14px;font-weight:700;}
QLabel#coachDescription {color:@muted;font-size:13px;}
QComboBox {background:@input;color:@text;border:1px solid @border;border-radius:7px;padding:7px;font-size:12px;}
QPushButton:disabled {color:@muted;background:@surface;border-color:@border;font-size:12px;padding:8px;}
QComboBox:disabled {color:@muted;}
QTextEdit {background:@background;color:@text;border:1px solid @border;border-radius:9px;padding:8px;}
QTextBrowser {font-size:13px;padding:12px;}
'''.replace('@background', C['background']).replace('@sidebar', C['sidebar']).replace('@border', C['border']).replace('@primary', C['primary']).replace('@surface', C['surface']).replace('@input', C['input']).replace('@accent', C['accent']).replace('@muted', C['muted']).replace('@text', C['text']).replace('@blue', C['blue'])

    def reflow(self):
        width = self.gallery_scroll.viewport().width()
        # Six originals: balanced 3x2 or 2x3 rows instead of a lonely sixth tile.
        columns = 3 if width >= 700 else 2
        if columns == self.columns:
            return
        while self.grid.count():
            self.grid.takeAt(0)
        for col in range(3):
            self.grid.setColumnStretch(col, 1 if col < columns else 0)
        for i, cell in enumerate(self.tiles):
            self.grid.addWidget(cell, i // columns, i % columns)
        self.columns = columns

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'gallery_scroll'):
            self.reflow()

    def showEvent(self, event):
        super().showEvent(event)
        self.reflow()

    def select_card(self, index):
        self.selected_index = index
        self.detail_toggle.setText(CARDS[index]['name'] + '  ×4  ·  Détails ▾')
        for i, card in enumerate(self.cards):
            card.selected = i == index
            card.update()
            self.tiles[i].setProperty('selected', i == index)
            self.tiles[i].style().unpolish(self.tiles[i])
            self.tiles[i].style().polish(self.tiles[i])
        self.details.setCurrentIndex(index)

    def reduce_motion(self, reduced):
        for card in self.cards:
            card.set_motion_enabled(not reduced)
        for stack in (self.pages, self.details):
            stack.set_motion_enabled(not reduced)

    def closeEvent(self, event):
        self.reduce_motion(True)
        super().closeEvent(event)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    app = QApplication.instance() or QApplication([])
    window = ReferenceWindow()
    window.show()
    if args.smoke:
        def finish():
            print(json.dumps(dict(visible=window.isVisible(), width=window.width(),
                height=window.height(), columns=window.columns, cards=len(window.cards),
                dock_right=window.dockWidgetArea(window.chat_dock)==Qt.DockWidgetArea.RightDockWidgetArea)))
            window.close()
            app.quit()
        QTimer.singleShot(400, finish)
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
