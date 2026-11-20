"""The capture script refuses a picture that would show this PC's profile folder or account name (D-320).

Settings › Data once showed a path inside the Windows profile, hence the account name, in a published capture. The
script now runs in a neutral folder with a neutral environment, and reads every visible widget's text before each
capture. Only invented names are used here; the Qt part runs in a process of its own (offscreen).
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import qa_premium_look as look  # noqa: E402

PROFILE = 'C:\\Users\\InventedOwner'
TERMS = [PROFILE, 'InventedOwner']


def test_the_forbidden_terms_are_the_profile_the_account_and_the_repository():
    terms = look.forbidden_terms({'USERPROFILE': PROFILE, 'USERNAME': 'InventedOwner'})
    assert PROFILE in terms and 'InventedOwner' in terms and str(look.ROOT) in terms
    assert look.forbidden_terms({'USERPROFILE': '', 'USERNAME': 'abc'}) == [str(look.ROOT)]  # too short: ignored


def test_a_path_or_name_is_found_whatever_the_case_or_the_slashes():
    texts = [('field', 'C:/users/inventedowner/AppData/Local/Temp/pmq/1/data'), ('label', 'Bonjour INVENTEDOWNER'),
             ('clean', 'C:\\PokeMind-demo\\1234\\data\\local\\qa-premium-look')]
    hits = look.personal_hits(texts, TERMS)
    assert {where for where, _ in hits} == {'field', 'label'}
    assert all(isinstance(index, int) for _, index in hits)  # the matched text itself is never returned


def test_the_neutral_environment_stays_inside_the_copy(local_tmp, monkeypatch):
    for name in ('HOME', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMP', 'POKEMIND_DATA_ROOT'):
        monkeypatch.setenv(name, 'unset')
    root = look.neutral_environment(local_tmp)
    for name in ('HOME', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMP', 'POKEMIND_DATA_ROOT'):
        assert Path(os.environ[name]).is_relative_to(local_tmp) and Path(os.environ[name]).is_dir()
    assert Path(os.environ['POKEMIND_DATA_ROOT']) == root


def check_widgets():
    """Run in a process of its own: leaking widgets are refused, clean or hidden ones are not."""
    from PySide6.QtWidgets import (QApplication, QComboBox, QLabel, QLineEdit, QListWidget, QStatusBar,
                                   QVBoxLayout, QWidget)
    application = QApplication.instance() or QApplication([])
    window = QWidget()
    layout = QVBoxLayout(window)
    clean = QLineEdit('C:\\PokeMind-demo\\1234\\data\\local\\qa-premium-look')
    hidden = QLabel(PROFILE + '\\secret')
    layout.addWidget(clean)
    layout.addWidget(hidden)
    window.show()
    hidden.hide()
    application.processEvents()
    look.refuse_personal([window], TERMS, 'clean')  # nothing visible leaks: no refusal

    leaks = {'field': lambda: QLineEdit(PROFILE + '\\AppData\\Local\\Temp\\pmq\\1'),
             'tooltip': lambda: _with_tooltip(QLabel('Dossier'), 'Dans ' + PROFILE),
             'combo': lambda: _combo(QComboBox()),
             'list': lambda: _list(QListWidget()),
             'status': lambda: _status(QStatusBar()),
             'placeholder': lambda: _placeholder(QLineEdit())}
    for name, make in leaks.items():
        widget = make()
        layout.addWidget(widget)
        widget.show()
        application.processEvents()
        try:
            look.refuse_personal([window], TERMS, name)
        except SystemExit as refusal:
            assert 'InventedOwner' not in str(refusal) and PROFILE not in str(refusal)  # the refusal names no path
        else:
            raise AssertionError('not refused: ' + name)
        widget.hide()
        application.processEvents()
        look.refuse_personal([window], TERMS, name + ' hidden')
    print('GUARD-OK')


def _with_tooltip(widget, text):
    widget.setToolTip(text)
    return widget


def _combo(widget):
    widget.addItems(['Thème sombre', 'C:/Users/InventedOwner/Documents'])
    return widget


def _list(widget):
    widget.addItems(['Vue d’ensemble', 'Bonjour inventedowner'])
    return widget


def _status(widget):
    widget.showMessage('Rapport écrit dans ' + PROFILE + '\\rapport.json')
    return widget


def _placeholder(widget):
    widget.setPlaceholderText(PROFILE)
    return widget


def test_the_guard_refuses_a_capture_that_shows_a_profile_path_or_the_account_name(local_tmp):
    pytest.importorskip('PySide6')
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen', LOCALAPPDATA=str(local_tmp), POKEMIND_TEST_OFFLINE='1',
               PYTHONPATH=os.pathsep.join([str(HERE), str(SCRIPTS), str(HERE.parent / 'src')]))
    done = subprocess.run([sys.executable, '-c', 'import test_capture_guard as t; t.check_widgets()'], env=env,
                          cwd=local_tmp, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
    assert done.returncode == 0 and 'GUARD-OK' in done.stdout, (done.stdout + done.stderr)[-3000:]
