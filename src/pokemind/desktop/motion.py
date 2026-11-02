"""Short native UI animations, with no idle loop or persistent screenshots."""
from __future__ import annotations
from pokemind.desktop.i18n import T, J, display

import math
from PySide6.QtCore import (QObject, QEvent, Qt, Property, QPropertyAnimation,
                            QEasingCurve, QPointF, QRectF)
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap, QLinearGradient
from PySide6.QtWidgets import QApplication, QFrame, QPushButton, QStackedWidget, QWidget
from pokemind.desktop.theme import logo_pixmap
from pokemind.desktop.i18n import QFrame, QPushButton, QWidget


class PageTransition(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('motionOverlay')
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.before, self.after = QPixmap(), QPixmap()
        self.direction, self._progress = 1, 1.0
        self.animation = QPropertyAnimation(self, b'progress', self)
        self.animation.setDuration(230)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.finished.connect(self.clear)
        self.hide()

    def set_progress(self, value):
        self._progress = value
        self.update()

    progress = Property(float, lambda self: self._progress, set_progress)

    def start(self, before, after, direction):
        self.before, self.after, self.direction = before, after, direction
        self.setGeometry(self.parentWidget().rect())
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.show()
        self.raise_()
        self.animation.start()

    def clear(self):
        self.animation.stop()
        self.hide()
        self.before, self.after = QPixmap(), QPixmap()

    def paintEvent(self, event):
        p = QPainter(self)
        background = self.parentWidget().palette().window().color()
        background.setAlpha(255)
        p.fillRect(self.rect(), background)
        value, distance = self._progress, 24 * self.direction
        p.setOpacity(max(0.0, 1 - value / 0.45))
        p.drawPixmap(QPointF(-distance * value, 0), self.before)
        p.setOpacity(max(0.0, (value - 0.3) / 0.7))
        p.drawPixmap(QPointF(distance * (1 - value), 0), self.after)
        p.end()


class AnimatedStack(QStackedWidget):
    """Switch the real page immediately; a brief overlay animates presentation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.motion_enabled = True
        self.transition = PageTransition(self)

    def setCurrentIndex(self, index):
        if index < 0 or index >= self.count() or index == self.currentIndex():
            return
        old = self.currentIndex()
        animate = self.motion_enabled and self.isVisible() and old >= 0
        # A second navigation starts at the last frame the user actually saw.
        before = (self.transition.grab() if self.transition.isVisible()
                  else self.currentWidget().grab()) if animate else None
        self.transition.clear()
        super().setCurrentIndex(index)
        if animate:
            self.transition.start(before, self.currentWidget().grab(), 1 if index > old else -1)

    def set_motion_enabled(self, enabled):
        self.motion_enabled = enabled
        if not enabled:
            self.transition.clear()

    def resizeEvent(self, event):
        self.transition.clear()
        super().resizeEvent(event)

    def hideEvent(self, event):
        self.transition.clear()
        super().hideEvent(event)


class ControlHighlight(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('motionOverlay')
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._glow, self._ripple = 0.0, 1.0
        self.origin = QPointF()
        self.hover_animation = QPropertyAnimation(self, b'glow', self)
        self.hover_animation.setDuration(150)
        self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.click_animation = QPropertyAnimation(self, b'ripple', self)
        self.click_animation.setDuration(360)
        self.click_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.setGeometry(parent.rect())
        self.show()

    def set_glow(self, value):
        self._glow = value
        self.update()

    def set_ripple(self, value):
        self._ripple = value
        self.update()

    glow = Property(float, lambda self: self._glow, set_glow)
    ripple = Property(float, lambda self: self._ripple, set_ripple)

    def hover(self, entered):
        self.hover_animation.stop()
        self.hover_animation.setStartValue(self._glow)
        self.hover_animation.setEndValue(1.0 if entered else 0.0)
        self.hover_animation.start()

    def click(self, position):
        self.origin = position
        self.click_animation.stop()
        self.click_animation.setStartValue(0.0)
        self.click_animation.setEndValue(1.0)
        self.click_animation.start()

    def stop(self):
        self.hover_animation.stop()
        self.click_animation.stop()
        self._glow, self._ripple = 0.0, 1.0
        self.update()

    def paintEvent(self, event):
        if not self._glow and self._ripple >= 1:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(bounds, 10, 10)
        p.setClipPath(path)
        gradient = QLinearGradient(bounds.topLeft(), bounds.bottomRight())
        gradient.setColorAt(0, QColor(255, 216, 99, round(28 * self._glow)))
        gradient.setColorAt(1, QColor(239, 88, 111, round(12 * self._glow)))
        p.fillPath(path, gradient)
        p.setPen(QPen(QColor(255, 211, 94, round(190 * self._glow)), 1.4))
        p.drawPath(path)
        if self._ripple < 1:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 220, 130, round(65 * (1 - self._ripple))))
            radius = math.hypot(self.width(), self.height()) * self._ripple
            p.drawEllipse(self.origin, radius, radius)
        p.end()


class MotionEffects(QObject):
    """Decorate existing and future controls without replacing their behavior."""
    def __init__(self, window):
        super().__init__(window)
        self.window, self.enabled, self.layers = window, True, {}
        QApplication.instance().installEventFilter(self)

    def set_enabled(self, enabled):
        self.enabled = enabled
        if not enabled:
            for layer in self.layers.values():
                layer.stop()

    def stop(self):
        self.set_enabled(False)
        QApplication.instance().removeEventFilter(self)

    def eventFilter(self, watched, event):
        kind = event.type()
        if kind not in (QEvent.Type.Enter, QEvent.Type.Leave, QEvent.Type.MouseButtonPress,
                        QEvent.Type.Resize, QEvent.Type.Hide, QEvent.Type.KeyPress):
            return False
        if not (isinstance(watched, QPushButton)
                or isinstance(watched, QFrame) and watched.objectName() == 'card'):
            return False
        if not self.window.isAncestorOf(watched):
            return False
        key = id(watched)
        layer = self.layers.get(key)
        if layer is not None and kind == QEvent.Type.Resize:
            layer.setGeometry(watched.rect())
        if layer is not None and kind == QEvent.Type.Hide:
            layer.stop()
        if not self.enabled or not watched.isEnabled() or kind not in (
                QEvent.Type.Enter, QEvent.Type.Leave, QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress):
            return False
        if layer is None:
            layer = ControlHighlight(watched)
            self.layers[key] = layer
            watched.destroyed.connect(lambda obj=None, key=key: self.layers.pop(key, None))
        if kind in (QEvent.Type.Enter, QEvent.Type.Leave):
            layer.hover(kind == QEvent.Type.Enter)
        elif isinstance(watched, QPushButton):
            if kind == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                layer.click(event.position())
            elif kind == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return):
                layer.click(QPointF(watched.rect().center()))
        return False


class EmblemWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('motionOverlay')
        self.setFixedSize(106, 106)
        self.setAccessibleName(T('Emblème PokeMind décoratif'))
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.picture, self.motion_enabled, self._progress = logo_pixmap(96), True, 1.0
        self.animation = QPropertyAnimation(self, b'progress', self)
        self.animation.setDuration(850)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def set_progress(self, value):
        self._progress = value
        self.update()

    progress = Property(float, lambda self: self._progress, set_progress)

    def set_motion_enabled(self, enabled):
        self.motion_enabled = enabled
        if not enabled:
            self.animation.stop()
            self.set_progress(1.0)

    def play(self):
        if self.motion_enabled:
            self.animation.stop()
            self.animation.setStartValue(0.0)
            self.animation.setEndValue(1.0)
            self.animation.start()

    def enterEvent(self, event):
        self.play()
        super().enterEvent(event)

    def showEvent(self, event):
        self.play()
        super().showEvent(event)

    def hideEvent(self, event):
        self.animation.stop()
        self.set_progress(1.0)
        super().hideEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        value = self._progress
        p.translate(self.width() / 2, self.height() / 2 - 5 * math.sin(value * math.pi))
        p.rotate(16 * math.sin(value * 4 * math.pi) * (1 - value))
        p.drawPixmap(-48, -48, self.picture)
        p.end()
