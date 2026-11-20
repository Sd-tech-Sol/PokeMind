"""Nothing runs off the side in the smallest window (owner, 2026-11-19, D-319).

At 1100 × 700, Coach docked, in French and in English, every page (advanced mode: the Terminal too) fits beside
the Coach: no sideways scroll bar, no visible control whose right edge passes the edge of its page, no button
narrower than its words and no season list too narrow for its choice. The French Overview used to scroll sideways
there (season row and tiles too wide for the room beside the Coach). Measured with the real Segoe UI: off screen,
Qt has no font unless it is given the Windows fonts, so the check runs in a process of its own that has them (as the
global style test).
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest
pytest.importorskip('PySide6')

HERE = Path(__file__).resolve().parent
WINDOWS_FONTS = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
LANGUAGES = ('fr', 'en')


@pytest.mark.skipif(not (WINDOWS_FONTS / 'seguisb.ttf').is_file(), reason='polices Windows absentes (Segoe UI)')
@pytest.mark.parametrize('scale', ('1', '1.25'))
def test_no_page_runs_off_the_side_at_1100_by_700_with_the_coach_docked(local_tmp, scale):
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QPA_FONTDIR=str(WINDOWS_FONTS), LOCALAPPDATA=str(local_tmp),
               QT_SCALE_FACTOR=scale, POKEMIND_TEST_OFFLINE='1',
               PYTHONPATH=os.pathsep.join([str(HERE), str(HERE.parent / 'src')]))
    env.pop('POKEMIND_DATA_ROOT', None)
    done = subprocess.run([sys.executable, '-c', 'import sys, test_desktop_narrow_window as t; t.check(sys.argv[1])',
                           str(local_tmp)], env=env, cwd=str(local_tmp), capture_output=True, text=True,
                          encoding='utf-8', errors='replace', timeout=300)
    assert done.returncode == 0 and 'DÉBORDEMENT : RIEN' in done.stdout, (done.stdout + done.stderr)[-4000:]


def report():
    """18 invented games on different days, three named families and an unknown one: the Overview has its full
    summary, its tiles and its season list, as an owner's would."""
    games = [('A', 'losses', 7), ('B', 'wins', 6), ('unknown', 'losses', None), ('C', 'wins', 9), ('A', 'wins', 10),
             ('unknown', 'losses', 5), ('B', 'wins', 8), ('A', 'losses', 6), ('unknown', 'wins', 11), ('B', 'losses', 5),
             ('C', 'losses', 7), ('unknown', 'losses', 6), ('A', 'wins', 9), ('B', 'wins', 8), ('unknown', 'unknown', None),
             ('A', 'losses', 5), ('unknown', 'losses', 4), ('B', 'wins', 9)]
    matches = []
    for number, (family, outcome, turn) in enumerate(games, 1):
        label = 'unknown' if family == 'unknown' else 'Famille inventée ' + family
        matches.append({'match': 'M%04d' % number, 'outcome': outcome, 'max_observed_turn': turn,
                        'opponent': {'label': label}, 'added_on': '2026-10-%02d' % (10 + number),
                        'opponent_cards': [{'name': 'Créature inventée ' + family}],
                        'evidence': [{'turn': 3, 'type': 'knockout', 'role': 'opponent', 'text': 'Créature inventée mise K.O.'}]})
    groups = []
    for family in ('unknown', 'A', 'B', 'C'):
        label = 'unknown' if family == 'unknown' else 'Famille inventée ' + family
        mine = [m for m in matches if m['opponent']['label'] == label]
        groups.append({'archetype': label, 'n': len(mine), 'matches': [m['match'] for m in mine],
                       **{key: sum(m['outcome'] == key for m in mine) for key in ('wins', 'losses', 'unknown')}})
    return {'as_of': '2026-11-16', 'model_version': 'battle-batch-v4', 'coverage': {'valid': len(matches)},
            'outcomes': {key: sum(m['outcome'] == key for m in matches) for key in ('wins', 'losses', 'unknown')},
            'groups': groups, 'matches': matches, 'persistence': {'status': 'BLOCKED_SCHEMA_NO_MIGRATION'},
            'recommendations': []}


def check(root):
    """Run in its own process (test above), with the Windows fonts."""
    import time
    from PySide6.QtCore import QPoint
    from PySide6.QtGui import QFontInfo
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QAbstractScrollArea, QApplication, QPushButton, QScrollArea
    from pokemind import seasons
    from pokemind.assistant import provider
    from pokemind.assistant.provider import ProviderAdapter
    from pokemind.desktop import window
    from pokemind.desktop.theme import IDEA_FAMILY, idea_font
    from pokemind.desktop.widgets import wanted_width
    application = QApplication.instance() or QApplication([])
    assert QFontInfo(idea_font()).family() == IDEA_FAMILY, QFontInfo(idea_font()).family()
    seasons.OFFICIAL = ()
    provider.terminal_model = lambda: None
    games = report()

    class Fake(ProviderAdapter):
        def health(self):
            return {'available': True, 'status': 'Invented provider'}

    def load(services, update=False, **kwargs):
        services.report, services.learning = games, None
        return {'report': games, 'learning': None}
    window.Services.load = load
    window.Services.deck_options = lambda services: []
    window.CodexAppServer = window.ClaudeCode = Fake
    folder = Path(root) / 'narrow'
    folder.mkdir(parents=True, exist_ok=True)
    window.Store(folder).write('preferences.json', {'cloud_consent': False, 'sharing': 'public', 'advanced_mode': True})
    ui = window.MainWindow(folder)
    ui.show()

    def settle():
        end = time.monotonic() + 10
        while time.monotonic() < end and (ui.jobs or ui.stack.transition.isVisible()):
            application.processEvents()
            QTest.qWait(10)
        for _ in range(8):
            application.processEvents()
            QTest.qWait(10)

    settle()
    ui.loaded_decks([dict(label='Deck inventé du joueur', selector='synthetic', total=60, export='', source={},
                          opponent_rebuild=False, kind=window.T('Mon deck · référence personnelle enregistrée par le coach'),
                          legality=window.T('Standard / Live inconnus'))])
    ui.open_match('M0001')
    ui.resize(1100, 700)
    settle()
    problems = []
    for language in LANGUAGES:
        ui.language.setCurrentIndex(1 if language == 'en' else 0)
        for theme in ('dark', 'light'):
            ui.theme.setCurrentIndex(1 if theme == 'light' else 0)
            for row in range(7):
                ui.navigation.setCurrentRow(row)
                settle()
                where = '%s %s page %d' % (language, theme, row)
                if not ui.chat_dock.isVisible() or ui.chat_dock.isFloating():
                    problems.append(where + ' : Coach non ancré')
                page = ui.stack.widget(row)
                if isinstance(page, QScrollArea):
                    if page.horizontalScrollBar().isVisible():
                        problems.append(where + ' : barre de défilement horizontale')
                    edge, origin = page.viewport().width(), page.viewport()
                else:
                    edge, origin = page.width(), page

                def walk(parent):
                    for child in parent.children():
                        if not hasattr(child, 'isVisible') or not child.isWidgetType() or not child.isVisible():
                            continue
                        right = child.mapTo(origin, QPoint(child.width(), 0)).x()
                        if right > edge + 1:
                            problems.append(where + ' : %s %r coupé (%d > %d)' % (
                                type(child).__name__, child.objectName() or getattr(child, 'text', lambda: '')()[:30],
                                right, edge))
                            continue
                        if isinstance(child, QAbstractScrollArea):
                            continue  # its own content scrolls inside it (tables, gallery, text)
                        walk(child)
                walk(page.widget() if isinstance(page, QScrollArea) else page)
                for button in page.findChildren(QPushButton):
                    if (button.isVisible() and button.text() and type(button) is window.QPushButton
                            and button.width() < button.sizeHint().width() - 1):
                        problems.append(where + ' : bouton coupé %r (%d < %d)' % (button.text(), button.width(),
                                                                                  button.sizeHint().width()))
                for picker in ui.season_pickers:
                    if picker.isVisible() and page.isAncestorOf(picker) and picker.width() < wanted_width(picker) - 1:
                        problems.append(where + ' : liste Saison coupée (%d < %d)' % (picker.width(), wanted_width(picker)))
    ui.close()
    ui.pool.waitForDone(5000)
    ui.image_pool.waitForDone(5000)
    print('\n'.join(problems) or 'DÉBORDEMENT : RIEN')
    sys.stdout.flush()
    os._exit(1 if problems else 0)  # no teardown: the window's threads are done, the process ends here
