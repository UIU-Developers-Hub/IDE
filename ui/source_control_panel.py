import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QSizePolicy, QVBoxLayout, QWidget,
)
from qfluentwidgets import LineEdit, PrimaryPushButton, PushButton

from core.git_service import GitService
from ui.icons_util import icon
from ui.sidebar_common import ElideMiddleDelegate, SIDEBAR_PAD

MAX_CHANGES_SHOWN = 500


def _full_width_btn(button):
    button.setMinimumHeight(28)
    button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    return button


class SourceControlPanel(QWidget):
    """VS Code Source Control — Git + GitHub."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._git = GitService(main_window._project_root)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(SIDEBAR_PAD, 8, SIDEBAR_PAD, 0)
        refresh_btn = PushButton("Refresh")
        refresh_btn.setFixedHeight(26)
        refresh_btn.clicked.connect(self.refresh)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(refresh_btn, 0)
        layout.addWidget(toolbar)

        self.branch_label = QLabel("")
        self.branch_label.setStyleSheet(
            f"color: #858585; padding: 0 {SIDEBAR_PAD}px; font-size: 12px;"
        )
        self.branch_label.setWordWrap(True)
        layout.addWidget(self.branch_label)

        commit_wrap = QWidget()
        commit_layout = QHBoxLayout(commit_wrap)
        commit_layout.setContentsMargins(SIDEBAR_PAD, 0, SIDEBAR_PAD, 0)
        self.commit_input = LineEdit()
        self.commit_input.setPlaceholderText("Commit message")
        self.commit_input.setToolTip("Ctrl+Enter to commit")
        self.commit_input.returnPressed.connect(self.commit)
        commit_layout.addWidget(self.commit_input)
        layout.addWidget(commit_wrap)

        git_grid = QGridLayout()
        git_grid.setContentsMargins(SIDEBAR_PAD, 0, SIDEBAR_PAD, 0)
        git_grid.setHorizontalSpacing(6)
        git_grid.setVerticalSpacing(6)
        self.stage_btn = _full_width_btn(PushButton("Stage All"))
        self.stage_btn.clicked.connect(self.stage_all)
        self.commit_btn = _full_width_btn(PrimaryPushButton("Commit"))
        self.commit_btn.clicked.connect(self.commit)
        self.push_btn = _full_width_btn(PushButton("Push"))
        self.push_btn.setIcon(icon("run"))
        self.push_btn.clicked.connect(self.push)
        self.pull_btn = _full_width_btn(PushButton("Pull"))
        self.pull_btn.clicked.connect(self.pull)
        git_grid.addWidget(self.stage_btn, 0, 0)
        git_grid.addWidget(self.commit_btn, 0, 1)
        git_grid.addWidget(self.push_btn, 1, 0)
        git_grid.addWidget(self.pull_btn, 1, 1)
        layout.addLayout(git_grid)

        gh_grid = QGridLayout()
        gh_grid.setContentsMargins(SIDEBAR_PAD, 0, SIDEBAR_PAD, 0)
        gh_grid.setHorizontalSpacing(6)
        gh_grid.setVerticalSpacing(6)
        self.gh_clone_btn = _full_width_btn(PushButton("Clone"))
        self.gh_clone_btn.clicked.connect(self.clone_repo)
        self.gh_init_btn = _full_width_btn(PushButton("Init"))
        self.gh_init_btn.setToolTip("Initialize repository")
        self.gh_init_btn.clicked.connect(self.init_repo)
        self.gh_open_btn = _full_width_btn(PushButton("GitHub"))
        self.gh_open_btn.setToolTip("Open on GitHub")
        self.gh_open_btn.clicked.connect(self.open_github)
        self.gh_publish_btn = _full_width_btn(PrimaryPushButton("Publish"))
        self.gh_publish_btn.setToolTip("Publish to GitHub")
        self.gh_publish_btn.clicked.connect(self.publish_github)
        gh_grid.addWidget(self.gh_clone_btn, 0, 0)
        gh_grid.addWidget(self.gh_init_btn, 0, 1)
        gh_grid.addWidget(self.gh_open_btn, 1, 0)
        gh_grid.addWidget(self.gh_publish_btn, 1, 1)
        layout.addLayout(gh_grid)

        self.changes_list = QListWidget()
        self.changes_list.setItemDelegate(ElideMiddleDelegate(self.changes_list))
        self.changes_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.changes_list.setStyleSheet("border: none; padding: 4px 0;")
        self.changes_list.itemDoubleClicked.connect(self._open_change)
        layout.addWidget(self.changes_list, 1)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            f"color: #858585; padding: 4px {SIDEBAR_PAD}px 8px; font-size: 11px;"
        )
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.status_label.setText("Select Source Control to load changes.")

    def set_root(self, path):
        self._git = GitService(path)
        self.changes_list.clear()
        self.branch_label.setText("")
        self.status_label.setText("Select Source Control to load changes.")

    def refresh(self):
        self.changes_list.clear()
        if not self._git.is_git_installed():
            self.branch_label.setText("Git is not installed")
            self.status_label.setText("Install Git from https://git-scm.com")
            return

        if not self._git.is_repo():
            self.branch_label.setText("No repository")
            self.status_label.setText("Initialize or clone a repository to get started.")
            return

        branch = self._git.current_branch() or "HEAD"
        self.branch_label.setText(f"⎇  {branch}")
        self.main_window.update_git_status()

        changes = self._git.status_changes()
        total = len(changes)
        for change in changes[:MAX_CHANGES_SHOWN]:
            prefix = {"M": "M", "A": "A", "D": "D", "?": "U", "U": "!"}.get(
                change.status[:1], change.status[:1]
            )
            item = QListWidgetItem(f"{prefix}  {change.path}")
            item.setToolTip(change.path)
            item.setData(Qt.ItemDataRole.UserRole, change.path)
            self.changes_list.addItem(item)

        if not changes:
            self.status_label.setText("No changes detected.")
        elif total > MAX_CHANGES_SHOWN:
            self.status_label.setText(
                f"Showing {MAX_CHANGES_SHOWN:,} of {total:,} changes. "
                f"Stage All / Commit apply to the full repo."
            )
        else:
            self.status_label.setText(f"{total:,} change(s)")

    def stage_all(self):
        ok, msg = self._git.stage_all()
        self._notify(ok, msg)
        self.refresh()

    def commit(self):
        message = self.commit_input.text().strip()
        if not message:
            self.status_label.setText("Enter a commit message first.")
            return
        ok, msg = self._git.commit(message)
        if ok:
            self.commit_input.clear()
        self._notify(ok, msg)
        self.refresh()

    def push(self):
        ok, msg = self._git.push()
        self._notify(ok, msg)
        self.refresh()

    def pull(self):
        ok, msg = self._git.pull()
        self._notify(ok, msg)
        self.refresh()
        self.main_window.explorer_panel.refresh()

    def init_repo(self):
        ok, msg = self._git.init_repo()
        self._notify(ok, msg)
        self.refresh()

    def clone_repo(self):
        from PyQt6.QtWidgets import QInputDialog

        url, ok = QInputDialog.getText(
            self, "Clone Repository", "GitHub / Git URL:",
        )
        if not ok or not url.strip():
            return
        folder = os.path.basename(url.rstrip("/").replace(".git", "")) or "repo"
        dest, ok = QInputDialog.getText(
            self, "Clone Destination", "Folder name:", text=folder,
        )
        if not ok or not dest.strip():
            return
        dest_path = os.path.join(self.main_window._project_root, dest.strip())
        ok, msg = self._git.clone(url.strip(), dest_path)
        self._notify(ok, msg)
        if ok:
            self.main_window.open_folder_at(dest_path)

    def open_github(self):
        if self._git.is_gh_installed():
            ok, msg = self._git.gh_open_repo()
            if not ok:
                url = self._git.github_web_url()
                if url:
                    import webbrowser
                    webbrowser.open(url)
                    return
            self._notify(ok, msg or "Opened in browser.")
            return
        url = self._git.github_web_url()
        if url:
            import webbrowser
            webbrowser.open(url)
        else:
            self.status_label.setText("No GitHub remote configured.")

    def publish_github(self):
        if not self._git.is_gh_installed():
            self.status_label.setText("Install GitHub CLI: https://cli.github.com")
            return
        authed, msg = self._git.gh_auth_status()
        if not authed:
            self.status_label.setText(f"Run 'gh auth login' first. {msg}")
            return
        from PyQt6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(
            self, "Publish to GitHub", "Repository name:",
            text=os.path.basename(self.main_window._project_root),
        )
        if not ok or not name.strip():
            return
        ok, msg = self._git.gh_create_repo(name.strip())
        self._notify(ok, msg)
        self.refresh()

    def _open_change(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        full = os.path.join(self.main_window._project_root, path)
        if os.path.isfile(full):
            self.main_window._open_file_path(full)

    def _notify(self, ok, msg):
        self.status_label.setText(msg)
        self.main_window.statusBar().showMessage(msg, 4000)
