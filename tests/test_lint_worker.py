import unittest
from unittest.mock import patch

import qt_helpers  # noqa: F401
from core.lint_worker import LintWorker


class TestLintWorker(unittest.TestCase):
    @patch("core.lint_worker.run_ruff_check")
    def test_lint_worker_emits_results(self, mock_check):
        mock_check.return_value = (
            "code.py:1:1: F401 [*] `os` imported but unused\n",
            "",
            1,
        )

        worker = LintWorker("import os\n")
        results = []
        worker.lint_result.connect(lambda lint_data: results.extend(lint_data))
        worker.run()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["line"], 1)
        self.assertIn("F401", results[0]["message"])


if __name__ == "__main__":
    unittest.main()
