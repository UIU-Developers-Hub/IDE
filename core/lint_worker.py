import logging

from PyQt6.QtCore import QThread, pyqtSignal

from core.ruff_utils import parse_diagnostic_output, run_ruff_check

logger = logging.getLogger(__name__)


class LintWorker(QThread):
    lint_result = pyqtSignal(list)

    def __init__(self, code):
        super().__init__()
        self.code = code

    def run(self):
        try:
            stdout, stderr, _returncode = run_ruff_check(self.code)
            output = stdout or stderr
            self.lint_result.emit(parse_diagnostic_output(output))
        except FileNotFoundError:
            logger.warning("ruff is not installed")
        except Exception as exc:
            logger.error("Linting error: %s", exc)
        finally:
            if self.isRunning():
                self.quit()

    def stop(self):
        self.requestInterruption()
        self.quit()
        self.wait(2000)
