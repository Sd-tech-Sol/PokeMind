from __future__ import annotations

import shutil
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest

from pokemind import synthetic_qa

SYNTHETIC_QA_ROOT = synthetic_qa.opt_in_root()


ROOT = Path(__file__).resolve().parents[1]
LOCAL_TEST_ROOT = ROOT / "data" / "local" / "test-runs"


@pytest.fixture(scope='session', autouse=True)
def isolated_app_folder(tmp_path_factory):
    """The data-location pointer lives in %LOCALAPPDATA%: never the owner's during tests."""
    import os
    previous = {name: os.environ.get(name) for name in ('LOCALAPPDATA', 'POKEMIND_DATA_ROOT')}
    os.environ['LOCALAPPDATA'] = str(tmp_path_factory.mktemp('appdata'))
    os.environ.pop('POKEMIND_DATA_ROOT', None)
    yield
    for name, value in previous.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


@pytest.fixture(scope='session', autouse=True)
def no_terminal_model():
    """Tests never read the owner's Claude Code settings (~/.claude/settings.json); one test opts in."""
    from pokemind.assistant import provider
    previous = provider.terminal_model
    provider.terminal_model = lambda: None
    yield previous
    provider.terminal_model = previous


@pytest.fixture(autouse=True)
def isolated_coach_chat():
    """The shipped default sends typed chat to Codex/Claude in the project folder (D-265).
    Older journeys exercise the isolated coach; project-folder tests opt in explicitly.
    No monkeypatch here: an autouse monkeypatch would undo a test's chdir only after
    local_tmp is removed, and Windows cannot remove the current directory."""
    from pokemind.assistant import sessions
    previous = sessions.DEFAULTS['chat_project'], sessions.DEFAULTS['language']
    # The shipped language follows Windows (English by default); journeys are written in French.
    sessions.DEFAULTS['chat_project'], sessions.DEFAULTS['language'] = False, 'fr'
    yield
    sessions.DEFAULTS['chat_project'], sessions.DEFAULTS['language'] = previous


@pytest.fixture(autouse=True)
def cold_analysis_memos():
    """Public work is reused within a process while its files are unchanged; every test starts cold."""
    from pokemind import battle_batch, competitive, counter_deck
    for memo in (competitive._SNAPSHOTS, counter_deck._MEMOS, battle_batch._CONTEXTS):
        memo.clear()
    yield


@pytest.fixture(autouse=True)
def every_game_in_one_season():
    """Whatever today's date, the season shown holds every invented game; test_seasons sets the ladders back.

    Set by hand, not with monkeypatch: an early monkeypatch would be undone after local_tmp is cleaned, while
    a test's own patches (no directory listing) still apply.
    """
    from pokemind import seasons
    real, seasons.OFFICIAL = seasons.OFFICIAL, ()
    yield
    seasons.OFFICIAL = real


@pytest.fixture(scope='session')
def qt_application():
    """One native Qt lifetime per process, including its animation driver."""
    import gc
    from PySide6.QtCore import QCoreApplication, QEvent
    from PySide6.QtWidgets import QApplication
    application = QApplication.instance() or QApplication([])
    yield application
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    gc.collect()
    application.shutdown()
    assert QApplication.instance() is None
    gc.collect()


@pytest.fixture
def local_tmp() -> Iterator[Path]:
    if SYNTHETIC_QA_ROOT is not None:
        yield synthetic_qa.current().allocate()
        return  # retain only the new allocations; never clean inherited roots
    path = (LOCAL_TEST_ROOT / uuid.uuid4().hex).resolve()
    allowed = LOCAL_TEST_ROOT.resolve()
    if not path.is_relative_to(allowed):
        raise RuntimeError("Répertoire de test hors de data/local")
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        if path.exists() and path.is_relative_to(allowed):
            shutil.rmtree(path)
