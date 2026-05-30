import logging
import re

import jedi
from PyQt6.Qsci import QsciLexerPython, QsciScintilla
from PyQt6.QtCore import (
    QEvent, QObject, QTimer, Qt, pyqtSignal, QStringListModel,
)
from PyQt6.QtGui import QColor, QFont, QKeyEvent, QAction
from PyQt6.QtWidgets import QCompleter, QMenu, QToolTip
from concurrent.futures import ThreadPoolExecutor

from core.lint_worker import LintWorker

logger = logging.getLogger(__name__)

BRACKET_PAIRS = {"(": ")", "[": "]", "{": "}"}
OPEN_BRACKETS = set(BRACKET_PAIRS)
CLOSE_BRACKETS = set(BRACKET_PAIRS.values())

BP_MARKER = 1
LINT_INDICATOR = 1
BP_MARGIN = 0       # left gutter — breakpoint dots
LINE_MARGIN = 1     # line numbers
FOLD_MARGIN = 2     # code folding (set by setFolding)


class _DocumentShim(QObject):
    modificationChanged = pyqtSignal(bool)

    def __init__(self, editor):
        super().__init__()
        self._editor = editor
        editor.modificationChanged.connect(self.modificationChanged.emit)

    def isModified(self):
        return self._editor.isModified()

    def setModified(self, modified):
        self._editor.setModified(modified)


class _TextCursorShim:
    def __init__(self, editor):
        self._editor = editor

    def blockNumber(self):
        return self._editor.getCursorPosition()[0]

    def positionInBlock(self):
        return self._editor.getCursorPosition()[1]

    def hasSelection(self):
        return self._editor.hasSelectedText()

    def selectedText(self):
        return self._editor.selectedText()

    def insertText(self, text):
        self._editor.insert(text)

    def clearSelection(self):
        self._editor.setSelection(-1, -1, -1, -1)


class _LineNumberAreaShim:
    def __init__(self, editor):
        self._editor = editor

    def update(self):
        pass


class CompletionWorkerSignals(QObject):
    completion_ready = pyqtSignal(list)


class CodeEditor(QsciScintilla):
    """Python code editor powered by QScintilla."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.file_path = None
        self.untitled_name = "Untitled-1"
        self.lint_errors = {}
        self.breakpoints = set()
        self._doc_shim = _DocumentShim(self)
        self.lineNumberArea = _LineNumberAreaShim(self)

        self._setup_lexer()
        self._setup_margins()
        self._setup_editor()
        self._setup_linting()
        self._setup_autocompletion()
        self._setup_documentation()
        self.installEventFilter(self)

    def _setup_lexer(self):
        self._lexer = QsciLexerPython(self)
        font = QFont("Cascadia Code", 13)
        if not QFont("Cascadia Code").exactMatch():
            font = QFont("Consolas", 13)
        self._lexer.setDefaultFont(font)
        self._lexer.setDefaultPaper(QColor("#1e1e1e"))
        self._lexer.setDefaultColor(QColor("#d4d4d4"))
        styles = {
            QsciLexerPython.Keyword: "#569cd6",
            QsciLexerPython.ClassName: "#4ec9b0",
            QsciLexerPython.FunctionMethodName: "#dcdcaa",
            QsciLexerPython.DoubleQuotedString: "#ce9178",
            QsciLexerPython.SingleQuotedString: "#ce9178",
            QsciLexerPython.TripleDoubleQuotedString: "#ce9178",
            QsciLexerPython.TripleSingleQuotedString: "#ce9178",
            QsciLexerPython.Number: "#b5cea8",
            QsciLexerPython.Comment: "#6a9955",
            QsciLexerPython.CommentBlock: "#6a9955",
            QsciLexerPython.Decorator: "#dcdcaa",
            QsciLexerPython.Operator: "#d4d4d4",
        }
        for style, color in styles.items():
            self._lexer.setColor(QColor(color), style)
        self.setLexer(self._lexer)
        self.setFont(font)

    def _setup_editor(self):
        self.setPaper(QColor("#1e1e1e"))
        self.setColor(QColor("#d4d4d4"))
        self.setCaretForegroundColor(QColor("#ffffff"))
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#2a2d2e"))
        self.setIndentationsUseTabs(False)
        self.setTabWidth(4)
        self.setIndentationGuides(True)
        self.setAutoIndent(True)
        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.setMatchedBraceBackgroundColor(QColor("#3a3d41"))
        self.setMatchedBraceForegroundColor(QColor("#ffcc00"))
        self.setFolding(QsciScintilla.FoldStyle.BoxedTreeFoldStyle)
        self.setFoldMarginColors(QColor("#252526"), QColor("#252526"))
        # Keep breakpoint markers off the fold margin
        self.setMarginMarkerMask(FOLD_MARGIN, self.marginMarkerMask(FOLD_MARGIN) & ~(1 << BP_MARKER))

    def _setup_margins(self):
        # Breakpoint gutter (leftmost — VS Code style)
        self.setMarginType(BP_MARGIN, QsciScintilla.MarginType.SymbolMargin)
        self.setMarginWidth(BP_MARGIN, 16)
        self.setMarginSensitivity(BP_MARGIN, True)
        self.setMarginMarkerMask(BP_MARGIN, 1 << BP_MARKER)

        # Line numbers — no markers here (avoids full-line red blocks)
        self.setMarginType(LINE_MARGIN, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(LINE_MARGIN, "00000")
        self.setMarginLineNumbers(LINE_MARGIN, True)
        self.setMarginMarkerMask(LINE_MARGIN, 0)

        self.setMarginsForegroundColor(QColor("#858585"))
        self.setMarginsBackgroundColor(QColor("#252526"))

        self.markerDefine(QsciScintilla.MarkerSymbol.Circle, BP_MARKER)
        self.setMarkerForegroundColor(QColor("#e51400"), BP_MARKER)
        self.setMarkerBackgroundColor(QColor("#e51400"), BP_MARKER)
        self.marginClicked.connect(self._on_margin_clicked)

        self.indicatorDefine(QsciScintilla.IndicatorStyle.SquiggleIndicator, LINT_INDICATOR)
        self.setIndicatorForegroundColor(QColor("#f44747"), LINT_INDICATOR)

    def _setup_linting(self):
        self.lint_timer = QTimer(self)
        self.lint_timer.setSingleShot(True)
        self.lint_timer.setInterval(1500)
        self.lint_timer.timeout.connect(self.lint_code)
        self.textChanged.connect(self.lint_timer.start)
        self.textChanged.connect(self._on_text_modified)
        self.cursorPositionChanged.connect(self._on_cursor_moved)

    def _setup_documentation(self):
        self.doc_timer = QTimer(self)
        self.doc_timer.setSingleShot(True)
        self.doc_timer.setInterval(400)
        self.doc_timer.timeout.connect(self._update_documentation)

    def _setup_autocompletion(self):
        self.completer = QCompleter(self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.activated.connect(self.insert_completion)

        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="jedi")
        self.worker_signals = CompletionWorkerSignals()
        self.worker_signals.completion_ready.connect(self.show_completions)

        self.auto_completion_timer = QTimer(self)
        self.auto_completion_timer.setSingleShot(True)
        self.auto_completion_timer.setInterval(300)
        self.auto_completion_timer.timeout.connect(self._handle_autocompletion)
        self.textChanged.connect(self.auto_completion_timer.start)

    def document(self):
        return self._doc_shim

    def textCursor(self):
        return _TextCursorShim(self)

    def setTextCursor(self, cursor):
        if hasattr(cursor, "blockNumber"):
            self.setCursorPosition(cursor.blockNumber(), cursor.positionInBlock())

    def toPlainText(self):
        return self.text()

    def setPlainText(self, text):
        self.setText(text)

    def blockCount(self):
        return self.lines()

    def setFont(self, font):
        super().setFont(font)
        self._lexer.setDefaultFont(font)
        self.setMarginWidth(LINE_MARGIN, "00000")

    def _on_text_modified(self):
        if self.main_window:
            self.main_window.update_tab_title(self)

    def _on_cursor_moved(self, _line, _index):
        self.doc_timer.start()
        if self.main_window:
            self.main_window.update_status_bar(self)

    def _update_documentation(self):
        if self.main_window:
            self.main_window.update_documentation(self)

    def _on_margin_clicked(self, margin, line, _modifiers):
        if margin != BP_MARGIN:
            return
        if line in self.breakpoints:
            self.breakpoints.remove(line)
            self.markerDelete(line, BP_MARKER)
        else:
            self.breakpoints.add(line)
            self.markerAdd(line, BP_MARKER)

    def _refresh_breakpoints(self):
        self.markerDeleteAll(BP_MARKER)
        for line in sorted(self.breakpoints):
            if 0 <= line < self.lines():
                self.markerAdd(line, BP_MARKER)

    def lint_code(self):
        code = self.text().strip()
        if not code:
            self.lint_errors.clear()
            if self.lines() > 0:
                self.clearIndicatorRange(0, 0, max(0, self.lines() - 1), 0, LINT_INDICATOR)
            if self.main_window:
                self.main_window.process_lint_results([])
            return

        if hasattr(self, "lint_worker") and self.lint_worker.isRunning():
            self.lint_worker.stop()

        self.lint_worker = LintWorker(self.text())
        self.lint_worker.lint_result.connect(self._on_lint_results)
        self.lint_worker.start()

    def _on_lint_results(self, lint_data):
        self.lint_errors.clear()
        self.clearIndicatorRange(0, 0, max(0, self.lines() - 1), 0, LINT_INDICATOR)

        for error in lint_data:
            line_number = error["line"] - 1
            message = error["message"]
            if line_number < 0 or line_number >= self.lines():
                continue
            self.lint_errors[line_number] = message
            length = max(1, self.lineLength(line_number))
            self.fillIndicatorRange(line_number, 0, line_number, length, LINT_INDICATOR)

        if self.main_window:
            self.main_window.process_lint_results(lint_data)

    def eventFilter(self, obj, event):
        if obj is self and event.type() == QEvent.Type.ToolTip:
            line = self._line_at_point(event.pos())
            message = self.lint_errors.get(line)
            if message:
                QToolTip.showText(
                    event.globalPosition().toPoint(),
                    f"<b>Line {line + 1}</b><br>{message}",
                    self,
                )
            else:
                QToolTip.hideText()
            return True
        return super().eventFilter(obj, event)

    def _line_at_point(self, point):
        pos = self.charPositionFromPoint(point.x(), point.y())
        if pos < 0:
            return -1
        return self.lineFromPosition(pos)

    def find_text(self, text, backward=False, case_sensitive=False):
        if not text:
            return False
        return self.findFirst(
            text, False, case_sensitive, False, True, not backward,
        )

    def replace_current(self, find, replace, case_sensitive=False):
        if self.hasSelectedText():
            selected = self.selectedText()
            matches = selected == find
            if not case_sensitive:
                matches = selected.lower() == find.lower()
            if matches:
                self.replaceSelectedText(replace)
                return True
        return self.find_text(find, case_sensitive=case_sensitive)

    def replace_all(self, find, replace, case_sensitive=False):
        self.beginUndoAction()
        count = 0
        if self.findFirst(find, False, case_sensitive, False, True, True):
            self.replace(replace)
            count = 1
            while self.findNext():
                self.replace(replace)
                count += 1
        self.endUndoAction()
        return count

    def go_to_line(self, line_number):
        line = line_number - 1
        if line < 0 or line >= self.lines():
            return False
        self.setCursorPosition(line, 0)
        self.ensureLineVisible(line)
        return True

    def toggle_comment(self):
        line_from, index_from, line_to, index_to = self.getSelection()
        if line_from < 0:
            line_from = line_to = self.getCursorPosition()[0]
            index_from = index_to = 0

        lines = []
        for line in range(line_from, line_to + 1):
            text = self.text(line)
            if text.strip():
                lines.append((line, text))

        uncomment = bool(lines) and all(
            text.lstrip().startswith("#") for _, text in lines
        )

        self.beginUndoAction()
        for line, text in lines:
            if uncomment:
                new_text = re.sub(r"^(\s*)#\s?", r"\1", text, count=1)
            else:
                indent = len(text) - len(text.lstrip())
                new_text = text[:indent] + "# " + text[indent:]
            self.setSelection(line, 0, line, self.lineLength(line))
            self.replaceSelectedText(new_text)
        self.endUndoAction()

    def keyPressEvent(self, event: QKeyEvent):
        if (
            event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            and event.modifiers() == Qt.KeyboardModifier.NoModifier
        ):
            line, _ = self.getCursorPosition()
            text = self.text(line).rstrip("\r\n")
            indent = len(text) - len(text.lstrip())
            if text.rstrip().endswith(":"):
                indent += 4
            super().keyPressEvent(event)
            if indent:
                self.insert(" " * indent)
            return

        if event.key() == Qt.Key.Key_Tab and self.hasSelectedText():
            self._indent_selection()
            return
        if event.key() == Qt.Key.Key_Backtab:
            self._unindent_selection()
            return

        super().keyPressEvent(event)

    def _indent_selection(self):
        line_from, _, line_to, _ = self.getSelection()
        if line_from < 0:
            return
        self.beginUndoAction()
        for line in range(line_from, line_to + 1):
            self.insertAt("    ", line, 0)
        self.endUndoAction()

    def _unindent_selection(self):
        line_from, _, line_to, _ = self.getSelection()
        if line_from < 0:
            line_from = line_to = self.getCursorPosition()[0]
        self.beginUndoAction()
        for line in range(line_from, line_to + 1):
            text = self.text(line)
            if text.startswith("    "):
                self.setSelection(line, 0, line, 4)
                self.replaceSelectedText("")
            elif text.startswith("\t"):
                self.setSelection(line, 0, line, 1)
                self.replaceSelectedText("")
        self.endUndoAction()

    def _handle_autocompletion(self):
        line, column = self.getCursorPosition()
        if column <= 0:
            return

        source = self.text()
        lines = source.splitlines()
        if line >= len(lines):
            return
        line_text = lines[line]
        if column > len(line_text):
            return
        prev_char = line_text[column - 1]
        if not (prev_char.isidentifier() or prev_char in "._"):
            self.completer.popup().hide()
            return

        self.executor.submit(self._get_completions, source, line + 1, column)

    def _get_completions(self, source, line, column):
        try:
            script = jedi.Script(code=source, path=self.file_path or "<stdin>")
            completions = script.complete(line=line, column=column)
            names = [item.name for item in completions]
            self.worker_signals.completion_ready.emit(names)
        except Exception as exc:
            logger.debug("Jedi completion failed: %s", exc)

    def show_completions(self, completion_suggestions):
        if not completion_suggestions:
            self.completer.popup().hide()
            return

        self.completer.setModel(QStringListModel(completion_suggestions, self.completer))
        line, index = self.getCursorPosition()
        pos = self.positionFromLineIndex(line, index)
        x = self.pointXFromPosition(pos)
        y = self.pointYFromPosition(pos)
        from PyQt6.QtCore import QRect
        popup = self.completer.popup()
        scroll_width = popup.verticalScrollBar().sizeHint().width()
        rect = QRect(x, y, popup.sizeHintForColumn(0) + scroll_width, 0)
        self.completer.complete(rect)

    def insert_completion(self, completion):
        line, index = self.getCursorPosition()
        line_text = self.text(line)
        start = index
        while start > 0 and (line_text[start - 1].isidentifier() or line_text[start - 1] in "._"):
            start -= 1
        self.setSelection(line, start, line, index)
        self.replaceSelectedText(completion)

    def contextMenuEvent(self, event):
        if not self.main_window:
            return super().contextMenuEvent(event)

        menu = QMenu(self)
        mw = self.main_window
        items = [
            ("Cut", "Ctrl+X", lambda: self.cut()),
            ("Copy", "Ctrl+C", lambda: self.copy()),
            ("Paste", "Ctrl+V", lambda: self.paste()),
            None,
            ("Find", "Ctrl+F", mw.show_find_dialog),
            ("Replace", "Ctrl+H", mw.show_replace_dialog),
            ("Go to Line", "Ctrl+G", mw.show_go_to_line),
            None,
            ("Toggle Comment", "Ctrl+/", mw.toggle_comment),
            ("Format Document", "Shift+Alt+F", mw.format_document),
            ("Organize Imports", "Ctrl+Alt+I", mw.organize_imports),
        ]
        for entry in items:
            if entry is None:
                menu.addSeparator()
                continue
            label, shortcut, slot = entry
            action = QAction(label, self)
            action.setShortcut(shortcut)
            action.triggered.connect(slot)
            menu.addAction(action)
        menu.exec(event.globalPos())

    def closeEvent(self, event):
        if hasattr(self, "lint_worker") and self.lint_worker.isRunning():
            self.lint_worker.stop()
        self.executor.shutdown(wait=False, cancel_futures=True)
        super().closeEvent(event)
