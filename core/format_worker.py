import logging

from PyQt6.QtCore import QThread, pyqtSignal

from core.ruff_utils import run_ruff_format, run_ruff_import_sort

logger = logging.getLogger(__name__)


class FormatWorker(QThread):
    format_done = pyqtSignal(str)
    format_failed = pyqtSignal(str)

    def __init__(self, code: str, mode: str = "format"):
        super().__init__()
        self.code = code
        self.mode = mode

    def run(self):
        try:
            if self.mode == "imports":
                stdout, stderr, returncode = run_ruff_import_sort(self.code)
            else:
                stdout, stderr, returncode = run_ruff_format(self.code)

            if returncode != 0 and stderr:
                self.format_failed.emit(stderr.strip())
                return

            formatted = stdout if stdout.strip() else self.code
            self.format_done.emit(formatted)
        except FileNotFoundError:
            self.format_failed.emit("Ruff is not installed. Run: pip install ruff")
        except Exception as exc:
            logger.error("Format error: %s", exc)
            self.format_failed.emit(str(exc))

    def stop(self):
        self.requestInterruption()
        self.quit()
        self.wait(2000)
