import unittest

from core.outline import extract_python_outline


class TestOutline(unittest.TestCase):
    def test_extracts_class_and_methods(self):
        source = '''
class Foo:
    def bar(self):
        pass

def baz():
    return 1
'''
        symbols = extract_python_outline(source)
        names = [s.name for s in symbols]
        self.assertIn("Foo", names)
        self.assertIn("bar", names)
        self.assertIn("baz", names)


if __name__ == "__main__":
    unittest.main()
