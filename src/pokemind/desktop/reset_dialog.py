"""The reset window: the owner ticks the kinds of data to erase, or everything (owner, 2026-11-03)."""
from __future__ import annotations

from PySide6 import QtWidgets as W
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout

from pokemind.data_reset import CATEGORIES
from pokemind.desktop.i18n import QCheckBox, QDialog, QFrame, QLabel, QPushButton, T

LABELS = {
    'games': T('Parties et statistiques'),
    'decks': T('Mes decks'),
    'chats': T('Discussions'),
    'knowledge': T('Connaissances'),
    'public': T('Catalogue et méta publics'),
    'preferences': T('Préférences'),
    'technical': T('Fichiers techniques'),
}
HINTS = {
    'games': T('Journaux de parties importés, nombre de parties, statistiques et apprentissage tiré des parties.'),
    'decks': T('Decks enregistrés par le coach et listes exportées.'),
    'chats': T('Conversations avec le coach.'),
    'knowledge': T('Mémoire web, recherches web gardées et ancienne base locale du cerveau (documents, observations).'),
    'public': T('Catalogue de cartes, méta publique et images; ils se retéléchargent.'),
    'preferences': T('Réglages, moteur choisi et consentements; l’assistant de bienvenue reviendra.'),
    'technical': T('Journal de diagnostic et autres fichiers techniques.'),
}


class ResetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(T('Réinitialiser PokeMind'))
        self.setModal(True)
        self.setMinimumWidth(560)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(6)
        intro = QLabel(T('Coche ce que tu veux effacer. Ce qui n’est pas coché ne bouge pas.'))
        intro.setObjectName('settingTitle')
        intro.setWordWrap(True)
        layout.addWidget(intro)
        self.everything = QCheckBox(T('Tout : comme à la toute première ouverture'))
        self.everything.clicked.connect(self.check_all)
        layout.addWidget(self.everything)
        line = QFrame()
        line.setFrameShape(W.QFrame.Shape.HLine)
        layout.addWidget(line)
        self.boxes = {}
        for key in CATEGORIES:
            box = QCheckBox(LABELS[key])
            box.toggled.connect(self.refresh)
            hint = QLabel(HINTS[key])
            hint.setObjectName('settingHint')
            hint.setWordWrap(True)
            hint.setContentsMargins(26, 0, 0, 4)
            layout.addWidget(box)
            layout.addWidget(hint)
            self.boxes[key] = box
        line = QFrame()
        line.setFrameShape(W.QFrame.Shape.HLine)
        layout.addWidget(line)
        self.keep = QCheckBox(T('Garder une copie de ce qui est retiré (recommandé)'))
        self.keep.setChecked(True)
        layout.addWidget(self.keep)
        note = QLabel(T('Ne sont pas touchés : tes fichiers ailleurs sur ce PC, le dossier de travail du terminal et '
                        'les historiques gardés par Codex ou Claude dans leurs propres dossiers.') + '\n'
                      + T('PokeMind va se fermer puis se rouvrir.'))
        note.setObjectName('settingHint')
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.confirm = QPushButton(T('Réinitialiser'))
        self.confirm.setAutoDefault(False)
        self.confirm.clicked.connect(self.accept)
        self.cancel = QPushButton(T('Annuler'))
        self.cancel.setDefault(True)
        self.cancel.clicked.connect(self.reject)
        buttons.addWidget(self.confirm)
        buttons.addWidget(self.cancel)
        layout.addLayout(buttons)
        self.refresh()

    def showEvent(self, event):
        # Wrapped hints need their height for the actual width, or the last lines and the buttons are cut.
        width = max(self.width(), 560)
        self.resize(width, max(self.layout().heightForWidth(width), self.sizeHint().height()))
        super().showEvent(event)

    def check_all(self, checked):
        for box in self.boxes.values():
            box.setChecked(checked)

    def refresh(self, *_):
        self.everything.setChecked(all(box.isChecked() for box in self.boxes.values()))
        self.confirm.setEnabled(bool(self.choices()))

    def choices(self):
        return [key for key in CATEGORIES if self.boxes[key].isChecked()]
