"""« Ajouter mon deck » (owner, 2026-11-06, D-288): paste a TCG Live export, name it, optionally make it the main deck."""
from __future__ import annotations

from PySide6.QtWidgets import QDialogButtonBox, QPlainTextEdit, QVBoxLayout

from pokemind.desktop.i18n import QCheckBox, QDialog, QLabel, QLineEdit, T

PROBLEMS = {'DECK_NAME_REQUIRED': 'Donne un nom à ton deck.',
            'DECK_REQUIRES_EXACT_60': 'La liste doit compter exactement 60 cartes (trouvé : {total}).',
            'DECK_RULES_VIOLATED': 'La liste enfreint une règle de construction : {problems}.'}


def problem_text(result):
    """The owner-facing reason a list was refused, from Services.save_deck."""
    code = result.get('error', '')
    validation = result.get('validation') or {}
    if validation.get('status') == 'INVALID_EXPORT':  # unreadable, or not exactly 60: the parser says why
        return T('Liste illisible ou incomplète : {reason}. Colle l’export complet de TCG Live (60 cartes).').format(
            reason=str(validation.get('error', '')).rstrip('. '))
    total = validation.get('total_cards', 0)
    return T(PROBLEMS.get(code, 'Liste refusée ({code}).')).format(
        total=total, problems=', '.join(result.get('structure_problems', [])), code=code)


class DeckEntryDialog(QDialog):
    """Name + pasted list; save() asks Services.save_deck(source='owner') and keeps the dialog open on a refusal."""

    def __init__(self, services, parent=None):
        super().__init__(parent)
        self.services, self.result = services, None
        self.setWindowTitle(T('Ajouter mon deck'))
        self.setMinimumSize(520, 520)
        column = QVBoxLayout(self)
        column.addWidget(QLabel(T('Nom du deck')))
        self.name = QLineEdit()
        self.name.setPlaceholderText(T('Ex. : Dragapult ex · ma version'))
        self.name.setMaxLength(80)
        column.addWidget(self.name)
        how = QLabel(T('Dans TCG Live : Decks › ton deck › Exporter (la liste est copiée), puis colle-la ici.'))
        how.setWordWrap(True)
        how.setObjectName('settingHint')
        column.addWidget(how)
        self.export = QPlainTextEdit()
        self.export.setPlaceholderText('Pokémon: 12\n4 …\n\nTrainer: 36\n…\n\nEnergy: 12\n…')
        column.addWidget(self.export, 1)
        self.main = QCheckBox(T('C’est mon deck principal'))
        self.main.setChecked(True)
        column.addWidget(self.main)
        self.message = QLabel('')
        self.message.setWordWrap(True)
        self.message.setObjectName('warning')
        column.addWidget(self.message)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(T('Enregistrer'))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(T('Annuler'))
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        column.addWidget(buttons)

    def save(self):
        export = self.export.toPlainText().strip().replace('\r\n', '\n')
        result = self.services.save_deck(self.name.text(), export, source='owner')
        if result.get('error'):
            self.message.setText(problem_text(result))
            return
        self.result = dict(result, export=export, main=self.main.isChecked())
        self.accept()
