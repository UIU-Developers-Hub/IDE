import logging
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time

from PyQt6.QtCore import QThread, pyqtSignal

from core.constants import DATA_DIR

logger = logging.getLogger(__name__)

PDB_COMMANDS = {
    "continue": "c",
    "step": "n",
    "next": "n",
    "quit": "q",
}


class DebuggerThread(QThread):
    output_received = pyqtSignal(str)
    error_received = pyqtSignal(str)

    def __init__(self, code: str, breakpoints=None):
        super().__init__()
        self.code = code
        self.breakpoints = frozenset(breakpoints or [])
        self.command_queue = queue.Queue()
        self.running = True
        self.process = None
        self._temp_file = None

    def run(self):
        try:
            fd, self._temp_file = tempfile.mkstemp(suffix=".py", dir=DATA_DIR, text=True)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(self.code)

            logger.info("Starting debugger for %s", self._temp_file)

            self.process = subprocess.Popen(
                [sys.executable, "-m", "pdb", self._temp_file],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            threading.Thread(target=self._process_input, daemon=True).start()
            if self.breakpoints:
                threading.Thread(target=self._apply_breakpoints, daemon=True).start()

            assert self.process.stdout is not None
            for line in self.process.stdout:
                if line:
                    self.output_received.emit(line.rstrip())

            self.process.wait()

        except Exception as exc:
            logger.exception("Debugger failed")
            self.error_received.emit(str(exc))
        finally:
            self._cleanup()

    def _apply_breakpoints(self):
        time.sleep(0.4)
        if not self.process or not self.process.stdin:
            return
        for line in sorted(self.breakpoints):
            try:
                self.process.stdin.write(f"break {line + 1}\n")
                self.process.stdin.flush()
            except Exception as exc:
                self.error_received.emit(f"Failed to set breakpoint: {exc}")

    def _process_input(self):
        while self.running:
            try:
                command = self.command_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if not command or not self.process or not self.process.stdin:
                continue

            pdb_cmd = PDB_COMMANDS.get(command.lower(), command)
            try:
                self.process.stdin.write(pdb_cmd + "\n")
                self.process.stdin.flush()
            except Exception as exc:
                self.error_received.emit(f"Failed to send command: {exc}")

    def send_command(self, command: str):
        self.command_queue.put(command)

    def _cleanup(self):
        self.running = False

        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(2)
            except Exception as exc:
                logger.warning("Failed to terminate debugger: %s", exc)

        if self._temp_file and os.path.exists(self._temp_file):
            try:
                os.remove(self._temp_file)
            except OSError as exc:
                logger.warning("Could not remove debug temp file: %s", exc)

    def stop(self):
        self.running = False
        self.send_command("quit")
        if self.isRunning():
            self.wait(3000)
