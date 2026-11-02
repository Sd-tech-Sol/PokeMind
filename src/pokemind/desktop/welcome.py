"""First-run assistant: language, coach engine and battle-log habits, in four short steps."""
from __future__ import annotations

import shutil

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QHBoxLayout, QStackedWidget, QVBoxLayout, QButtonGroup, QRadioButton

from pokemind.desktop.i18n import QCheckBox, QComboBox, QDialog, QFrame, QLabel, QPushButton, QWidget, T, set_language, retranslate
from pokemind.desktop.theme import logo_pixmap, setting_icon

ENGINES = (('codex', 'Codex CLI', 'codex', T('Ton compte OpenAI, en ligne')),
           ('claude', 'Claude Code', 'claude', T('Ton compte Anthropic, en ligne')),
           ('ollama', 'Ollama', 'ollama', T('Un modèle local, rien ne quitte ton PC')))


def installed(command):
    return shutil.which(command) is not None


class WelcomeWizard(QDialog):
    """Returns the chosen preferences with `choices()` after `exec()` is accepted."""

    def __init__(self, preferences, parent=None, detect=installed, catalog_missing=False):
        super().__init__(parent)
        self.setObjectName('welcome')
        self.setWindowTitle(T('Bienvenue dans PokeMind'))
        self.setMinimumSize(QSize(620, 520))
        self.preferences = dict(preferences)
        self.catalog_missing = catalog_missing
        outer = QVBoxLayout(self)
        outer.setContentsMargins(26, 22, 26, 20)
        self.steps = QStackedWidget()
        outer.addWidget(self.steps, 1)
        self.dots = QLabel()
        self.dots.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dots.setObjectName('smallCaption')
        outer.addWidget(self.dots)
        buttons = QHBoxLayout()
        self.back = QPushButton(T('Retour'))
        self.back.clicked.connect(lambda: self.go(-1))
        self.next = QPushButton(T('Suivant'))
        self.next.setObjectName('primary')
        self.next.setDefault(True)
        self.next.clicked.connect(lambda: self.go(1))
        buttons.addWidget(self.back)
        buttons.addStretch()
        buttons.addWidget(self.next)
        outer.addLayout(buttons)

        # 1. Welcome and language
        page, column = self.page(T('Bienvenue dans PokeMind'),
                                 T('Ton compagnon Pokémon TCG Live : tes combats, tes decks et tes cartes restent sur ton PC.'))
        logo = QLabel()
        logo.setPixmap(logo_pixmap(120))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        column.insertWidget(0, logo)
        column.addWidget(self.caption(T('Langue')))
        self.language = QComboBox()
        self.language.addItem('English', 'en')
        self.language.addItem('Français (Québec)', 'fr')
        self.language.setCurrentIndex(1 if self.preferences.get('language') == 'fr' else 0)
        self.language.currentIndexChanged.connect(self.change_language)
        column.addWidget(self.language)
        column.addStretch()

        # 2. Coach engine
        page, column = self.page(T('Ton coach'), T('PokeMind parle avec un moteur que tu as déjà. Tu pourras changer plus tard.'))
        self.engines = QButtonGroup(self)
        self.engine_buttons = {}
        for key, name, command, hint in ENGINES:
            found = detect(command)
            row = QFrame()
            row.setObjectName('settingRow')
            line = QHBoxLayout(row)
            icon = QLabel()
            icon.setPixmap(setting_icon('coach' if key != 'ollama' else 'shield').pixmap(QSize(32, 32)))
            line.addWidget(icon)
            button = QRadioButton(name)
            button.setObjectName('engineChoice')
            self.engines.addButton(button)
            self.engine_buttons[key] = button
            words = QVBoxLayout()
            words.addWidget(button)
            note = QLabel(hint + ' · ' + (T('installé') if found else T('non trouvé sur ce PC')))
            note.setObjectName('settingHint')
            words.addWidget(note)
            line.addLayout(words, 1)
            column.addWidget(row)
        chosen = self.preferences.get('provider', 'codex')
        if not detect(dict((k, c) for k, _, c, _ in ENGINES)[chosen]):
            chosen = next((k for k, _, c, _ in ENGINES if detect(c)), chosen)
        self.engine_buttons[chosen].setChecked(True)
        self.cloud = QCheckBox(T('J’autorise l’envoi de mes questions à Codex / Claude (cloud)'))
        self.cloud.setChecked(bool(self.preferences.get('cloud_consent')))
        column.addWidget(self.cloud)
        cloud_note = QLabel(T('Les journaux bruts, identités et chemins ne sont jamais envoyés automatiquement.'))
        cloud_note.setObjectName('settingHint')
        cloud_note.setWordWrap(True)
        column.addWidget(cloud_note)
        column.addStretch()

        # 3. Battles
        page, column = self.page(T('Tes combats'), T('Colle un journal TCG Live dans le chat, ou dépose un fichier .txt / .log.'))
        self.watch = QCheckBox(T('Surveiller les nouveaux journaux pendant que PokeMind est ouvert'))
        self.watch.setChecked(bool(self.preferences.get('watch_logs')))
        self.refresh = QCheckBox(T('Actualiser mes combats au démarrage'))
        self.refresh.setChecked(bool(self.preferences.get('startup_refresh')))
        self.images = QCheckBox(T('Afficher les illustrations publiques TCGdex'))
        self.images.setChecked(bool(self.preferences.get('card_images', True)))
        self.catalog = QCheckBox(T('Télécharger le catalogue des cartes FR/EN (environ 25 Mo, TCGdex)'))
        self.catalog.setChecked(True)
        self.catalog.setVisible(catalog_missing)
        for widget in (self.watch, self.refresh, self.images, self.catalog):
            column.addWidget(widget)
        fair = QLabel(T('Pour l’entraînement et la révision après la partie : pas pendant un tournoi officiel.'))
        fair.setObjectName('settingHint')
        fair.setWordWrap(True)
        column.addWidget(fair)
        column.addStretch()

        # 4. Ready
        page, column = self.page(T('Tout est prêt'), T('Tu peux tout changer dans Réglages.'))
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        column.addWidget(self.summary)
        column.addStretch()
        self.show_step(0)

    def page(self, title, text):
        widget = QWidget()
        column = QVBoxLayout(widget)
        column.setSpacing(10)
        heading = QLabel(title)
        heading.setObjectName('title')
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        column.addWidget(heading)
        intro = QLabel(text)
        intro.setObjectName('muted')
        intro.setWordWrap(True)
        intro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        column.addWidget(intro)
        self.steps.addWidget(widget)
        return widget, column

    @staticmethod
    def caption(text):
        label = QLabel(text)
        label.setObjectName('settingTitle')
        return label

    def change_language(self):
        set_language(self.language.currentData())
        retranslate(self)
        self.show_step(self.steps.currentIndex())

    def engine(self):
        return next(key for key, button in self.engine_buttons.items() if button.isChecked())

    def show_step(self, index):
        self.steps.setCurrentIndex(index)
        last = index == self.steps.count() - 1
        self.back.setEnabled(index > 0)
        self.next.setText(T('Commencer') if last else T('Suivant'))
        self.dots.setText('   '.join('●' if i == index else '○' for i in range(self.steps.count())))
        if last:
            names = dict((k, n) for k, n, _, _ in ENGINES)
            yes, no = T('oui'), T('non')
            self.summary.setText(T('Coach : ') + names[self.engine()] + '\n'
                                 + T('Envoi au cloud : ') + (yes if self.cloud.isChecked() else no) + '\n'
                                 + T('Surveiller les journaux : ') + (yes if self.watch.isChecked() else no) + '\n'
                                 + T('Illustrations TCGdex : ') + (yes if self.images.isChecked() else no)
                                 + ('\n' + T('Catalogue des cartes : ') + (T('téléchargé à l’ouverture') if self.wants_catalog() else no)
                                    if self.catalog_missing else ''))

    def go(self, step):
        index = self.steps.currentIndex() + step
        if index >= self.steps.count():
            self.accept()
            return
        self.show_step(max(0, index))

    def wants_catalog(self):
        return self.catalog_missing and self.catalog.isChecked()

    def choices(self):
        return {'language': self.language.currentData(), 'provider': self.engine(),
                'cloud_consent': self.cloud.isChecked(), 'watch_logs': self.watch.isChecked(),
                'startup_refresh': self.refresh.isChecked(), 'card_images': self.images.isChecked()}
