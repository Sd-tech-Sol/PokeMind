"""Local FR/EN presentation bindings. Raw data is never looked up or rewritten."""
from __future__ import annotations

from PySide6 import QtWidgets as W
from PySide6.QtCore import QSignalBlocker, QTranslator, QLibraryInfo, QEvent, Qt
from PySide6.QtGui import QPainter as NativePainter
from pokemind.desktop.locale_text import Text, T, J, variant, display, set_current_language

_qt_translator = None
_translator_app = None


def set_language(language):
    global _qt_translator, _translator_app
    set_current_language(language)
    app = W.QApplication.instance()
    if app is not None:
        if app.property('pokemind_language') == language:
            return
        app.setProperty('pokemind_language', language)
        if _qt_translator is None or _translator_app is not app:
            _translator_app = app
            _qt_translator = QTranslator(app)
            _qt_translator.load('qtbase_fr', QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))
        if language != 'en':
            app.installTranslator(_qt_translator)
        else:
            app.removeTranslator(_qt_translator)


def retranslate(root):
    for widget in [root, *root.findChildren(W.QWidget)]:
        if hasattr(widget, '_retranslate'):
            widget._retranslate()
        widget.update()


class Bound:
    def __init__(self, *args, **kwargs):
        self._bindings = {}
        super().__init__(*(display(a) if isinstance(a, Text) else a for a in args), **kwargs)
        if args and isinstance(args[0], Text):
            setter = 'setText' if hasattr(super(), 'setText') else 'setWindowTitle'
            getattr(self, setter)(args[0])

    def _retranslate(self):
        for setter, value in self._bindings.items():
            getattr(super(), setter)(display(value))

    def changeEvent(self, event):
        if event.type() == QEvent.Type.LanguageChange:
            self._retranslate()
        super().changeEvent(event)


def bind_method(name):
    def setter(self, value):
        if isinstance(value, Text):
            self._bindings[name] = value
        else:
            self._bindings.pop(name, None)
        getattr(super(Bound, self), name)(display(value) if isinstance(value, Text) else value)
    return setter


for _setter in ('setText', 'setHtml', 'setPlainText', 'setWindowTitle', 'setPlaceholderText',
                'setToolTip', 'setAccessibleName', 'setAccessibleDescription'):
    setattr(Bound, _setter, bind_method(_setter))


class QWidget(Bound, W.QWidget): pass
class QFrame(Bound, W.QFrame): pass
class QLabel(Bound, W.QLabel): pass
class QPushButton(Bound, W.QPushButton): pass
class QCheckBox(Bound, W.QCheckBox): pass
class QLineEdit(Bound, W.QLineEdit): pass
class QTextEdit(Bound, W.QTextEdit):
    def setPlainText(self, text):
        self._bindings.pop('setPlainText', None)
        W.QTextEdit.setPlainText(self, display(text))
class QTextBrowser(Bound, W.QTextBrowser):
    def _retranslate(self):
        vertical, horizontal = self.verticalScrollBar(), self.horizontalScrollBar()
        position = vertical.value(), horizontal.value()
        super()._retranslate()
        vertical.setValue(position[0])
        horizontal.setValue(position[1])
class QMainWindow(Bound, W.QMainWindow): pass
class QDockWidget(Bound, W.QDockWidget): pass
class QDialog(Bound, W.QDialog): pass


class QStatusBar(Bound, W.QStatusBar):
    def showMessage(self, text, timeout=0):
        self._status = text
        super().showMessage(display(text), timeout)

    def _retranslate(self):
        super()._retranslate()
        if self.currentMessage() and hasattr(self, '_status'):
            super().showMessage(display(self._status))


class QComboBox(Bound, W.QComboBox):
    def __init__(self, *args, **kwargs):
        self._items = []
        super().__init__(*args, **kwargs)

    def addItem(self, *args):
        values = list(args)
        index = 0 if isinstance(values[0], str) else 1
        source = values[index]
        values[index] = display(source)
        super().addItem(*values)
        self._items.append(source)

    def addItems(self, labels):
        for label in labels:
            self.addItem(label)

    def clear(self):
        self._items.clear()
        super().clear()

    def setItemText(self, index, text):
        if 0 <= index < len(self._items):
            self._items[index] = text
        super().setItemText(index, display(text))

    def _retranslate(self):
        super()._retranslate()
        blocker = QSignalBlocker(self)
        for index, source in enumerate(self._items):
            super().setItemText(index, display(source))
        del blocker


class QTabWidget(Bound, W.QTabWidget):
    def __init__(self, *args, **kwargs):
        self._tabs = []
        super().__init__(*args, **kwargs)

    def addTab(self, *args):
        values = list(args)
        self._tabs.append(values[-1])
        values[-1] = display(values[-1])
        return super().addTab(*values)

    def _retranslate(self):
        super()._retranslate()
        for index, text in enumerate(self._tabs):
            self.setTabText(index, display(text))


class QTableWidget(Bound, W.QTableWidget):
    def setHorizontalHeaderLabels(self, labels):
        self._headers = list(labels)
        super().setHorizontalHeaderLabels([display(label) for label in labels])

    def _retranslate(self):
        super()._retranslate()
        blocker = QSignalBlocker(self)
        if hasattr(self, '_headers'):
            super().setHorizontalHeaderLabels([display(label) for label in self._headers])
        for row in range(self.rowCount()):
            for column in range(self.columnCount()):
                item = self.item(row, column)
                if isinstance(item, QTableWidgetItem):
                    item._retranslate()
        del blocker


class QTableWidgetItem(W.QTableWidgetItem):
    def setData(self, role, value):
        if role == Qt.ItemDataRole.DisplayRole:
            self._display = value
        super().setData(role, display(value) if isinstance(value, Text) else value)

    def _retranslate(self):
        if isinstance(getattr(self, '_display', None), Text):
            super().setData(Qt.ItemDataRole.DisplayRole, display(self._display))


class Painter(NativePainter):
    def drawText(self, *args):
        return super().drawText(*(display(arg) if isinstance(arg, Text) else arg for arg in args))


class QMessageBox(Bound, W.QMessageBox):
    @classmethod
    def _show(cls, parent, title, text, buttons, default, icon):
        box = cls(parent)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIcon(icon)
        box.setStandardButtons(buttons)
        box.setDefaultButton(default)
        for key, label in ((cls.StandardButton.Yes, T('Oui')), (cls.StandardButton.No, T('Non')),
                           (cls.StandardButton.Ok, 'OK'), (cls.StandardButton.Cancel, T('Annuler')),
                           (cls.StandardButton.Close, T('Fermer'))):
            button = box.button(key)
            if button:
                button.setText(display(label))
        return cls.StandardButton(box.exec())

    @classmethod
    def question(cls, parent, title, text, buttons=W.QMessageBox.StandardButton.Yes | W.QMessageBox.StandardButton.No, default=W.QMessageBox.StandardButton.No):
        return cls._show(parent,title,text,buttons,default,cls.Icon.Question)

    @classmethod
    def information(cls, parent, title, text, buttons=W.QMessageBox.StandardButton.Ok, default=W.QMessageBox.StandardButton.Ok):
        return cls._show(parent,title,text,buttons,default,cls.Icon.Information)

    @classmethod
    def warning(cls, parent, title, text, buttons=W.QMessageBox.StandardButton.Ok, default=W.QMessageBox.StandardButton.Ok):
        return cls._show(parent,title,text,buttons,default,cls.Icon.Warning)


class QFileDialog(W.QFileDialog):
    @staticmethod
    def getOpenFileNames(parent=None, caption='', directory='', filter='', *args, **kwargs):
        return W.QFileDialog.getOpenFileNames(parent,display(caption),directory,display(filter),
            options=W.QFileDialog.Option.DontUseNativeDialog)

    @staticmethod
    def getSaveFileName(parent=None, caption='', directory='', filter='', *args, **kwargs):
        return W.QFileDialog.getSaveFileName(parent,display(caption),directory,display(filter),
            options=W.QFileDialog.Option.DontUseNativeDialog)

    @staticmethod
    def getExistingDirectory(parent=None, caption='', directory='', *args, **kwargs):
        return W.QFileDialog.getExistingDirectory(parent,display(caption),directory,
            options=W.QFileDialog.Option.DontUseNativeDialog)
