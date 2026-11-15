"""Original fictional illustrations, drawn locally with Qt; no external assets.

Copyright (c) 2026 PokeMind contributors. MIT, like this repository.
These creatures, names and concept cards are invented, not Pokémon TCG cards.
"""
from __future__ import annotations

import math
import random
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QColor, QFont, QImage, QLinearGradient, QPainter,
                          QPainterPath, QPen, QPolygonF, QRadialGradient)


CARDS = (
    dict(name='Aurex', title='Dragon des aurores', kind='dragon', color='#68D6F9',
         dark='#122F72', quote='Quand le ciel se fend, ses ailes deviennent lumière.', role='ÉLAN / ÉLECTRIQUE'),
    dict(name='Flamaris', title='Renard des braises', kind='fox', color='#FFBD6D',
         dark='#6C263B', quote='Une étincelle suffit à réveiller toute la forêt.', role='IMPULSION / FEU'),
    dict(name='Nérélys', title='Raie des profondeurs', kind='ray', color='#71F4DA',
         dark='#07515D', quote='Elle suit les courants que personne ne peut voir.', role='FLUIDITÉ / EAU'),
    dict(name='Sylvar', title='Gardien des cimes', kind='stag', color='#BAEBA2',
         dark='#214C49', quote='Chaque ramure porte un fragment de printemps.', role='ANCRAGE / NATURE'),
    dict(name='Noctéa', title='Oracle des étoiles', kind='owl', color='#D3B5FF',
         dark='#403266', quote='Son regard garde la mémoire des constellations.', role='VISION / ASTRE'),
    dict(name='Prisme originel', title='Relique de l’horizon', kind='crystal', color='#FECF4D',
         dark='#4E4252', quote='Six reflets. Une seule source d’énergie.', role='RELIQUE / LUMIÈRE'),
)


def path(points):
    """An illustration contour: move, cubic curves, lines, close."""
    shape = QPainterPath(QPointF(*points[0]))
    for segment in points[1:]:
        if len(segment) == 6:
            shape.cubicTo(*segment)
        else:
            shape.lineTo(*segment)
    shape.closeSubpath()
    return shape


def polygon(p, points, fill, edge=None, width=1.5):
    p.setBrush(QColor(fill))
    p.setPen(QPen(QColor(edge), width) if edge else Qt.PenStyle.NoPen)
    p.drawPolygon(QPolygonF([QPointF(*point) for point in points]))


def creature(p, card):
    """Sculpted silhouettes, facets and details in a 400 x 560 composition."""
    tint, kind = card['color'], card['kind']
    pale = QColor(tint).lighter(125).name()
    shade = QColor(tint).darker(230).name()
    p.setPen(QPen(QColor(tint), 2))
    p.setBrush(QColor(shade))
    if kind == 'dragon':
        # Swept wings, curved neck, long tail, angular head and luminous crest.
        polygon(p, [(199,283),(64,140),(76,236),(42,290),(141,268),(166,333)], shade, tint)
        polygon(p, [(219,270),(341,131),(313,238),(366,273),(270,283),(249,337)], shade, tint)
        for a,b in [((199,283),(76,236)),((199,283),(64,140)),((219,270),(313,238)),((219,270),(341,131))]:
            p.drawLine(QPointF(*a),QPointF(*b))
        body = path([(231,212),(295,244,258,325,222,333),(174,344,170,375,241,398),
                     (153,409,127,356,183,315),(228,285,218,267,197,246),(209,227)])
        p.setBrush(QColor(tint));p.drawPath(body)
        polygon(p, [(197,247),(176,223),(197,195),(235,184),(257,209),(229,232)], tint, pale)
        polygon(p, [(198,200),(177,162),(213,192)], pale)
        polygon(p, [(229,188),(252,150),(245,206)], pale)
        polygon(p, [(188,227),(208,217),(210,225)], '#07142F')
        p.setPen(QPen(QColor(pale),4));p.drawLine(233,259,217,297)
        for i in range(5):
            polygon(p, [(246-i*5,272+i*9),(266-i*7,270+i*9),(241-i*5,282+i*9)], pale)
        p.setPen(QPen(QColor(tint), 3));p.drawPolyline(QPolygonF([QPointF(94,119),QPointF(120,148),QPointF(107,153),QPointF(139,185)]))
    elif kind == 'fox':
        for index in range(3):
            p.save();p.translate(205,307);p.rotate((index-1)*28)
            flame = path([(0,25),(-116,-24,-120,-92,-69,-153),(-82,-70,-26,-73,0,-13),
                          (40,-107,65,-128,89,-164),(75,-44,99,-13,0,25)])
            g=QLinearGradient(0,-165,0,30);g.setColorAt(0,QColor('#FFF1BD'));g.setColorAt(1,QColor('#E65E42'))
            p.setBrush(g);p.setPen(Qt.PenStyle.NoPen);p.drawPath(flame);p.restore()
        polygon(p, [(156,267),(209,246),(263,287),(248,371),(153,372),(136,319)], '#E77D52', tint, 3)
        polygon(p, [(141,246),(133,168),(184,205),(219,201),(271,164),(263,254),(218,293),(185,293)], tint, pale, 3)
        polygon(p, [(143,193),(149,234),(171,216)], '#6C263B')
        polygon(p, [(256,190),(251,232),(233,215)], '#6C263B')
        polygon(p, [(155,246),(192,250),(204,275),(216,250),(250,242),(220,292),(185,292)], '#FFF1D3')
        polygon(p, [(190,268),(218,268),(204,279)], '#34213C')
        p.setPen(QPen(QColor('#34213C'),5));p.drawLine(159,237,181,242);p.drawLine(227,241,246,234)
        polygon(p, [(165,315),(204,339),(241,312),(225,369),(178,369)], '#FFF1D3')
    elif kind == 'ray':
        wing=path([(201,232),(150,225,113,165,49,186),(78,248,65,283,117,300),
                   (146,303,171,284,201,277),(238,297,263,310,300,293),(337,274,318,227,355,184),
                   (279,176,256,229,201,232)])
        g=QLinearGradient(120,190,240,320);g.setColorAt(0,QColor('#B3FFF1'));g.setColorAt(1,QColor('#12889E'))
        p.setBrush(g);p.drawPath(wing)
        p.setPen(QPen(QColor(tint),8,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
        tail=QPainterPath(QPointF(201,267));tail.cubicTo(164,329,271,361,213,405);p.drawPath(tail)
        polygon(p, [(201,210),(232,255),(202,286),(172,255)], '#125B77', tint)
        p.setPen(QPen(QColor('#E5FFFA'),3))
        for side in (-1,1):
            for i in range(4):
                p.drawLine(QPointF(201+side*(40+i*18),246-i*4),QPointF(201+side*(46+i*22),270-i*3))
        p.setPen(QPen(QColor('#FFF1BD'),5));p.drawPoint(190,246);p.drawPoint(214,246)
    elif kind == 'stag':
        polygon(p, [(142,286),(237,275),(266,307),(228,329),(226,386),(209,386),(201,331),
                    (169,326),(154,385),(138,385),(148,322),(122,308)], shade, tint,3)
        polygon(p, [(219,294),(215,242),(230,206),(254,219),(259,253),(242,296)], tint,pale,3)
        polygon(p, [(227,218),(209,192),(237,207)],pale)
        polygon(p, [(251,221),(278,201),(262,231)],pale)
        p.setPen(QPen(QColor('#E5D5A5'),6,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
        for side in (-1,1):
            horn=QPainterPath(QPointF(240+side*8,211));horn.cubicTo(240+side*44,187,240+side*38,148,240+side*58,130);p.drawPath(horn)
            p.drawLine(QPointF(240+side*34,177),QPointF(240+side*65,162))
            p.drawLine(QPointF(240+side*36,165),QPointF(240+side*23,143))
            polygon(p, [(240+side*63,157),(240+side*86,143),(240+side*76,169)],tint)
        p.setPen(QPen(QColor('#07142F'),4));p.drawPoint(245,241)
        p.setPen(QPen(QColor(tint),2));p.drawLine(160,301,204,302)
    elif kind == 'owl':
        for side in (-1,1):
            polygon(p, [(200+side*18,263),(200+side*146,203),(200+side*122,300),
                        (200+side*57,338)], shade,tint,3)
            for i in range(4):
                p.drawLine(QPointF(200+side*(55+i*15),274-i*7),QPointF(200+side*(53+i*17),310-i*2))
        p.setBrush(QColor(shade));p.setPen(QPen(QColor(tint),3));p.drawEllipse(QRectF(143,231,114,137))
        polygon(p, [(150,253),(142,184),(189,204),(217,204),(264,181),(254,253),(204,283)],tint,pale,3)
        for x in (177,229):
            p.setBrush(QColor('#2D2454'));p.drawEllipse(QPointF(x,237),20,24)
            p.setBrush(QColor('#FECF4D'));p.setPen(Qt.PenStyle.NoPen);p.drawEllipse(QPointF(x,237),7,13)
            p.setBrush(QColor('#FEFCFA'));p.drawEllipse(QPointF(x-2,232),2.5,3.5)
        polygon(p, [(196,255),(212,255),(204,270)], '#FECF4D')
        for y in (294,316,338):
            polygon(p, [(185,y),(204,y+13),(224,y),(204,y+4)], tint)
        p.setPen(QPen(QColor(tint),2));p.setBrush(Qt.BrushStyle.NoBrush);p.drawEllipse(QPointF(202,167),48,12)
    else:
        facets=[([(201,153),(147,236),(202,332)],'#FFF0AC'),
                ([(201,153),(258,235),(202,332)],'#C89232'),
                ([(147,236),(202,217),(258,235),(202,332)],'#FECF4D'),
                ([(201,153),(202,217),(147,236)],'#FEFCFA')]
        for points,fill in facets:polygon(p,points,fill,tint,2)
        p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor(tint),2))
        p.drawEllipse(QRectF(93,324,216,42));p.drawEllipse(QRectF(118,336,166,24))
        for i in range(8):
            angle=i*math.pi/4
            x,y=201+121*math.cos(angle),245+121*math.sin(angle)
            polygon(p,[(x,y-5),(x+4,y),(x,y+5),(x-4,y)],tint)


def render_card(index, width=480):
    """Rasterize once; interaction only transforms this locally cached image."""
    card=CARDS[index]
    image=QImage(width,round(width*1.4),QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(width/400,width/400)
    outline=QPainterPath();outline.addRoundedRect(QRectF(2,2,396,556),20,20)
    p.setClipPath(outline)
    backdrop=QLinearGradient(0,0,400,560)
    backdrop.setColorAt(0,QColor(card['dark']));backdrop.setColorAt(.58,QColor('#07142F'));backdrop.setColorAt(1,QColor(card['dark']))
    p.fillRect(QRectF(0,0,400,560),backdrop)
    glow=QRadialGradient(204,235,223);c=QColor(card['color']);c.setAlpha(105)
    glow.setColorAt(0,c);glow.setColorAt(1,QColor(0,0,0,0));p.fillRect(QRectF(0,0,400,560),glow)
    rng=random.Random(171+index)
    p.setPen(Qt.PenStyle.NoPen)
    for _ in range(95):
        x,y=rng.uniform(20,380),rng.uniform(70,440)
        c=QColor(card['color']);c.setAlpha(rng.randint(30,160));p.setBrush(c)
        r=rng.uniform(.6,2.2);p.drawEllipse(QPointF(x,y),r,r)
    # An orbital halo and distant layered mountains add depth behind the creature.
    p.setBrush(Qt.BrushStyle.NoBrush);c=QColor(card['color']);c.setAlpha(60)
    p.setPen(QPen(c,1.2));p.drawEllipse(QPointF(201,245),143,143);p.drawArc(QRectF(48,92,306,306),15*16,245*16)
    for layer in range(3):
        points=[(0,440)] + [(i*50,390+layer*15+rng.randint(-45,20)) for i in range(9)] + [(400,510),(0,510)]
        c=QColor(card['dark']).darker(110+layer*30);polygon(p,points,c.name())
    creature(p,card)
    # Bottom fade keeps the title and lore legible without an opaque enterprise-style box.
    fade=QLinearGradient(0,365,0,560);fade.setColorAt(0,QColor(7,20,47,0));fade.setColorAt(.48,QColor(7,20,47,240));fade.setColorAt(1,QColor('#07142F'))
    p.fillRect(QRectF(0,360,400,200),fade)
    p.setPen(QColor(card['color']));p.setFont(QFont('Segoe UI',10,QFont.Weight.DemiBold))
    p.drawText(QRectF(24,21,350,24),Qt.AlignmentFlag.AlignLeft,'ORIGINES  /  '+card['role'])
    p.setPen(QColor('#FEFCFA'));p.setFont(QFont('Segoe UI',25,QFont.Weight.Bold))
    p.drawText(QRectF(24,429,350,45),Qt.AlignmentFlag.AlignLeft,card['name'])
    p.setFont(QFont('Segoe UI',11));p.setPen(QColor('#C3D8F4'))
    p.drawText(QRectF(24,480,350,24),Qt.AlignmentFlag.AlignLeft,card['title'])
    p.setPen(QPen(QColor(card['color']),1));p.drawLine(24,518,376,518)
    p.setFont(QFont('Segoe UI',8));p.drawText(QRectF(24,531,350,18),Qt.AlignmentFlag.AlignLeft,f'ILLUSTRATION ORIGINALE  /  FICTIF                         {index+1:02d} / 06')
    p.setClipping(False);p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor(card['color']),2.5));p.drawRoundedRect(QRectF(3,3,394,554),19,19)
    p.setPen(QPen(QColor(255,255,255,65),1));p.drawRoundedRect(QRectF(9,9,382,542),15,15)
    p.end()
    return image
