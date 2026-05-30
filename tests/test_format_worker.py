import unittest
from unittest.mock import patch

import qt_helpers  # noqa: F401
from core.format_worker import FormatWorker


class TestFormatWorker(unittest.TestCase):
    @patch("core.format_worker.run_ruff_format")
    def test_format_worker_emits_formatted_code(self, mock_format):
        mock_format.return_value = ("print('hi')\n", "", 0)

        worker = FormatWorker("print( 'hi' )")
        results = []
        worker.format_done.connect(results.append)
        worker.run()

        self.assertEqual(results[0], "print('hi')\n")


if __name__ == "__main__":
    unittest.main()
