"""Capture every page of the real MainWindow with invented fixtures, in an isolated copy.

    python scripts/qa_premium_look.py --label avant
    python scripts/qa_premium_look.py --label apres
    python scripts/qa_premium_look.py --label avant --baseline-ref work/pm-v1-lotj-final-readiness-windows

    python scripts/qa_premium_look.py --set simplification --label avant --baseline-ref e8479cb
    python scripts/qa_premium_look.py --set simplification --label apres
    python scripts/qa_premium_look.py --set simplification --sheets

    python scripts/qa_premium_look.py --set coherence --label avant --baseline-ref 617642c
    python scripts/qa_premium_look.py --set coherence --label apres
    python scripts/qa_premium_look.py --set coherence --sheets

    python scripts/qa_premium_look.py --set style --label avant --baseline-ref 5880563
    python scripts/qa_premium_look.py --set style --label apres
    python scripts/qa_premium_look.py --set style --sheets

    python scripts/qa_premium_look.py --set global --label avant --baseline-ref 811f8b4
    python scripts/qa_premium_look.py --set global --label apres
    python scripts/qa_premium_look.py --set global --sheets

Rendered off screen (nothing appears on the desktop) with the Windows fonts. No installed application,
personal data, network or model is used: the report, the decks, the card pictures and the discussion are invented.

The isolated copy lives in a neutral folder outside the Windows profile (C:\\PokeMind-demo, or POKEMIND_DEMO_DIR),
and HOME, USERPROFILE, APPDATA, LOCALAPPDATA, TEMP, TMP and POKEMIND_DATA_ROOT point inside it: Settings › Data
used to show a path in the profile, hence the account name (D-320). Before every capture a guard reads the text of
every visible widget (fields, labels, tooltips, lists, status bar) and refuses the capture if it holds the real
profile folder, the repository path or the Windows account name.

The « simplification » set uses fixtures worded like the application's own (an unidentified opponent, the
kinds and legality the services give, a learning journal, a public ranking) and adds the empty Coach and the
Ranking tab. Its captures go to build/ (not versioned); --sheets pairs them into before/after sheets.
The « coherence » set (owner, 2026-11-19) uses the same fixtures and shows every bar and the running text: the
Overview (top and Bilan tab), the Opponents, Turns and Actions tabs, Combats with a game open and Learning, in the
dark and the light theme. The « style » set (owner, 2026-11-19, text like the Coach's idea buttons) takes the
Overview (top and Bilan tab), Combats and Learning of that set, in the dark and the light theme. The « global »
set (owner, 2026-11-19, the idea buttons' text everywhere) takes every page and tab: the Overview and its four
statistics tabs, Combats with a game open, Deck Lab and its tabs, Cards & meta, Learning, Settings and its tabs,
the Terminal, with the Active deck card, in both themes, at the usual size and in the smallest window (1100 × 700).
"""
from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import sys
import tarfile
import time
import uuid
from pathlib import Path

from local_gate import ROOT, copy_tree, remove_copy

DEMO_DIR = Path(os.environ.get('POKEMIND_DEMO_DIR') or 'C:/PokeMind-demo')
FORBIDDEN_VARIABLE = 'POKEMIND_CAPTURE_FORBIDDEN'  # set by the parent: what identifies this PC, never stored
LOOK_FILES = ('theme.py', 'widgets.py', 'window.py')
CAPTURES = 'docs/design/pokemind-brainball/captures/premium-look'
SIMPLE_CAPTURES = 'build/qa-simplification'
SHEETS = 'docs/design/pokemind-brainball/captures/simplification'
COHERENCE_CAPTURES = 'build/qa-coherence'
COHERENCE_SHEETS = 'docs/design/pokemind-brainball/captures/coherence'
STYLE_CAPTURES = 'build/qa-style'
STYLE_SHEETS = 'docs/design/pokemind-brainball/captures/style-miroir'
GLOBAL_CAPTURES = 'build/qa-global'
GLOBAL_SHEETS = 'docs/design/pokemind-brainball/captures/style-global'
SINGLE_SCALE = ('coherence', 'style', 'global')  # sets shot at 100 % only, from the coherence views
PAGES = ('vue-ensemble', 'combats', 'decklab', 'cartes-meta', 'apprentissage', 'reglages', 'terminal')
REPORT = {
    'as_of': '2026-10-25', 'model_version': 'battle-batch-v4', 'coverage': {'valid': 14},
    'outcomes': {'wins': 6, 'losses': 7, 'unknown': 1},
    'groups': [{'archetype': 'Famille inventée A', 'wins': 2, 'losses': 4, 'unknown': 0, 'n': 6},
               {'archetype': 'Famille inventée B', 'wins': 3, 'losses': 2, 'unknown': 1, 'n': 6},
               {'archetype': 'Famille inventée C', 'wins': 1, 'losses': 1, 'unknown': 0, 'n': 2}],
    'matches': [{'match': 'M0001', 'outcome': 'losses', 'opponent': {'label': 'Famille inventée A'},
                 'evidence': [{'turn': 3, 'type': 'knockout', 'text': 'Créature inventée mise K.O.'}]},
                {'match': 'M0002', 'outcome': 'wins', 'opponent': {'label': 'Famille inventée B'},
                 'evidence': [{'turn': 5, 'type': 'knockout', 'text': 'Créature adverse inventée mise K.O.'}]}],
    'persistence': {'status': 'BLOCKED_SCHEMA_NO_MIGRATION'}, 'recommendations': []}
# What a first-time owner sees: an opponent PokeMind could not name, and 18 games.
SIMPLE_REPORT = {
    'as_of': '2026-11-16', 'model_version': 'battle-batch-v4', 'coverage': {'valid': 18},
    'outcomes': {'wins': 8, 'losses': 9, 'unknown': 1},
    'groups': [{'archetype': 'unknown', 'wins': 1, 'losses': 4, 'unknown': 1, 'n': 6, 'matches': ['M0003']},
               {'archetype': 'Famille inventée A', 'wins': 2, 'losses': 3, 'unknown': 0, 'n': 5, 'matches': ['M0001']},
               {'archetype': 'Famille inventée B', 'wins': 4, 'losses': 1, 'unknown': 0, 'n': 5, 'matches': ['M0002']},
               {'archetype': 'Famille inventée C', 'wins': 1, 'losses': 1, 'unknown': 0, 'n': 2, 'matches': []}],
    'matches': [{'match': 'M0001', 'outcome': 'losses', 'opponent': {'label': 'Famille inventée A'}, 'max_observed_turn': 7,
                 'evidence': [{'turn': 3, 'type': 'knockout', 'role': 'opponent', 'text': 'Créature inventée mise K.O.'},
                              {'turn': 5, 'type': 'prize', 'role': 'opponent', 'text': 'Récompense prise (inventé).'}]},
                {'match': 'M0002', 'outcome': 'wins', 'opponent': {'label': 'Famille inventée B'}, 'max_observed_turn': 6,
                 'evidence': [{'turn': 5, 'type': 'knockout', 'role': 'self', 'text': 'Créature adverse inventée mise K.O.'}]},
                {'match': 'M0003', 'outcome': 'losses', 'opponent': {'label': 'unknown'},
                 'evidence': [{'turn': None, 'type': 'knockout', 'text': 'Créature inventée mise K.O.'}]}],
    'persistence': {'status': 'BLOCKED_SCHEMA_NO_MIGRATION'}, 'recommendations': []}
# The other 15 invented games (pipeline 023, phase 7), so that the summaries have something to tell: one a day,
# with the same totals as above. (opponent, result, last turn header seen)
_MORE_GAMES = [('C', 'wins', 9), ('A', 'wins', 10), ('unknown', 'losses', 5), ('B', 'wins', 8), ('A', 'losses', 6),
               ('unknown', 'wins', 11), ('B', 'losses', 5), ('C', 'losses', 7), ('unknown', 'losses', 6), ('A', 'wins', 9),
               ('B', 'wins', 8), ('unknown', 'unknown', None), ('A', 'losses', 5), ('unknown', 'losses', 4), ('B', 'wins', 9)]
_SEEN = {'A': ['Créature inventée A', 'Dresseur inventé B'], 'B': ['Créature inventée C', 'Créature inventée D'],
         'C': ['Créature inventée E'], 'unknown': ['Dresseur inventé F']}
for _number, (_family, _outcome, _turn) in enumerate(_MORE_GAMES, 4):
    SIMPLE_REPORT['matches'].append({'match': 'M%04d' % _number, 'outcome': _outcome, 'max_observed_turn': _turn,
        'opponent': {'label': 'unknown' if _family == 'unknown' else 'Famille inventée ' + _family}, 'evidence': []})
for _number, _match in enumerate(SIMPLE_REPORT['matches'], 1):
    _family = _match['opponent']['label'][-1] if _match['opponent']['label'] != 'unknown' else 'unknown'
    _match.update(added_on='2026-10-%02d' % (10 + _number), opponent_cards=[{'name': n} for n in _SEEN[_family]])
for _group in SIMPLE_REPORT['groups']:
    _group['matches'] = [m['match'] for m in SIMPLE_REPORT['matches'] if m['opponent']['label'] == _group['archetype']]
SIMPLE_LEARNING = {'current': [
    {'kind': 'observed_game_event', 'recorded_at': '2026-11-16T10:00:00', 'payload': {'matches': ['M%04d' % i for i in range(1, 19)]}},
    {'kind': 'derived_statistic', 'recorded_at': '2026-11-16T10:00:00', 'payload': {'groups': [
        {'archetype': 'unknown', 'wins': 1, 'losses': 4, 'n': 6}, {'archetype': 'Famille inventée A', 'wins': 2, 'losses': 3, 'n': 5},
        {'archetype': 'Famille inventée B', 'wins': 4, 'losses': 1, 'n': 5}]}},
    {'kind': 'test_plan', 'recorded_at': '2026-11-15T10:00:00', 'payload': {'recommendations': [
        {'archetype': 'Famille inventée A', 'loss_match_refs': ['M0001'],
         'plan': {'alternatives': [{'archetypes': ['Base inventée']}]}}]}}],
    'history': [{'recorded_at': '2026-11-10T09:00:00', 'revises': 'derived_statistic'}]}


def forbidden_terms(environ=os.environ):
    """What would identify this PC in a capture: profile folder, repository path, Windows account name."""
    found = {environ.get('USERPROFILE', ''), environ.get('USERNAME', ''), str(ROOT)}
    return sorted(term for term in found if len(term) >= 4)


def _plain(text):
    return str(text).replace('/', '\\').casefold()


def personal_hits(texts, terms):
    """The (where, term index) pairs whose text holds a forbidden term; the matched text is never returned."""
    wanted = [_plain(term) for term in terms if term]
    return [(where, index) for where, text in texts for index, term in enumerate(wanted) if text and term in _plain(text)]


def widget_texts(widgets):
    """(where, text) for what visible widgets show or say: text, placeholder, tooltip, items, status bar, title."""
    from PySide6.QtCore import QModelIndex
    from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QPlainTextEdit, QStatusBar, QTabBar, QTextEdit,
                                   QWidget)
    for top in widgets:
        for widget in [top] + top.findChildren(QWidget):
            if not widget.isVisible():
                continue
            where = type(widget).__name__ + ('#' + widget.objectName() if widget.objectName() else '')
            values = [widget.windowTitle(), widget.toolTip(), widget.statusTip(), widget.accessibleName(),
                      widget.accessibleDescription()]
            for name in ('text', 'placeholderText', 'currentText'):
                method = getattr(widget, name, None)
                if callable(method):
                    try:
                        values.append(method())
                    except TypeError:
                        pass
            if isinstance(widget, (QTextEdit, QPlainTextEdit)):
                values.append(widget.toPlainText())
            if isinstance(widget, QComboBox):
                values += [widget.itemText(i) for i in range(widget.count())]
            if isinstance(widget, QTabBar):
                values += [widget.tabText(i) + ' ' + widget.tabToolTip(i) for i in range(widget.count())]
            if isinstance(widget, QStatusBar):
                values.append(widget.currentMessage())
            if isinstance(widget, QAbstractItemView) and widget.model() is not None:
                model, top_level = widget.model(), QModelIndex()
                try:
                    columns = model.columnCount(top_level)
                except TypeError:  # a list model hides columnCount
                    columns = 1
                for row in range(min(model.rowCount(top_level), 500)):
                    for column in range(min(columns, 20)):
                        index = model.index(row, column)
                        values += [index.data(), index.data(3)]  # display and tooltip roles
            for value in values:
                if isinstance(value, str) and value:
                    yield where, value


def refuse_personal(widgets, terms, name):
    hits = personal_hits(widget_texts(widgets), terms)
    if hits:
        raise SystemExit('capture refused (%s): %d visible text(s) hold a path or name of this PC, in %s'
                         % (name, len(hits), ', '.join(sorted({where for where, _ in hits}))))


def neutral_environment(base):
    """HOME, profile, AppData, temp and data root inside the copy: nothing of the Windows profile can show."""
    base = Path(base)
    folders = {'HOME': 'home', 'USERPROFILE': 'home', 'APPDATA': 'home/AppData/Roaming',
               'LOCALAPPDATA': 'home/AppData/Local', 'TEMP': 'home/AppData/Local/Temp', 'TMP': 'home/AppData/Local/Temp'}
    for variable, relative in folders.items():
        (base / relative).mkdir(parents=True, exist_ok=True)
        os.environ[variable] = str(base / relative)
    root = base / 'data/local/qa-premium-look'
    root.mkdir(parents=True, exist_ok=True)
    os.environ['POKEMIND_DATA_ROOT'] = str(root)
    return root


def child(output, scale, capture_set):
    """Runs inside the copy: the repository and data/local of the owner are never the working folder."""
    terms = [term for term in os.environ.get(FORBIDDEN_VARIABLE, '').split('\n') if term]
    if not terms:
        raise SystemExit('capture: no forbidden terms given, the guard cannot run')
    if personal_hits([('copy', str(Path.cwd()))], terms):
        raise SystemExit('capture: the copy is inside the Windows profile or the repository')
    root = neutral_environment(Path.cwd())
    from PySide6.QtCore import QBuffer, QIODevice, QRectF, Qt
    from PySide6.QtGui import QColor, QFont, QImage, QLinearGradient, QPainter, QPen
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    from pokemind import seasons
    from pokemind.assistant import provider, sessions
    from pokemind.assistant.provider import ProviderAdapter
    from pokemind.desktop import window
    from pokemind.desktop.i18n import T

    simple = capture_set in ('simplification',) + SINGLE_SCALE
    report, learning = (SIMPLE_REPORT, SIMPLE_LEARNING) if simple else (REPORT, None)
    provider.terminal_model = lambda: None  # never the owner's Claude Code settings
    sessions.DEFAULTS['chat_project'], sessions.DEFAULTS['language'] = False, 'fr'
    seasons.OFFICIAL = ()

    class Fake(ProviderAdapter):
        def health(self):
            return {'available': True, 'status': 'Invented provider'}

        def ask_stream(self, prompt, history, emit, tool=None):
            emit('Réponse inventée.')

    def load(services, update=False, **kwargs):
        services.report, services.learning = report, learning
        return {'report': report, 'learning': learning}

    window.Services.load = load
    window.Services.deck_options = lambda services: []
    window.CodexAppServer = window.ClaudeCode = Fake
    application = QApplication.instance() or QApplication([])

    def picture(index, category):
        """An invented card: a coloured frame and a number, no Pokémon artwork."""
        image = QImage(300, 420, QImage.Format.Format_RGB32)
        hue = {'pokemon': 8, 'trainer': 205, 'energy': 48}[category] + index * 23
        p = QPainter(image)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        fill = QLinearGradient(0, 0, 300, 420)
        fill.setColorAt(0, QColor.fromHsv(hue % 360, 150, 235))
        fill.setColorAt(1, QColor.fromHsv((hue + 40) % 360, 190, 120))
        p.fillRect(image.rect(), fill)
        p.setPen(QPen(QColor('#F4E6A6'), 12))
        p.drawRect(image.rect().adjusted(6, 6, -6, -6))
        p.fillRect(QRectF(28, 62, 244, 170), QColor(255, 255, 255, 60))
        p.setPen(QColor('#10203C'))
        p.setFont(QFont('Segoe UI', 15, QFont.Weight.Bold))
        p.drawText(QRectF(28, 22, 244, 34), Qt.AlignmentFlag.AlignVCenter, 'Synthétique ' + str(index + 1))
        p.setFont(QFont('Segoe UI', 11))
        p.drawText(QRectF(28, 250, 244, 130), Qt.TextFlag.TextWordWrap, 'Carte inventée pour la capture. Aucune illustration réelle.')
        p.end()
        data = QBuffer()
        data.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(data, 'PNG')
        return bytes(data.data())

    names = (['Créature inventée ' + letter for letter in 'ABCDEFGH'] + ['Dresseur inventé ' + letter for letter in 'ABCDEFG']
             + ['Énergie inventée ' + letter for letter in 'ABC'])
    categories = ['pokemon'] * 8 + ['trainer'] * 7 + ['energy'] * 3
    quantities = [4, 4, 3, 2, 2, 2, 2, 1, 4, 4, 4, 3, 2, 2, 1] + [8, 8, 4]
    cards = [dict(name=name, quantity=quantity, category=category, printing='SYN ' + str(index + 1).zfill(3),
                  identity='synthetic-' + str(index))
             for index, (name, category, quantity) in enumerate(zip(names, categories, quantities))]
    assert sum(quantities) == 60
    pictures = {card['identity']: picture(index, card['category']) for index, card in enumerate(cards)}
    export = '\n'.join(str(card['quantity']) + ' ' + card['name'] + ' ' + card['printing'] for card in cards)

    window.Store(root).write('preferences.json', {'cloud_consent': False, 'sharing': 'public'})
    ui = window.MainWindow(root)
    ui.services.gallery_cards = lambda value: cards
    ui.images.fetch = lambda key, *args: {'data': pictures[key], 'source_url': 'https://example.invalid/synthetic.png'}
    ui.show()

    def settle(condition=lambda: True, timeout=15):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            application.processEvents()
            QTest.qWait(20)
            time.sleep(.002)
            if condition() and not ui.jobs and not ui.stack.transition.isVisible():
                break
        else:
            raise SystemExit('capture: the window did not settle')
        QTest.qWait(350)  # entrance animations of charts and tiles
        application.processEvents()

    settle(lambda: ui.metrics[0].text() == str(report['coverage']['valid']))
    if simple:  # the words the services really give, and a public deck with a rank
        ranking = {'fraction': .508, 'n': 117, 'mode': 'BO1', 'window': {'since': '2026-10-18', 'until': '2026-11-14'},
                   'source_url': 'https://example.invalid/tournaments', 'last_success_at': '2026-11-14',
                   'refresh': {'automatic_due': False}}
        ui.loaded_decks([
            dict(label='Deck inventé du joueur', selector='synthetic', total=60, export=export, source={},
                 opponent_rebuild=False,  # an own deck of « Mes decks », as the services give it
                 kind=T('Mon deck · référence personnelle enregistrée par le coach'), legality=T('Standard / Live inconnus'),
                 public_ranking=ranking),
            dict(label='Modèle public inventé', selector='synthetic-public', total=60, export=export + '\n', source={},
                 kind=T('Référence PUBLIC'), legality=T('Standard / Live inconnus'), public_ranking={'fraction': None})])
    else:
        ui.loaded_decks([dict(label='Deck inventé · 18 références / 60 cartes', selector='synthetic', total=60,
                              export=export, kind='QA synthétique', legality='légalité inconnue', source={})])
    ui.conversation['messages'] = [
        {'role': 'user', 'content': 'Question inventée : que travailler contre la Famille inventée A ?'},
        {'role': 'assistant', 'content': 'Réponse inventée pour la capture.\n\n- Premier point inventé.\n- Second point inventé.'}]
    ui.render_chat()
    settle(lambda: len(ui.gallery.tiles) == len(cards) and all(not tile.picture.isNull() for tile in ui.gallery.tiles))
    ui.gallery.select_tile(ui.gallery.tiles[0])  # the look of a selected card is part of what is compared
    output.mkdir(parents=True, exist_ok=True)

    def checked(name):
        refuse_personal([w for w in application.topLevelWidgets() if w.isVisible()], terms, name)
        return ui.grab()

    def shoot(name, row):
        ui.navigation.setCurrentRow(row)
        settle()
        if not checked(name).save(str(output / (name + '.png'))):
            raise SystemExit('capture: ' + name + ' not written')

    def theme(name):
        ui.theme.setCurrentIndex(1 if name == 'light' else 0)
        settle()

    if capture_set == 'global':
        if hasattr(ui, 'advanced_mode'):
            ui.advanced_mode.setChecked(True)  # the Terminal page exists in advanced mode only
        scroll = ui.stack.widget(0)
        ui.open_match('M0001')  # an opponent chosen, its summary and one of its games
        settle()
        usual = ui.size()

        def save(name):
            if not checked(name).save(str(output / (name + '.png'))):
                raise SystemExit('capture: ' + name + ' not written')

        for size, suffix in ((usual, ''), (None, '-1100x700')):
            if size is None:
                ui.resize(1100, 700)
            else:
                ui.resize(size)
            settle()
            for shade in ('sombre', 'clair'):
                theme('light' if shade == 'clair' else 'dark')
                end = '-' + shade + suffix
                ui.navigation.setCurrentRow(0)
                scroll.verticalScrollBar().setValue(0)
                settle()
                save('01-vue-ensemble' + end)
                for number in range(ui.statistics.tabs.count()):
                    ui.statistics.tabs.setCurrentIndex(number)
                    scroll.verticalScrollBar().setValue(
                        ui.statistics.mapTo(scroll.widget(), ui.statistics.rect().topLeft()).y() - 12)
                    settle()
                    save('01-vue-ensemble-statistiques-%d%s' % (number + 1, end))
                ui.statistics.tabs.setCurrentIndex(0)
                scroll.verticalScrollBar().setValue(0)
                shoot('02-combats' + end, 1)
                for number in range(ui.deck_views.count()):
                    ui.deck_views.setCurrentIndex(number)
                    shoot('03-decklab-%d%s' % (number + 1, end), 2)
                ui.deck_views.setCurrentIndex(0)
                shoot('04-cartes-meta' + end, 3)
                shoot('05-apprentissage' + end, 4)
                for number, key in enumerate(ui.settings_sections):
                    ui.show_settings_section(key)
                    shoot('06-reglages-%d-%s%s' % (number + 1, key, end), 5)
                ui.show_settings_section('general')
                shoot('07-terminal' + end, 6)
        theme('dark')
        ui.resize(usual)
    elif capture_set in SINGLE_SCALE:
        tabs = ((2, 'bilan'),) if capture_set == 'style' else ((2, 'bilan'), (3, 'adversaires'), (4, 'tours'),
                                                                (5, 'actions'))
        if hasattr(ui, 'advanced_mode'):
            ui.advanced_mode.setChecked(False)
        scroll = ui.stack.widget(0)

        def overview(tab=None):
            ui.navigation.setCurrentRow(0)
            settle()
            top = 0
            if tab is not None:
                ui.statistics.tabs.setCurrentIndex(tab)
                top = ui.statistics.mapTo(scroll.widget(), ui.statistics.rect().topLeft()).y() - 12
            scroll.verticalScrollBar().setValue(top)
            settle()

        def save(name):
            if not checked(name).save(str(output / (name + '.png'))):
                raise SystemExit('capture: ' + name + ' not written')

        ui.open_match('M0001')  # an opponent chosen, its summary and one of its games
        settle()
        for shade in ('sombre', 'clair'):
            theme('light' if shade == 'clair' else 'dark')
            overview()
            save('01-vue-ensemble-' + shade)
            for number, tab in tabs:
                overview(number - 2)
                save('%02d-statistiques-%s-%s' % (number, tab, shade))
            ui.statistics.tabs.setCurrentIndex(0)
            scroll.verticalScrollBar().setValue(0)
            shoot('06-combats-' + shade, 1)
            shoot('07-apprentissage-' + shade, 4)
        theme('dark')
    elif scale == '1':
        for index, name in enumerate(PAGES):
            if index == 6 and hasattr(ui, 'advanced_mode'):
                ui.advanced_mode.setChecked(True)  # the Terminal page only exists in advanced mode
                settle()
            shoot('%02d-%s-sombre' % (index + 1, name), index)
        if simple:
            if hasattr(ui, 'advanced_mode'):
                ui.advanced_mode.setChecked(False)  # the menu a first-time owner sees
                settle()
            ui.open_match('M0003')  # a game against an opponent PokeMind could not name
            settle()
            shoot('08-combats-partie-sombre', 1)
            ui.deck_views.setCurrentIndex(3)
            shoot('09-decklab-classement-sombre', 2)
            ui.deck_views.setCurrentIndex(0)
            ui.new_conversation()
            settle()
            shoot('10-coach-vide-sombre', 0)
            ui.conversation['messages'] = [{'role': 'user', 'content': 'Question inventée.'},
                                           {'role': 'assistant', 'content': 'Réponse inventée pour la capture.'}]
            ui.render_chat()
        theme('light')
        for index in (0, 1, 2):
            shoot('%02d-%s-clair' % (index + 1, PAGES[index]), index)
        ui.resize(1100, 700)  # the smallest window
        shoot('03-decklab-etroit-clair', 2)
        theme('dark')
        shoot('03-decklab-etroit-sombre', 2)
    else:
        shoot('01-vue-ensemble-125-sombre', 0)
        shoot('03-decklab-125-sombre', 2)
    ui.close()
    ui.pool.waitForDone(5000)
    ui.image_pool.waitForDone(5000)
    application.processEvents()
    return 0


def sheets(capture_set='simplification'):
    """Pair build/…/avant and …/apres into before/after sheets, half size, side by side."""
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    os.environ.setdefault('QT_QPA_FONTDIR', str(Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'))
    from PySide6.QtCore import QRect, Qt
    from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter
    application = QGuiApplication.instance() or QGuiApplication([])
    source, sheets_dir = {'coherence': (COHERENCE_CAPTURES, COHERENCE_SHEETS),
                          'style': (STYLE_CAPTURES, STYLE_SHEETS),
                          'global': (GLOBAL_CAPTURES, GLOBAL_SHEETS)}.get(capture_set, (SIMPLE_CAPTURES, SHEETS))
    before, after, target = ROOT / source / 'avant', ROOT / source / 'apres', ROOT / sheets_dir
    target.mkdir(parents=True, exist_ok=True)
    for stale in list(target.glob('*.png')) + list(target.glob('*.jpg')):
        stale.unlink()
    written = 0
    light = capture_set == 'global'  # 76 sheets: JPEG (quality 72) keeps the repository light, the text stays readable
    for path in sorted(after.glob('*.png')):
        right, left = QImage(str(path)), QImage(str(before / path.name))
        if '-125-' in path.name:
            continue  # the same pages, larger: nothing more to read on a sheet
        width, band, gap = 1000, 40, 16
        right = right.scaledToWidth(width, Qt.TransformationMode.SmoothTransformation)
        if not left.isNull():
            left = left.scaledToWidth(width, Qt.TransformationMode.SmoothTransformation)
        height = max(right.height(), left.height())
        sheet = QImage(width * 2 + gap, height + band, QImage.Format.Format_RGB32)
        sheet.fill(QColor('#0B1220'))
        p = QPainter(sheet)
        p.setFont(QFont('Segoe UI', 13, QFont.Weight.Bold))
        for x, title, image in ((0, 'AVANT', left), (width + gap, 'APRÈS', right)):
            p.setPen(QColor('#C9D7EE'))
            p.drawText(QRect(x + 8, 0, width, band), int(Qt.AlignmentFlag.AlignVCenter),
                       title + ' · ' + path.stem if not image.isNull() else title + ' · (cette vue n’existait pas)')
            if not image.isNull():
                p.drawImage(x, band, image)
        p.end()
        name = path.with_suffix('.jpg').name if light else path.name
        if not (sheet.save(str(target / name), 'JPG', 72) if light else sheet.save(str(target / name))):
            raise SystemExit('sheet not written: ' + path.name)
        written += 1
    del application
    print('Planches :', sheets_dir, '·', written, 'images')
    return 0


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--set', default='premium-look', choices=('premium-look', 'simplification', 'coherence', 'style', 'global'),
                        dest='capture_set')
    parser.add_argument('--label', default='apres', choices=('avant', 'apres'))
    parser.add_argument('--baseline-ref', help='Take the code from this Git ref: theme.py, widgets.py and window.py '
                                               '(premium-look) or the whole src/pokemind (simplification)')
    parser.add_argument('--sheets', action='store_true', help='Only pair the simplification captures into sheets')
    parser.add_argument('--child', help=argparse.SUPPRESS)
    parser.add_argument('--scale', default='1', help=argparse.SUPPRESS)
    options = parser.parse_args()
    if options.child:
        return child(Path(options.child), options.scale, options.capture_set)
    if options.sheets:
        return sheets(options.capture_set)
    simple = options.capture_set in ('simplification',) + SINGLE_SCALE
    terms = forbidden_terms()
    target = DEMO_DIR / uuid.uuid4().hex[:8]
    if personal_hits([('copy', str(target))], terms):
        raise SystemExit('capture: the demo folder must be outside the Windows profile and the repository')
    target.mkdir(parents=True)
    output = ROOT / ({'simplification': SIMPLE_CAPTURES, 'coherence': COHERENCE_CAPTURES,
                      'style': STYLE_CAPTURES, 'global': GLOBAL_CAPTURES}.get(options.capture_set) or CAPTURES) / options.label
    status = 0
    try:
        copy_tree(target)
        if options.baseline_ref and simple:  # the whole application as it was; this script stays the current one
            archive = subprocess.run(['git', 'archive', '--format=tar', options.baseline_ref, 'src/pokemind'], cwd=ROOT,
                                     capture_output=True, check=True).stdout
            shutil.rmtree(target / 'src/pokemind')
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
                tar.extractall(target, filter='data')
        for name in LOOK_FILES if options.baseline_ref and not simple else ():
            relative = 'src/pokemind/desktop/' + name
            source = subprocess.run(['git', 'show', options.baseline_ref + ':' + relative], cwd=ROOT,
                                    capture_output=True, check=True).stdout
            (target / relative).write_bytes(source)
        output.mkdir(parents=True, exist_ok=True)
        for stale in output.glob('*.png'):
            stale.unlink()
        for scale in ('1',) if options.capture_set in SINGLE_SCALE else ('1', '1.25'):
            env = dict(os.environ, POKEMIND_TEST_OFFLINE='1', QT_QPA_PLATFORM='offscreen', QT_SCALE_FACTOR=scale,
                       QT_QPA_FONTDIR=str(Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'),
                       PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(target / 'src'))
            for name in ('POKEMIND_SYNTHETIC_QA_ROOT', 'POKEMIND_SYNTHETIC_QA_TOKEN', 'POKEMIND_DATA_ROOT'):
                env.pop(name, None)
            env[FORBIDDEN_VARIABLE] = '\n'.join(terms)
            result = subprocess.run([sys.executable, str(target / 'scripts/qa_premium_look.py'), '--child', str(output),
                                     '--scale', scale, '--set', options.capture_set], cwd=target, env=env,
                                    capture_output=True, text=True, encoding='utf-8', errors='replace')
            if result.returncode:
                print((result.stdout + result.stderr)[-6000:])
                status = result.returncode
    finally:
        remove_copy(target)
        try:
            DEMO_DIR.rmdir()  # only when empty
        except OSError:
            pass
    print('Captures :', output.relative_to(ROOT).as_posix(), '·', len(list(output.glob('*.png'))), 'images')
    return status


if __name__ == '__main__':
    raise SystemExit(main())
