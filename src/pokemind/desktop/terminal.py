"""Embedded terminal: Codex and Claude Code run as-is, like in a PowerShell window.

ConPTY (pywinpty) does the console emulation; pyte only redraws what conhost
sends back, so the app stays light (no browser engine in the EXE).
"""
import os
import re
import shutil
import subprocess
import threading

from PySide6.QtCore import QEvent, QObject, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QGuiApplication, QPainter
from PySide6.QtWidgets import QWidget

try:
    import pyte
except ImportError:  # pragma: no cover - the desktop extra installs it
    pyte = None

# Windows Terminal « Campbell » palette, with black and the background matched to PokeMind's panels.
PALETTE = {'black': '#1b2130', 'red': '#c50f1f', 'green': '#13a10e', 'brown': '#c19c00', 'blue': '#0037da',
    'magenta': '#881798', 'cyan': '#3a96dd', 'white': '#cccccc', 'brightblack': '#767676', 'brightred': '#e74856',
    'brightgreen': '#16c60c', 'brightbrown': '#f9f1a5', 'brightblue': '#3b78ff', 'brightmagenta': '#b4009e',
    'brightcyan': '#61d6d6', 'brightwhite': '#f2f2f2'}
FOREGROUND, BACKGROUND, SELECTION = '#dfe5f0', '#151a24', '#7a2533'
BYPASS = {'codex': '--dangerously-bypass-approvals-and-sandbox', 'claude': '--dangerously-skip-permissions'}
KEYS = {Qt.Key.Key_Return: '\r', Qt.Key.Key_Enter: '\r', Qt.Key.Key_Backspace: '\x7f', Qt.Key.Key_Tab: '\t',
    Qt.Key.Key_Backtab: '\x1b[Z', Qt.Key.Key_Escape: '\x1b', Qt.Key.Key_PageUp: '\x1b[5~',
    Qt.Key.Key_PageDown: '\x1b[6~', Qt.Key.Key_Delete: '\x1b[3~', Qt.Key.Key_Insert: '\x1b[2~',
    Qt.Key.Key_F1: '\x1bOP', Qt.Key.Key_F2: '\x1bOQ', Qt.Key.Key_F3: '\x1bOR', Qt.Key.Key_F4: '\x1bOS',
    Qt.Key.Key_F5: '\x1b[15~', Qt.Key.Key_F6: '\x1b[17~', Qt.Key.Key_F7: '\x1b[18~', Qt.Key.Key_F8: '\x1b[19~',
    Qt.Key.Key_F9: '\x1b[20~', Qt.Key.Key_F10: '\x1b[21~', Qt.Key.Key_F11: '\x1b[23~', Qt.Key.Key_F12: '\x1b[24~'}
CURSOR_KEYS = {Qt.Key.Key_Up: 'A', Qt.Key.Key_Down: 'B', Qt.Key.Key_Right: 'C', Qt.Key.Key_Left: 'D',
    Qt.Key.Key_Home: 'H', Qt.Key.Key_End: 'F'}
BRACKETED_PASTE = 2004 << 5  # pyte stores private modes shifted by 5
MOUSE_SGR, MOUSE_TRACKING = 1006 << 5, {1000 << 5, 1002 << 5, 1003 << 5}
# pyte reads « CSI > 4;2 m » (keyboard modes) as underline and prints the « u » of kitty
# keyboard queries; conhost answers those itself, so they are dropped before drawing.
IGNORED = re.compile(r'\x1b\[[<>=][0-9;:]*[ -/]*[@-~]|\x1b\[\?[0-9;:]*u|\x1b\[[0-9;]*:[0-9:;]*m')
PARTIAL = re.compile(r'\x1b(?:\[[0-?]*[ -/]*)?$')
COLOR_QUERY = re.compile(r'\x1b\](1[01]);\?(?:\x07|\x1b\\)')
# Markers of a parent Claude Code session; a tab is a new session of its own.
SESSION_MARKERS = {'CLAUDECODE', 'CLAUDE_PID', 'CLAUDE_EFFORT', 'CLAUDE_CODE_CHILD_SESSION', 'CLAUDE_CODE_SESSION_ID',
    'CLAUDE_CODE_SESSION_ATTENDED', 'CLAUDE_CODE_MESSAGING_SOCKET', 'CLAUDE_CODE_MESSAGING_TOKEN',
    'CLAUDE_CODE_ENTRYPOINT', 'CLAUDE_CODE_EXECPATH', 'CLAUDE_CODE_SSE_PORT'}


def available():
    if pyte is None or os.name != 'nt':
        return False
    try:
        import winpty  # noqa: F401
    except ImportError:
        return False
    return True


def command(kind):
    """argv for a tab: the real CLI, with every approval bypassed for Codex and Claude."""
    if kind == 'powershell':
        return [shutil.which('pwsh') or shutil.which('powershell') or 'powershell.exe', '-NoLogo']
    from pokemind.assistant.provider import executable
    path = executable(kind)
    argv = [path, BYPASS[kind]]
    if path.lower().endswith(('.cmd', '.bat')):
        # npm shims are batch files; CreateProcess needs the interpreter.
        argv = [os.environ.get('COMSPEC') or 'cmd.exe', '/c'] + argv
    return argv


def environment():
    return {k: v for k, v in os.environ.items() if k not in SESSION_MARKERS}


def key_text(key, modifiers, text):
    """Bytes a terminal sends for a key press; '' when the key means nothing to the shell."""
    ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
    alt = bool(modifiers & Qt.KeyboardModifier.AltModifier)
    shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
    if key in CURSOR_KEYS:
        flag = 1 + shift + 2 * alt + 4 * ctrl
        return '\x1b[' + ('1;' + str(flag) if flag > 1 else '') + CURSOR_KEYS[key]
    if key in KEYS:
        return ('\x1b' if alt and key != Qt.Key.Key_Escape else '') + KEYS[key]
    if ctrl and not alt:
        if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            return chr(key - Qt.Key.Key_A + 1)
        return {Qt.Key.Key_Space: '\x00', Qt.Key.Key_BracketLeft: '\x1b', Qt.Key.Key_Backslash: '\x1c',
                Qt.Key.Key_BracketRight: '\x1d'}.get(key, '')
    if text and text.isprintable():
        # AltGr arrives as Ctrl+Alt on Windows (e.g. @ { } on a French keyboard): plain text.
        return ('\x1b' if alt and not ctrl else '') + text
    return ''


class Screen(pyte.HistoryScreen if pyte else object):
    def __init__(self, columns, lines, reply):
        super().__init__(columns, lines, history=5000, ratio=0.3)
        self.reply = reply

    def write_process_input(self, data):
        # Answers conhost's own queries (device attributes, cursor position) at once.
        self.reply(data)


class Session(QObject):
    """One console process behind ConPTY; reads on a thread, signals on the GUI thread."""
    output = Signal(str)
    ended = Signal(object)

    def __init__(self, argv, cwd, rows, columns, env=None):
        super().__init__()
        from winpty import PtyProcess
        self.argv = list(argv)
        self.process = PtyProcess.spawn(self.argv, cwd=str(cwd), env=env or environment(), dimensions=(rows, columns))
        self.done = False
        self.lock = threading.Lock()
        threading.Thread(target=self._pump, daemon=True, name='pokemind-terminal').start()

    def _pump(self):
        try:
            while True:
                data = self.process.read(65536)
                if data:
                    self.output.emit(data)
        except (EOFError, OSError):
            pass
        self.finish()

    def finish(self):
        with self.lock:
            if self.done:
                return
            self.done = True
        self.ended.emit(getattr(self.process, 'exitstatus', None))

    def alive(self):
        return not self.done and self.process.isalive()

    def write(self, text):
        if self.alive():
            self.process.write(text)

    def resize(self, rows, columns):
        if self.alive():
            self.process.setwinsize(rows, columns)

    def close(self):
        # The whole tree: an npm shim leaves node behind if only cmd.exe dies.
        if self.process.isalive():
            subprocess.run(['taskkill', '/PID', str(self.process.pid), '/T', '/F'], capture_output=True,
                           timeout=15, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        try:
            self.process.close(force=True)
        except OSError:
            pass


class TerminalView(QWidget):
    title_changed = Signal(str)
    finished = Signal(object)

    def __init__(self, argv=None, cwd=None, parent=None, session_type=Session):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled)
        self.setCursor(Qt.CursorShape.IBeamCursor)
        self.setMinimumSize(320, 160)
        font = QFont()
        font.setFamilies(['Cascadia Mono', 'Consolas', 'Courier New'])
        font.setPointSize(11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        font.setKerning(False)
        # Kept apart from self.font(): the app stylesheet would impose its proportional font.
        self.regular, self.bold = font, QFont(font)
        self.bold.setBold(True)
        metrics = QFontMetricsF(font)
        self.cell_w, self.cell_h, self.ascent = metrics.horizontalAdvance('M'), metrics.height(), metrics.ascent()
        self.screen = Screen(100, 30, self.send)
        self.stream = pyte.Stream(self.screen)
        self.pending, self.carry, self.selection, self.anchor, self.title = [], '', None, None, ''
        self.flush_timer = QTimer(self, singleShot=True, interval=12)
        self.flush_timer.timeout.connect(self.flush)
        self.session = None
        self.exit_code = None
        if argv:
            self.session = session_type(argv, cwd, self.screen.lines, self.screen.columns)
            self.session.output.connect(self.receive)
            self.session.ended.connect(self.ended)
            # pywinpty reports EOF a few seconds after exit; polling shows the end sooner,
            # one tick late so the last lines are drawn first.
            self.watch, self.exited_ticks = QTimer(self, interval=400), 0
            self.watch.timeout.connect(self.check_exit)
            self.watch.start()

    def check_exit(self):
        if not self.session.alive():
            self.exited_ticks += 1
            if self.exited_ticks >= 2:
                self.session.finish()

    # Output -------------------------------------------------------------
    def receive(self, data):
        self.pending.append(data)
        if not self.flush_timer.isActive():
            self.flush_timer.start()

    def flush(self):
        data, self.pending = self.carry + ''.join(self.pending), []
        # A sequence cut between two reads waits for its end.
        cut = PARTIAL.search(data)
        self.carry, data = (data[cut.start():], data[:cut.start()]) if cut else ('', data)
        for query in COLOR_QUERY.finditer(data):
            value = FOREGROUND if query.group(1) == '10' else BACKGROUND
            self.send('\x1b]' + query.group(1) + ';rgb:' + '/'.join(value[i:i + 2] * 2 for i in (1, 3, 5)) + '\x1b\\')
        data = IGNORED.sub('', data)
        if data:
            self.feed(data)

    def feed(self, data):
        self.stream.feed(data)
        if self.screen.title != self.title:
            self.title = self.screen.title
            self.title_changed.emit(self.title)
        dirty = set(self.screen.dirty)
        self.screen.dirty.clear()
        if len(dirty) > self.screen.lines // 2:
            self.update()
        else:
            for row in dirty | {self.screen.cursor.y}:
                self.update(0, int(row * self.cell_h), self.width(), int(self.cell_h) + 2)

    def ended(self, code):
        self.exit_code = code
        if hasattr(self, 'watch'):
            self.watch.stop()
        self.flush()
        self.feed('\r\n\x1b[90m[Session terminée' + ('' if code is None else ' · code ' + str(code)) + ']\x1b[0m\r\n')
        self.finished.emit(code)

    def text(self):
        lines = [''.join(line[x].data for x in range(self.screen.columns)) for line in self.screen.history.top]
        return '\n'.join([l.rstrip() for l in lines] + [l.rstrip() for l in self.screen.display]).strip('\n')

    # Input --------------------------------------------------------------
    def send(self, text):
        if self.session and text:
            self.session.write(text)

    def paste(self):
        text = QGuiApplication.clipboard().text().replace('\r\n', '\r').replace('\n', '\r')
        if text:
            if BRACKETED_PASTE in self.screen.mode:
                text = '\x1b[200~' + text + '\x1b[201~'
            self.send(text)

    def copy(self):
        chosen = self.selected_text()
        if chosen:
            QGuiApplication.clipboard().setText(chosen)
        self.selection = None
        self.update()
        return bool(chosen)

    def event(self, event):
        # Every shortcut belongs to the shell while the terminal has focus (Ctrl+R, Ctrl+L, Échap…).
        if event.type() == QEvent.Type.ShortcutOverride:
            event.accept()
            return True
        return super().event(event)

    def focusNextPrevChild(self, forward):
        return False  # Tab completes in the shell instead of moving the focus

    def keyPressEvent(self, event):
        key, modifiers = event.key(), event.modifiers()
        ctrl = modifiers & Qt.KeyboardModifier.ControlModifier
        shift = modifiers & Qt.KeyboardModifier.ShiftModifier
        if ctrl and key == Qt.Key.Key_V:
            return self.paste()
        if ctrl and key == Qt.Key.Key_C and (shift or self.selection):
            return self.copy()
        if shift and key in (Qt.Key.Key_PageUp, Qt.Key.Key_PageDown):
            return self.scroll(key == Qt.Key.Key_PageUp)
        text = key_text(key, modifiers, event.text())
        if text:
            self.selection = None
            self.bottom()
            self.send(text)
        event.accept()

    def inputMethodEvent(self, event):
        self.send(event.commitString())
        event.accept()

    def wheelEvent(self, event):
        steps = event.angleDelta().y() // 120
        mode = self.screen.mode
        if MOUSE_SGR in mode and mode & MOUSE_TRACKING:
            # Full-screen apps (Codex) scroll their own transcript.
            row, column = self.cell(event.position())
            self.send(('\x1b[<%d;%d;%dM' % (64 if steps > 0 else 65, column + 1, row + 1)) * abs(steps))
            return
        for _ in range(abs(steps)):
            self.scroll(steps > 0)

    def scroll(self, up):
        (self.screen.prev_page if up else self.screen.next_page)()
        self.screen.dirty.clear()
        self.update()

    def bottom(self):
        history = self.screen.history
        if history.position < history.size and history.bottom:
            while history.bottom:
                self.screen.next_page()
            self.update()

    # Selection ----------------------------------------------------------
    def cell(self, point):
        return (max(0, min(self.screen.lines - 1, int(point.y() // self.cell_h))),
                max(0, min(self.screen.columns, int(point.x() // self.cell_w))))

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.MouseButton.LeftButton:
            self.anchor, self.selection = self.cell(event.position()), None
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.copy() or self.paste()  # Windows Terminal habit: right-click copies, or pastes

    def mouseMoveEvent(self, event):
        if self.anchor is not None:
            end = self.cell(event.position())
            self.selection = (min(self.anchor, end), max(self.anchor, end)) if end != self.anchor else None
            self.update()

    def mouseReleaseEvent(self, event):
        self.anchor = None

    def selected_text(self):
        if not self.selection:
            return ''
        (top, left), (bottom, right) = self.selection
        rows = []
        for y in range(top, bottom + 1):
            line = self.screen.display[y]
            rows.append(line[left if y == top else 0:right if y == bottom else None].rstrip())
        return '\n'.join(rows)

    def selected(self, y, x):
        if not self.selection:
            return False
        start, end = self.selection
        return start <= (y, x) < end

    # Geometry and painting ----------------------------------------------
    def resizeEvent(self, event):
        columns = max(20, int(self.width() // self.cell_w))
        lines = max(5, int(self.height() // self.cell_h))
        if (columns, lines) != (self.screen.columns, self.screen.lines):
            self.screen.resize(lines, columns)
            if self.session:
                self.session.resize(lines, columns)
        super().resizeEvent(event)

    @staticmethod
    def color(name, default):
        if name == 'default':
            return QColor(default)
        if name in PALETTE:
            return QColor(PALETTE[name])
        return QColor('#' + name) if len(name) == 6 else QColor(default)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor(BACKGROUND))
        first = max(0, int(event.rect().top() // self.cell_h))
        last = min(self.screen.lines - 1, int(event.rect().bottom() // self.cell_h))
        for y in range(first, last + 1):
            self.paint_line(painter, y)
        cursor = self.screen.cursor
        if not cursor.hidden and self.hasFocus() and first <= cursor.y <= last:
            box = QRectF(cursor.x * self.cell_w, cursor.y * self.cell_h, self.cell_w, self.cell_h)
            painter.fillRect(box, QColor(255, 255, 255, 150))
        painter.end()

    def paint_line(self, painter, y):
        line, top = self.screen.buffer[y], y * self.cell_h
        x = 0
        while x < self.screen.columns:
            char = line[x]
            style = (char.fg, char.bg, char.bold, char.reverse, char.underscore, char.italics, self.selected(y, x))
            run = [char.data]
            end = x + 1
            # Plain characters share a run; symbols from fallback fonts are drawn cell by cell.
            if plain(char.data):
                while end < self.screen.columns:
                    following = line[end]
                    if (following.fg, following.bg, following.bold, following.reverse, following.underscore,
                            following.italics, self.selected(y, end)) != style or not plain(following.data):
                        break
                    run.append(following.data)
                    end += 1
            self.paint_run(painter, x, end, top, ''.join(run), style)
            x = end

    def paint_run(self, painter, start, end, top, text, style):
        fg, bg, bold, reverse, underscore, italics, chosen = style
        front = self.color(fg, FOREGROUND)
        back = self.color(bg, BACKGROUND)
        if reverse:
            front, back = back, front
        if chosen:
            back = QColor(SELECTION)
        box = QRectF(start * self.cell_w, top, (end - start) * self.cell_w, self.cell_h)
        if back != QColor(BACKGROUND):
            painter.fillRect(box, back)
        if text.strip():
            font = self.bold if bold else self.regular
            if italics or underscore:
                font = QFont(font)
                font.setItalic(bool(italics))
                font.setUnderline(bool(underscore))
            painter.setFont(font)
            painter.setPen(front)
            painter.drawText(QPointF(box.left(), top + self.ascent), text)


def plain(data):
    return len(data) == 1 and (ord(data) < 0x2000 or 0x2500 <= ord(data) <= 0x259f)
