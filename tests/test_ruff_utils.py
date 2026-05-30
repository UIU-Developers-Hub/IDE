import unittest

from core.ruff_utils import parse_diagnostic_output


class TestRuffUtils(unittest.TestCase):
    def test_parse_ruff_output_strips_autofix_marker(self):
        output = "code.py:2:1: F401 [*] `sys` imported but unused\n"
        results = parse_diagnostic_output(output)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["line"], 2)
        self.assertTrue(results[0]["message"].startswith("F401"))

    def test_parse_empty_output(self):
        self.assertEqual(parse_diagnostic_output(""), [])


if __name__ == "__main__":
    unittest.main()
