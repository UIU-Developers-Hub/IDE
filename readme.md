# PyDitor

A lightweight Python IDE built with PyQt6.

## Libraries

| Library | Purpose |
|---------|---------|
| **PyQt6** | Desktop UI |
| **Ruff** | Fast linting, formatting, import sorting |
| **Jedi** | Code completion and documentation |
| **Pygments** | Syntax highlighting |
| **qtawesome** | Font Awesome toolbar icons |
| **qdarkstyle** | Dark theme |

## Features

- Tabbed editor with syntax highlighting, bracket matching, breakpoints
- **Ruff** real-time lint (replaces flake8) — faster, more rules
- **Format document** (Shift+Alt+F) and **organize imports** (Ctrl+Alt+I)
- Jedi autocompletion and documentation sidebar
- Find/replace, go to line, comment toggle, auto-indent
- Run / stop scripts, pdb debugger
- File watcher — reload when files change on disk
- Session restore with breakpoints

## Keyboard shortcuts

| Action | Shortcut |
|--------|----------|
| Format document | Shift+Alt+F |
| Organize imports | Ctrl+Alt+I |
| Run | F5 |
| Stop | Shift+F5 |
| Find | Ctrl+F |
| Lint report | Ctrl+Shift+L |

See Edit and File menus for the full list.

## Setup

```sh
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Tests

```sh
python -m unittest discover -s tests
```

## License

MIT — see [LICENSE](LICENSE).
