"""Embedded terminal: ConPTY rendering, keys, and the page that starts Codex/Claude as-is."""
import sys
import pytest
pytest.importorskip('PySide6')
pytest.importorskip('pyte')
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication
from test_desktop_qt import app, ui, wait_until  # noqa: F401
from pokemind.desktop import terminal, window

ESC = '\x1b'
M = Qt.KeyboardModifier


def test_keys_follow_what_a_windows_terminal_sends():
    assert terminal.key_text(Qt.Key.Key_Return, M.NoModifier, '\r') == '\r'
    assert terminal.key_text(Qt.Key.Key_C, M.ControlModifier, '\x03') == '\x03'
    assert terminal.key_text(Qt.Key.Key_Left, M.ControlModifier, '') == ESC + '[1;5D'
    assert terminal.key_text(Qt.Key.Key_Up, M.NoModifier, '') == ESC + '[A'
    assert terminal.key_text(Qt.Key.Key_Backtab, M.ShiftModifier, '') == ESC + '[Z'
    # AltGr on a French keyboard is Ctrl+Alt: the character itself, not a control code.
    assert terminal.key_text(Qt.Key.Key_At, M.ControlModifier | M.AltModifier, '@') == '@'
    assert terminal.key_text(Qt.Key.Key_E, M.NoModifier, 'é') == 'é'
    assert terminal.key_text(Qt.Key.Key_B, M.AltModifier, 'b') == ESC + 'b'
    assert terminal.key_text(Qt.Key.Key_Shift, M.ShiftModifier, '') == ''


def test_conpty_output_is_drawn_without_the_keyboard_modes_pyte_misreads(app):
    view = terminal.TerminalView()
    sent = []
    view.send = sent.append
    view.screen.reply = sent.append
    view.resize(800, 300)
    # Claude Code asks for keyboard modes; pyte would read « > 4;2 m » as underline.
    view.receive(ESC + '[>4;2m' + ESC + '[>5u' + ESC + '[?u' + ESC + '[31mrouge' + ESC + '[0m é ⏺ ─┐' + ESC + '[3')
    view.receive('2mvert' + ESC + ']0;Titre inventé' + ESC + '\\' + ESC + ']11;?' + ESC + '\\')
    wait_until(app, lambda: not view.pending and not view.flush_timer.isActive())
    first = view.screen.buffer[0]
    assert view.screen.display[0].startswith('rouge é ⏺ ─┐vert')
    green = next(x for x in range(40) if first[x].data == 'v')
    assert first[0].fg == 'red' and not any(first[x].underscore for x in range(20))
    assert first[green].fg == 'green' and view.title == 'Titre inventé'
    assert sent == [ESC + ']11;rgb:1515/1a1a/2424' + ESC + '\\']  # PokeMind's dark panel, still read as dark
    assert not view.grab().isNull()


def test_selection_copy_paste_and_scrollback(app):
    view = terminal.TerminalView()
    sent = []
    view.send = sent.append
    view.resize(640, 200)
    view.feed('premiere ligne\r\n' + 'x\r\n' * 40 + 'derniere')
    view.selection = ((view.screen.lines - 1, 0), (view.screen.lines - 1, 8))
    assert view.copy() and QGuiApplication.clipboard().text() == 'derniere' and view.selection is None
    QGuiApplication.clipboard().setText('un\ndeux')
    view.paste()
    assert sent[-1] == 'un\rdeux'
    view.feed(ESC + '[?2004h')
    view.paste()
    assert sent[-1] == ESC + '[200~un\rdeux' + ESC + '[201~'
    assert view.text().startswith('premiere ligne') and view.text().endswith('derniere')


@pytest.mark.skipif(not terminal.available(), reason='ConPTY (pywinpty) is Windows-only')
def test_a_real_console_program_round_trips_through_conpty(app, tmp_path):
    script = 'import sys; sys.stdout.reconfigure(encoding="utf-8"); print(input("> ").upper()); sys.exit(3)'
    view = terminal.TerminalView([sys.executable, '-c', script], tmp_path)
    ended = []
    view.finished.connect(ended.append)
    view.resize(700, 240)
    view.show()
    try:
        wait_until(app, lambda: view.text().endswith('>'), timeout=20000)
        view.send('bonjour inventé\r')
        wait_until(app, lambda: bool(ended), timeout=20000)
        assert 'BONJOUR INVENTÉ' in view.text() and ended == [3] and 'Session terminée · code 3' in view.text()
    finally:
        view.session.close()
        view.close()


class FakeSession(QObject):
    output = Signal(str)
    ended = Signal(object)
    started = []

    def __init__(self, argv, cwd, rows, columns, env=None):
        super().__init__()
        self.argv, self.cwd, self.open = argv, cwd, True
        FakeSession.started.append(self)

    def alive(self):
        return self.open

    def finish(self):
        self.open = False

    def write(self, text):
        pass

    def resize(self, rows, columns):
        pass

    def close(self):
        self.open = False


def test_terminal_page_starts_codex_yolo_and_claude_bypass_only_after_consent(ui, app, monkeypatch):
    FakeSession.started = []
    monkeypatch.setattr(terminal, 'Session', FakeSession)
    monkeypatch.setattr(terminal, 'available', lambda: True)
    monkeypatch.setattr('pokemind.assistant.provider.executable', lambda name: 'C:/invented/' + name + '.exe')
    answers = [window.QMessageBox.StandardButton.No]
    monkeypatch.setattr(window.QMessageBox, 'question', lambda *a, **k: answers.pop(0))
    assert ui.navigation.item(6).text() == 'Terminal' and ui.stack.count() == 7
    for button in ui.terminal_buttons.values():
        button.setEnabled(True)  # disabled at start where ConPTY is absent (Linux CI)
    ui.terminal_buttons['codex'].click()
    assert FakeSession.started == [] and ui.terminal_tabs.count() == 0
    answers[:] = [window.QMessageBox.StandardButton.Yes, window.QMessageBox.StandardButton.Yes]
    ui.terminal_buttons['codex'].click()
    ui.terminal_buttons['claude'].click()
    codex, claude = FakeSession.started
    assert codex.argv == ['C:/invented/codex.exe', '--dangerously-bypass-approvals-and-sandbox']
    assert claude.argv == ['C:/invented/claude.exe', '--dangerously-skip-permissions']
    assert codex.cwd == ui.development_workspace() and ui.terminal_tabs.count() == 2
    ui.terminal_buttons['powershell'].click()  # no cloud provider: no consent dialog
    assert ui.terminal_tabs.count() == 3 and FakeSession.started[2].argv[-1] == '-NoLogo'
    # Consent is remembered per provider; a second Codex tab does not ask again.
    ui.terminal_buttons['codex'].click()
    assert ui.terminal_tabs.count() == 4
    answers[:] = [window.QMessageBox.StandardButton.No]
    ui.close_terminal(0)
    assert ui.terminal_tabs.count() == 4 and codex.open
    answers[:] = [window.QMessageBox.StandardButton.Yes]
    ui.close_terminal(0)
    assert ui.terminal_tabs.count() == 3 and not codex.open
    for view in ui.terminal_views():
        view.session.close()  # the window closes after monkeypatch is undone


def test_npm_batch_shims_run_through_the_command_interpreter(monkeypatch):
    monkeypatch.setattr('pokemind.assistant.provider.executable', lambda name: 'C:/invented/npm/claude.CMD')
    argv = terminal.command('claude')
    assert argv[1:] == ['/c', 'C:/invented/npm/claude.CMD', '--dangerously-skip-permissions']
    monkeypatch.setenv('CLAUDECODE', '1')
    monkeypatch.setenv('CLAUDE_CODE_SESSION_ID', 'invented')
    assert 'CLAUDECODE' not in terminal.environment() and 'CLAUDE_CODE_SESSION_ID' not in terminal.environment()
