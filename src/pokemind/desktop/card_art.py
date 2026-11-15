"""Local presentation effects on artwork already authorized by ImageCache."""
from pokemind.desktop.i18n import T, J, display
from PySide6.QtCore import Qt, Property, QPropertyAnimation, QEasingCurve, QRectF
from PySide6.QtGui import QPainter, QPainterPath, QLinearGradient, QColor, QPalette
from PySide6.QtWidgets import QPushButton, QWidget, QStyleOptionButton, QStylePainter, QStyle
from pokemind.desktop.i18n import QPushButton, QWidget
from pokemind.desktop.theme import BRAND


class CardArt(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setObjectName('cardArt')
        self.setMouseTracking(True)
        self.motion_enabled, self._hover = True, 0.0
        self.tilt_x = self.tilt_y = 0.0
        self.animation = QPropertyAnimation(self, b'hover', self)
        self.animation.setDuration(180)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def set_hover(self, value):
        self._hover = value
        self.update()

    hover = Property(float, lambda self: self._hover, set_hover)

    def set_motion_enabled(self, enabled):
        self.motion_enabled = enabled
        if not enabled:
            self.animation.stop()
            self.tilt_x = self.tilt_y = 0.0
            self.set_hover(0.0)

    def animate(self, value):
        if self.motion_enabled and self.isVisible():
            self.animation.stop()
            self.animation.setStartValue(self._hover)
            self.animation.setEndValue(value)
            self.animation.start()

    def enterEvent(self, event):
        self.animate(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animate(0.0)
        super().leaveEvent(event)

    def keyPressEvent(self, event):
        if self.property('galleryArt') and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.click()
            event.accept()
        else:
            super().keyPressEvent(event)

    def mouseMoveEvent(self, event):
        if self.motion_enabled:
            self.tilt_x = max(-1, min(1, 2 * event.position().x() / max(1, self.width()) - 1))
            self.tilt_y = max(-1, min(1, 2 * event.position().y() / max(1, self.height()) - 1))
            self.update()
        super().mouseMoveEvent(event)

    def hideEvent(self, event):
        self.animation.stop()
        self.tilt_x = self.tilt_y = 0.0
        self.set_hover(0.0)
        super().hideEvent(event)

    def paintEvent(self, event):
        if self.icon().isNull():
            if self.property('galleryArt'):
                option = QStyleOptionButton()
                self.initStyleOption(option)
                option.text = ''
                p = QStylePainter(self)
                p.drawControl(QStyle.ControlElement.CE_PushButton, option)
                self.style().drawItemText(p, self.rect().adjusted(12, 12, -12, -12),
                    int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap), self.palette(),
                    self.isEnabled(), self.text(), QPalette.ColorRole.ButtonText)
                p.end()
            else:
                super().paintEvent(event)
            return
        option = QStyleOptionButton()
        self.initStyleOption(option)
        option.icon = type(option.icon)()
        option.text = ''
        p = QStylePainter(self)
        p.drawControl(QStyle.ControlElement.CE_PushButton, option)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        picture = self.icon().pixmap(440, 620)
        gallery = bool(self.property('galleryArt'))
        bounds = QRectF(self.rect()).adjusted(7, 10, -7, -6) if gallery else QRectF(self.rect()).adjusted(10, 10, -10, -10)
        size = picture.size().scaled(bounds.size().toSize(), Qt.AspectRatioMode.KeepAspectRatio)
        p.translate(bounds.center())
        if gallery:
            # Lift and zoom within the reserved inset, keeping every image edge
            # inside the button. The layout and neighbouring tiles never move.
            p.translate(0, -2 * self._hover)
            p.scale(1 + .018 * self._hover, 1 + .018 * self._hover)
        else:
            p.shear(self.tilt_x * self._hover * .025, self.tilt_y * self._hover * .018)
            p.scale(1 + .025 * self._hover, 1 + .025 * self._hover)
        target = QRectF(-size.width()/2, -size.height()/2, size.width(), size.height())
        path = QPainterPath()
        path.addRoundedRect(target, 8, 8)
        if not gallery:
            p.setClipPath(path)
        p.drawPixmap(target, picture, QRectF(picture.rect()))
        if self._hover:
            position = self.tilt_x * target.width() * .35
            shine = QLinearGradient(position - target.width(), target.top(), position + target.width(), target.bottom())
            stops = ((0, QColor(BRAND['bleu_lumineux'])), (.5, QColor(BRAND['blanc_nacre'])),
                     (1, QColor(BRAND['gold']))) if gallery else (
                         (0, QColor(120,180,255,0)), (.35,QColor(100,180,255,35)),
                         (.5,QColor(255,255,255,85)), (.65,QColor(255,120,210,40)), (1,QColor(255,220,100,0)))
            for stop, color in stops:
                if gallery:
                    color.setAlpha(24 if stop == .5 else 0)
                color.setAlpha(round(color.alpha() * self._hover))
                shine.setColorAt(stop, color)
            p.fillPath(path, shine)
        p.end()


class ZoomImage(QWidget):
    def __init__(self, picture, *, motion=True):
        super().__init__()
        self.picture, self._reveal, self.motion_enabled = picture, 1.0, motion
        self.setMinimumSize(240, 320)
        self.animation = QPropertyAnimation(self, b'reveal', self)
        self.animation.setDuration(220)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def set_reveal(self, value):
        self._reveal = value
        self.update()

    reveal = Property(float, lambda self: self._reveal, set_reveal)

    def showEvent(self, event):
        super().showEvent(event)
        if self.motion_enabled:
            self.animation.setStartValue(0.0)
            self.animation.setEndValue(1.0)
            self.animation.start()

    def hideEvent(self, event):
        self.animation.stop()
        super().hideEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        available = self.size() * (.93 + .07 * self._reveal)
        size = self.picture.size().scaled(available, Qt.AspectRatioMode.KeepAspectRatio)
        target = QRectF((self.width()-size.width())/2, (self.height()-size.height())/2, size.width(), size.height())
        p.drawPixmap(target, self.picture, QRectF(self.picture.rect()))
        p.end()
