"""Standalone, offline Qt design study. No Services/Store, data root, account or network.

Run from the repository: python demos/premium_decklab/demo.py
Original fictional art is generated in memory; opening this window writes nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui import (QColor, QFont, QPainter, QPainterPath, QPen, QPixmap,
                          QLinearGradient, QRadialGradient)
from PySide6.QtWidgets import (QApplication, QWidget, QFrame, QLabel, QVBoxLayout,
    QHBoxLayout, QGridLayout, QPushButton, QCheckBox, QScrollArea, QTabBar, QTextBrowser,
    QSizePolicy)
from pokemind.desktop.theme import BRAND, colors, palette, logo_pixmap
from pokemind.desktop.card_art import CardArt
from pokemind.desktop.motion import AnimatedStack
from artwork import CARDS, render_card

C = colors('dark')


def label(text, name='', wrap=False):
    value=QLabel(text);value.setObjectName(name);value.setWordWrap(wrap)
    value.setTextFormat(Qt.TextFormat.PlainText)
    return value


class DemoCard(CardArt):
    """The existing CardArt hover animation; all new painting stays in the demo."""
    def __init__(self, index, picture):
        super().__init__('')
        self.index, self.picture, self.selected = index, picture, False
        self.setObjectName('demoCard')
        self.setProperty('galleryArt', True)
        self.animation.setDuration(220)
        self.setMinimumSize(170,278)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(CARDS[index]['name']+' — carte fictive, sélectionner')

    def sizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(220,300)

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        height=min(self.height()-32,(self.width()-30)*1.4)
        width=height/1.4
        bounds=QRectF((self.width()-width)/2,(self.height()-height)/2,width,height)
        # Soft layered shadow, then optical lift inside an unchanged button rect.
        for spread,alpha in ((9,12),(6,22),(3,40)):
            p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(0,0,0,alpha))
            p.drawRoundedRect(bounds.adjusted(-spread,5-spread,spread,10+spread),13,13)
        p.translate(bounds.center()+QPointF(0,-5*self.hover))
        p.scale(1+.025*self.hover,1+.025*self.hover)
        target=QRectF(-width/2,-height/2,width,height)
        tint=QColor(CARDS[self.index]['color'])
        for spread in (7,4):
            tint.setAlpha(round((17 if spread==7 else 36)*self.hover))
            p.setPen(QPen(tint,spread));p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(target.adjusted(-2,-2,2,2),11,11)
        p.drawPixmap(target,self.picture,QRectF(self.picture.rect()))
        if self.hover:
            path=QPainterPath();path.addRoundedRect(target,10,10)
            shine=QLinearGradient(target.topLeft(),target.bottomRight())
            for stop,alpha in ((0,0),(.45,0),(.58,round(40*self.hover)),(.8,0),(1,0)):
                shine.setColorAt(stop,QColor(254,252,250,alpha))
            p.fillPath(path,shine)
        if self.selected:
            p.setPen(QPen(QColor(BRAND['gold']),2));p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(target.adjusted(-4,-4,4,4),13,13)
            p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(BRAND['gold']))
            p.drawEllipse(QPointF(target.right()-12,target.top()+12),10,10)
            p.setPen(QPen(QColor(C['background']),2));x,y=target.right()-12,target.top()+12
            p.drawPolyline([QPointF(x-4,y),QPointF(x-1,y+3),QPointF(x+5,y-4)])
        if self.hasFocus():
            p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor(C['focus']),1,Qt.PenStyle.DashLine))
            p.drawRoundedRect(target.adjusted(-8,-8,8,8),14,14)
        p.end()


class Composition(QWidget):
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(QFont('Segoe UI',12));p.setPen(QColor(C['muted']))
        p.drawText(24,38,'COMPOSITION FICTIVE — AUCUN RÉSULTAT DE PARTIE')
        for i,(name,n,tint) in enumerate((('Créatures',20,C['blue']),('Reliques',4,C['yellow']),('Énergies',36,C['success']))):
            y=90+i*88;w=max(50,self.width()-56)
            p.setPen(QColor(C['text']));p.drawText(24,y,f'{name}  ·  {n} cartes')
            p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(C['alternate']));p.drawRoundedRect(QRectF(24,y+14,w,12),6,6)
            p.setBrush(QColor(tint));p.drawRoundedRect(QRectF(24,y+14,w*n/60,12),6,6)
        p.end()


class DemoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PokeMind — Deck Lab · démonstration fictive')
        self.setObjectName('demoRoot');self.setMinimumSize(1100,760);self.resize(1360,900)
        self.setPalette(palette('dark'));self.setFont(QFont('Segoe UI',10))
        self.pictures=[QPixmap.fromImage(render_card(i)) for i in range(len(CARDS))]
        self.selected_index=0;self.replay_timers=[];self.closing=False
        self.setStyleSheet(self.css())
        outer=QHBoxLayout(self);outer.setContentsMargins(0,0,0,0);outer.setSpacing(0)
        sidebar=QFrame();sidebar.setObjectName('sidebar');sidebar.setFixedWidth(166)
        side=QVBoxLayout(sidebar);side.setContentsMargins(17,27,17,22);side.setSpacing(10)
        emblem=label('');emblem.setPixmap(logo_pixmap(52));side.addWidget(emblem)
        side.addWidget(label('PokeMind','brand'));side.addWidget(label('TCG COACH','eyebrow'));side.addSpacing(37)
        for text in ('Vue d’ensemble','Combats','Deck Lab','Cartes & méta','Apprentissage'):
            item=label(('▸  ' if text=='Deck Lab' else '   ')+text,'activeNav' if text=='Deck Lab' else 'navItem')
            side.addWidget(item)
        side.addStretch();side.addWidget(label('ÉTUDE VISUELLE','eyebrow'))
        side.addWidget(label('Hors ligne\nAucun compte connecté','muted',True));outer.addWidget(sidebar)
        content=QWidget();main=QVBoxLayout(content);main.setContentsMargins(24,20,24,15);main.setSpacing(15)
        top=QHBoxLayout();top.addWidget(label('ATELIER  /  DECK LAB','eyebrow'));top.addStretch()
        top.addWidget(label('DÉMONSTRATION FICTIVE','demoBadge'));main.addLayout(top)
        heading=QHBoxLayout();heading.addWidget(label('Deck Lab','pageTitle'));heading.addStretch()
        self.reduced=QCheckBox('Réduire les animations');self.reduced.toggled.connect(self.reduce_motion)
        heading.addWidget(self.reduced);main.addLayout(heading)
        hero=QFrame();hero.setObjectName('hero');h=QHBoxLayout(hero);h.setContentsMargins(19,15,19,15)
        titles=QVBoxLayout();titles.setSpacing(3);titles.addWidget(label('COLLECTION ORIGINES','heroKicker'))
        titles.addWidget(label('Orage astral','deckTitle'))
        titles.addWidget(label('6 illustrations originales · 60 cartes imaginaires','heroDescription'))
        h.addLayout(titles,1)
        self.replay=QPushButton('▶  Voir les effets');self.replay.clicked.connect(self.replay_effects);h.addWidget(self.replay)
        main.addWidget(hero)
        body=QHBoxLayout();body.setSpacing(18)
        center=QVBoxLayout();center.setSpacing(7)
        self.tabs=QTabBar();self.tabs.setExpanding(False)
        for name in ('Galerie','Liste texte','Statistiques'):self.tabs.addTab(name)
        self.tabs.setAccessibleName('Vues de la démonstration');center.addWidget(self.tabs)
        self.pages=AnimatedStack();self.pages.transition.animation.setDuration(180)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QFrame.Shape.NoFrame)
        gallery=QWidget();gl=QVBoxLayout(gallery);gl.setContentsMargins(0,12,0,12);gl.setSpacing(5)
        guide=QHBoxLayout();guide.addWidget(label('CONCEPTS ILLUSTRÉS','eyebrow'));guide.addStretch()
        guide.addWidget(label('Survolez · cliquez · Tab / Espace','muted'));gl.addLayout(guide)
        grid=QGridLayout();grid.setContentsMargins(0,0,0,0);grid.setHorizontalSpacing(7);grid.setVerticalSpacing(3)
        self.cards=[]
        for i,picture in enumerate(self.pictures):
            tile=DemoCard(i,picture);tile.clicked.connect(lambda checked=False,i=i:self.select_card(i))
            self.cards.append(tile);grid.addWidget(tile,i//3,i%3)
        gl.addLayout(grid);gl.addWidget(label('Créatures × 20  ·  Relique × 4  ·  Énergies × 36  /  Échantillon fictif, sans légalité TCG','muted',True))
        gl.addStretch();scroll.setWidget(gallery);self.gallery_scroll=scroll;self.pages.addWidget(scroll)
        text=QTextBrowser();text.setOpenExternalLinks(False)
        text.setPlainText('ORAGE ASTRAL — LISTE STRICTEMENT FICTIVE\n\n'+
                          '\n'.join('4 × '+c['name'] for c in CARDS)+
                          '\n36 × Énergie de l’horizon\n\n60 cartes imaginaires.\nAucune liste Pokémon TCG, aucune donnée de joueur.')
        self.pages.addWidget(text)
        composition=Composition();self.pages.addWidget(composition)
        self.tabs.currentChanged.connect(self.change_tab)
        center.addWidget(self.pages,1);body.addLayout(center,1)
        panel=QFrame();panel.setObjectName('details');panel.setFixedWidth(236)
        details=QVBoxLayout(panel);details.setContentsMargins(16,18,16,16);details.setSpacing(12)
        details.addWidget(label('LA CARTE EN VEDETTE','eyebrow'))
        self.details=AnimatedStack();self.details.transition.animation.setDuration(180)
        for i,card in enumerate(CARDS):
            page=QWidget();dl=QVBoxLayout(page);dl.setContentsMargins(0,0,0,0);dl.setSpacing(10)
            thumb=label('');thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumb.setPixmap(self.pictures[i].scaled(176,247,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
            dl.addWidget(thumb);dl.addWidget(label(card['name'],'detailName'))
            dl.addWidget(label(card['title'],'muted',True));dl.addWidget(label(card['role'],'role',True))
            dl.addWidget(label('« '+card['quote']+' »','lore',True));dl.addStretch();self.details.addWidget(page)
        details.addWidget(self.details,1)
        details.addWidget(label('UNE SÉLECTION, UN ACCENT','eyebrow'))
        details.addWidget(label('L’or garde ta sélection. La lumière suit le survol, sans déplacer la grille.','muted',True))
        details.addWidget(label('COACH  /  APERÇU LOCAL','coachLabel'))
        details.addWidget(label('Explore les cartes et les onglets. Aucun message n’est envoyé.','muted',True))
        body.addWidget(panel);main.addLayout(body,1)
        main.addWidget(label('Étude interactive Qt · Illustrations fictives originales · Aucun accès aux données PokeMind','footer'))
        outer.addWidget(content,1);self.select_card(0)

    @staticmethod
    def css():
        template='''
QWidget {background:transparent;color:@text;font-family:"Segoe UI";font-size:13px;}
QWidget#demoRoot {background:@background;}
QFrame#sidebar {background:@sidebar;border-right:1px solid @border;}
QLabel#brand {font-size:23px;font-weight:800;color:@text;}
QLabel#eyebrow {font-size:10px;font-weight:700;letter-spacing:1px;color:@muted;}
QLabel#navItem {padding:12px 0;color:@muted;font-size:12px;}
QLabel#activeNav {padding:12px 8px;color:@text;background:@primary;border:1px solid @blue;border-radius:9px;font-weight:700;}
QLabel#pageTitle {font-size:31px;font-weight:800;}
QLabel#demoBadge {font-size:9px;letter-spacing:1px;color:@accent;border:1px solid @border;border-radius:8px;padding:6px 9px;}
QFrame#hero {background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 @hero_start,stop:0.65 @surface,stop:1 @sidebar);border:1px solid @border;border-radius:14px;}
QLabel#heroKicker {font-size:10px;letter-spacing:2px;color:@hero_kicker;font-weight:700;}
QLabel#deckTitle {font-size:25px;font-weight:700;color:@hero_text;}
QLabel#heroDescription {color:@hero_muted;font-size:12px;}
QPushButton {background:@primary;color:@on_primary;border:1px solid @blue;border-radius:9px;padding:10px 12px;font-weight:600;}
QPushButton:hover {background:@primary_hover;border-color:@focus;}
QPushButton:focus {border-color:@focus;}
QPushButton#demoCard {background:transparent;border:0;padding:0;}
QTabBar::tab {color:@muted;background:transparent;border-bottom:2px solid transparent;padding:12px 16px;}
QTabBar::tab:selected {color:@text;border-color:@blue;}
QTabBar::tab:focus {color:@focus;}
QScrollArea {background:transparent;border:0;}
QScrollBar:vertical {background:@sidebar;width:6px;border-radius:3px;}
QScrollBar::handle:vertical {background:@border;min-height:25px;border-radius:3px;}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {height:0;}
QFrame#details {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 @surface,stop:1 @input);border:1px solid @border;border-radius:14px;}
QLabel#detailName {font-size:22px;font-weight:700;}
QLabel#role {color:@accent;font-size:10px;font-weight:700;}
QLabel#lore {color:@text;font-size:13px;}
QLabel#muted {color:@muted;font-size:11px;}
QLabel#coachLabel {color:@blue;font-weight:700;font-size:10px;border-top:1px solid @border;padding-top:14px;}
QLabel#footer {color:@muted;font-size:10px;}
QCheckBox {color:@muted;spacing:7px;font-size:11px;}
QTextBrowser {background:@input;color:@text;border:1px solid @border;border-radius:12px;padding:22px;font-size:15px;}
QWidget#motionOverlay {background:transparent;border:0;}
'''
        for key,value in sorted(C.items(),key=lambda item:-len(item[0])):
            template=template.replace('@'+key,value)
        return template

    def paintEvent(self,event):
        p=QPainter(self);p.fillRect(self.rect(),QColor(C['background']))
        glow=QRadialGradient(self.width()*.5,120,self.width()*.65)
        glow.setColorAt(0,QColor(7,147,250,25));glow.setColorAt(1,QColor(7,20,47,0))
        p.fillRect(self.rect(),glow);p.end()

    def select_card(self,index):
        self.selected_index=index
        for i,card in enumerate(self.cards):card.selected=i==index;card.update()
        self.details.setCurrentIndex(index)

    def change_tab(self,index):
        self.pages.setCurrentIndex(index)

    def reduce_motion(self,reduced):
        self.stop_replay()
        for card in self.cards:card.set_motion_enabled(not reduced)
        for stack in (self.pages,self.details):stack.set_motion_enabled(not reduced)

    def stop_replay(self):
        for timer in self.replay_timers:timer.stop();timer.deleteLater()
        self.replay_timers=[]

    def replay_effects(self):
        self.stop_replay()
        self.tabs.setCurrentIndex(0)
        if self.reduced.isChecked():
            self.select_card((self.selected_index+1)%len(self.cards))
            return
        # Bounded one-shot actions, only on request. No idle or looping timer.
        for delay,action in ((150,lambda:self.cards[1].animate(1)),
                             (850,lambda:self.select_card(1)),
                             (1400,lambda:self.cards[1].animate(0)),
                             (1800,lambda:self.tabs.setCurrentIndex(2)),
                             (2600,lambda:self.tabs.setCurrentIndex(0))):
            timer=QTimer(self);timer.setSingleShot(True)
            timer.timeout.connect(action);timer.start(delay);self.replay_timers.append(timer)

    def hideEvent(self,event):
        self.stop_replay()
        super().hideEvent(event)

    def closeEvent(self,event):
        self.closing=True;self.stop_replay()
        for card in self.cards:card.set_motion_enabled(False)
        for stack in (self.pages,self.details):stack.set_motion_enabled(False)
        super().closeEvent(event)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--smoke',action='store_true',help='open the native synthetic window briefly and exit')
    args=parser.parse_args(argv)
    app=QApplication.instance() or QApplication([])
    window=DemoWindow();window.show()
    if args.smoke:
        def finish():
            print(json.dumps(dict(visible=window.isVisible(),cards=len(window.cards),
                                  width=window.width(),tabs=window.tabs.count(),personal_data_access=False)))
            window.close();app.quit()
        QTimer.singleShot(300,finish)
    return app.exec()


if __name__=='__main__':
    raise SystemExit(main())
