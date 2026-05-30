import os
import sys
import subprocess
import logging
import tempfile

from PyQt6.QtCore import QObject, pyqtSignal

from core.constants import DATA_DIR

logger = logging.getLogger(__name__)


class Signals(QObject):
    """Signals to communicate between worker threads and the main UI."""

    output_received = pyqtSignal(str, str)  # message, message_type
    error_received = pyqtSignal(str)


class CodeRunner:
    """Runs a Python script from a worker thread (ThreadPoolExecutor)."""

    DEFAULT_TIMEOUT = 30

    def __init__(self, file_path, input_value="", signals=None, timeout=None):
        self.file_path = file_path
        self.input_value = input_value or ""
        self.signals = signals or Signals()
        self.timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        self.process = None
        self._temp_file = None

    @classmethod
    def from_source(cls, source, signals=None, timeout=None):
        """Write source to a temp file and return a runner for that file."""
        fd, path = tempfile.mkstemp(suffix=".py", dir=DATA_DIR, text=True)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(source)
        runner = cls(path, signals=signals, timeout=timeout)
        runner._temp_file = path
        return runner

    def run(self):
        try:
            self.process = subprocess.Popen(
                [sys.executable, self.file_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(self.file_path) or None,
            )

            try:
                stdout, stderr = self.process.communicate(
                    input=self.input_value, timeout=self.timeout
                )
            except subprocess.TimeoutExpired:
                self.kill()
                stdout, stderr = self.process.communicate()
                stderr = (stderr or "") + f"\nProcess timed out after {self.timeout}s."

            if stdout:
                self.signals.output_received.emit(stdout.rstrip(), "info")
            if stderr:
                self.signals.error_received.emit(stderr.rstrip())

        except Exception as exc:
            logger.exception("Code execution failed")
            self.signals.error_received.emit(str(exc))
        finally:
            self._cleanup()

    def kill(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.kill()
            except OSError as exc:
                logger.warning("Could not kill process: %s", exc)

    def _cleanup(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(3)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None

        if self._temp_file and os.path.exists(self._temp_file):
            try:
                os.remove(self._temp_file)
            except OSError as exc:
                logger.warning("Could not remove temp file %s: %s", self._temp_file, exc)
            self._temp_file = None


# Backward-compatible aliases
CodeRunnerThread = CodeRunner
