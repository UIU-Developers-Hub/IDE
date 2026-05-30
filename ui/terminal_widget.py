import os
import sys

from PyQt6.QtCore import QProcess, Qt
from PyQt6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPlainTextEdit


class TerminalWidget(QWidget):
    """Interactive shell terminal using QProcess (VS Code–style panel)."""

    def __init__(self, cwd: str, parent=None):
        super().__init__(parent)
        self._cwd = cwd
        self._started = False
        self._history: list[str] = []
        self._history_index = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Cascadia Mono", 12))
        self.output.setStyleSheet(
            "background: #1e1e1e; color: #cccccc; border: none; padding: 6px;"
        )
        layout.addWidget(self.output)

        self.input = QPlainTextEdit()
        self.input.setMaximumHeight(72)
        self.input.setFont(QFont("Cascadia Mono", 12))
        self.input.setPlaceholderText("Enter command… (Up/Down for history)")
        self.input.setStyleSheet(
            "background: #252526; color: #cccccc; border-top: 1px solid #3e3e42; padding: 6px;"
        )
        self.input.installEventFilter(self)
        layout.addWidget(self.input)

        self.process = QProcess(self)
        self.process.setWorkingDirectory(cwd)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.finished.connect(self._on_finished)

    def set_cwd(self, cwd: str):
        self._cwd = cwd
        if not self._started:
            self.process.setWorkingDirectory(cwd)

    def start(self):
        if self._started:
            return
        self._append(f"PyDitor Terminal — {self._cwd}\n", "#858585")
        if sys.platform == "win32":
            shell = os.environ.get("COMSPEC", "cmd.exe")
            self.process.start(shell, ["/Q", "/K"])
        else:
            self.process.start("/bin/bash", ["-i"])
        self._started = True
        self.input.setFocus()

    def _disconnect_process(self):
        try:
            self.process.readyReadStandardOutput.disconnect(self._read_output)
        except TypeError:
            pass
        try:
            self.process.finished.disconnect(self._on_finished)
        except TypeError:
            pass

    def stop(self, *, force: bool = False, shutdown: bool = False):
        """Stop the shell process; disconnect Qt signals first (avoids Windows crash on exit)."""
        if self.process.state() == QProcess.ProcessState.NotRunning:
            self._started = False
            return

        self._disconnect_process()

        if shutdown:
            # During app exit: never kill/wait — that triggers Windows 0xC0000409 with cmd.exe
            try:
                line = b"exit\r\n" if sys.platform == "win32" else b"exit\n"
                self.process.write(line)
            except (RuntimeError, OSError):
                pass
            self.process.setParent(None)
            self._started = False
            return

        if not force:
            try:
                line = b"exit\r\n" if sys.platform == "win32" else b"exit\n"
                self.process.write(line)
                if self.process.waitForFinished(800):
                    self._started = False
                    return
            except (RuntimeError, OSError):
                pass

        self.process.terminate()
        if not self.process.waitForFinished(1000):
            self.process.kill()
            self.process.waitForFinished(500)
        self._started = False

    def kill(self):
        self.stop(force=True)

    def clear(self):
        self.output.clear()

    def _read_output(self):
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if data:
            self._append(data)

    def _on_finished(self, code, _status):
        self._append(f"\n[Process exited with code {code}]\n", "#cca700")
        self._started = False

    def _append(self, text: str, color: str = "#cccccc"):
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(text)
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def _send_command(self):
        cmd = self.input.toPlainText().strip()
        if not cmd:
            return
        if cmd.lower() in ("clear", "cls"):
            self.clear()
            self.input.clear()
            return
        if cmd.lower() == "exit":
            self.kill()
            self.input.clear()
            return

        self._history.append(cmd)
        self._history_index = len(self._history)
        self._append(f"\n$ {cmd}\n", "#569cd6")

        if self.process.state() == QProcess.ProcessState.NotRunning:
            self.start()

        line = cmd + ("\r\n" if sys.platform == "win32" else "\n")
        self.process.write(line.encode("utf-8", errors="replace"))
        self.input.clear()

    def closeEvent(self, event):
        self.stop(shutdown=True)
        super().closeEvent(event)

    def eventFilter(self, obj, event):
        if obj is self.input and event.type() == event.Type.KeyPress:
            key = event.key()
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                    return False
                self._send_command()
                return True
            if key == Qt.Key.Key_Up and self._history:
                self._history_index = max(0, self._history_index - 1)
                self.input.setPlainText(self._history[self._history_index])
                return True
            if key == Qt.Key.Key_Down and self._history:
                self._history_index = min(len(self._history), self._history_index + 1)
                if self._history_index >= len(self._history):
                    self.input.clear()
                else:
                    self.input.setPlainText(self._history[self._history_index])
                return True
        return super().eventFilter(obj, event)
