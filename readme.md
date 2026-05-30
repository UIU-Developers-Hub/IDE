# PyDitor

A lightweight Python IDE built with **PyQt6**, inspired by the VS Code layout: activity bar, sidebar panels, tabbed editor, integrated terminal, and Git source control.

## Libraries

| Library | Purpose |
|---------|---------|
| **PyQt6** | Desktop UI framework |
| **PyQt6-QScintilla** | Code editor (syntax, margins, breakpoints) |
| **PyQt6-Fluent-Widgets** | Modern controls and dark theme |
| **Ruff** | Linting, formatting, import sorting |
| **Jedi** | Autocompletion and documentation |
| **Pygments** | Syntax highlighting |
| **qtawesome** | Toolbar and activity bar icons |
| **markdown** | Documentation sidebar rendering |

## Features

### Editor

- Tabbed editor with syntax highlighting, bracket matching, and breakpoints
- **Ruff** real-time lint with a **Problems** panel
- **Format document** (Shift+Alt+F) and **organize imports** (Ctrl+Alt+I)
- Jedi autocompletion and documentation sidebar
- Find/replace, go to line, comment toggle, auto-indent
- File watcher — reload when files change on disk
- Session restore (open files and breakpoints)

### Run & debug

- Run / stop the current file (F5 / Shift+F5)
- Run buffer as tests (Ctrl+T)
- **pdb** debugger: start, continue, step

### VS Code–style UI

- **Activity bar** — Explorer, Search, Source Control, Run, Settings
- **Explorer** — open folders, browse project tree
- **Search** — find in files across the workspace
- **Source Control** — status, stage, commit, push, pull, clone, publish to GitHub
- **Terminal** — integrated shell tabs in the bottom panel
- **Command palette** (Ctrl+Shift+P) and **Quick Open** (Ctrl+P)
- Welcome screen with recent projects and files
- Status bar: project name, Git branch, lint count, cursor position, encoding, Python version

## Keyboard shortcuts

| Action | Shortcut |
|--------|----------|
| New file | Ctrl+N |
| Open file | Ctrl+O |
| Open folder | Ctrl+Shift+O |
| Quick open | Ctrl+P |
| Command palette | Ctrl+Shift+P |
| Save | Ctrl+S |
| Save as | Ctrl+Shift+S |
| Close tab | Ctrl+W |
| Find | Ctrl+F |
| Replace | Ctrl+H |
| Go to line | Ctrl+G |
| Toggle comment | Ctrl+/ |
| Format document | Shift+Alt+F |
| Organize imports | Ctrl+Alt+I |
| Run | F5 |
| Stop | Shift+F5 |
| Run buffer (tests) | Ctrl+T |
| Explorer | Ctrl+Shift+E |
| Search in files | Ctrl+Shift+F |
| Source control | Ctrl+Shift+G |
| Git commit | Ctrl+Enter |
| Git push | Ctrl+Shift+K |
| Git pull | Ctrl+Shift+U |
| Toggle terminal | Ctrl+` |
| New terminal | Ctrl+Shift+` |
| Toggle side bar | Ctrl+B |
| Toggle bottom panel | Ctrl+J |
| Problems panel | Ctrl+Shift+M |
| Documentation sidebar | Ctrl+Shift+I |
| Lint report | Ctrl+Shift+L |

See **File**, **Edit**, **Run**, **Debug**, **Git**, and **View** menus for the full list.

## Setup

Requires **Python 3.10+**.

```sh
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
python main.py
```

User settings, recent files, and session data are stored under `data/` (gitignored).

## Project layout

```
PyDitor/
├── main.py           # Application entry point
├── core/             # Run, debug, lint, format, Git services
├── ui/               # Main window, editor, panels, theme
├── tests/            # Unit tests
└── data/             # Local runtime data (not committed)
```

## Tests

```sh
python -m unittest discover -s tests
```

## License

MIT — see [LICENSE](LICENSE).
