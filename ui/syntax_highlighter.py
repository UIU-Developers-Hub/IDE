from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.token import Token
from pygments.formatter import Formatter


class QFormatter(Formatter):
    """Pygments formatter that stores tokens for QSyntaxHighlighter."""

    def __init__(self, highlighter):
        super().__init__()
        self.highlighter = highlighter
        self.data = []

    def format(self, tokensource, outfile):
        for ttype, value in tokensource:
            self.data.append((ttype, value))


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """Python syntax highlighter using Pygments."""

    def __init__(self, document):
        super().__init__(document)
        self.lexer = PythonLexer()
        self.formatter = QFormatter(self)
        self.formats = {
            Token.Keyword: self.create_format(QColor("#569CD6"), bold=True),
            Token.Comment: self.create_format(QColor("#6A9955")),
            Token.String: self.create_format(QColor("#CE9178")),
            Token.Number: self.create_format(QColor("#B5CEA8")),
            Token.Operator: self.create_format(QColor("#D4D4D4")),
            Token.Name.Function: self.create_format(QColor("#DCDCAA")),
            Token.Name.Class: self.create_format(QColor("#4EC9B0")),
            Token.Name.Variable: self.create_format(QColor("#9CDCFE")),
            Token.Text: self.create_format(QColor("#D4D4D4")),
        }

    def create_format(self, color, bold=False, italic=False):
        text_format = QTextCharFormat()
        text_format.setForeground(color)
        if bold:
            text_format.setFontWeight(QFont.Weight.Bold)
        if italic:
            text_format.setFontItalic(True)
        return text_format

    def highlightBlock(self, text):
        highlight(text, self.lexer, self.formatter)

        index = 0
        for ttype, value in self.formatter.data:
            length = len(value)
            token_type = ttype
            while token_type not in self.formats and token_type.parent:
                token_type = token_type.parent
            if token_type in self.formats:
                self.setFormat(index, length, self.formats[token_type])
            index += length

        self.formatter.data = []
