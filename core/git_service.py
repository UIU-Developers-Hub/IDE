"""Git and GitHub CLI helpers (subprocess — no extra deps)."""

import logging
import os
import shutil
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GitFileChange:
    path: str
    status: str  # M, A, D, ?, U, etc.


class GitService:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def is_repo(self) -> bool:
        return os.path.isdir(os.path.join(self.repo_path, ".git"))

    def is_git_installed(self) -> bool:
        return shutil.which("git") is not None

    def is_gh_installed(self) -> bool:
        return shutil.which("gh") is not None

    def run_git(self, *args: str) -> tuple[str, str, int]:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return result.stdout, result.stderr, result.returncode
        except (OSError, subprocess.TimeoutExpired) as exc:
            logger.warning("git command failed: %s", exc)
            return "", str(exc), 1

    def run_gh(self, *args: str) -> tuple[str, str, int]:
        try:
            result = subprocess.run(
                ["gh", *args],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return result.stdout, result.stderr, result.returncode
        except (OSError, subprocess.TimeoutExpired) as exc:
            logger.warning("gh command failed: %s", exc)
            return "", str(exc), 1

    def current_branch(self) -> str | None:
        if not self.is_repo():
            return None
        out, _, code = self.run_git("branch", "--show-current")
        branch = out.strip()
        return branch if code == 0 and branch else None

    def status_changes(self) -> list[GitFileChange]:
        if not self.is_repo():
            return []
        out, _, code = self.run_git("status", "--porcelain")
        if code != 0:
            return []

        changes = []
        for line in out.splitlines():
            if len(line) < 4:
                continue
            status = line[:2].strip() or line[0]
            path = line[3:].strip().strip('"')
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            changes.append(GitFileChange(path=path, status=status or "?"))
        return changes

    def stage(self, path: str) -> tuple[bool, str]:
        _, err, code = self.run_git("add", "--", path)
        return code == 0, err.strip()

    def stage_all(self) -> tuple[bool, str]:
        _, err, code = self.run_git("add", "-A")
        return code == 0, err.strip()

    def unstage(self, path: str) -> tuple[bool, str]:
        _, err, code = self.run_git("restore", "--staged", "--", path)
        return code == 0, err.strip()

    def commit(self, message: str) -> tuple[bool, str]:
        _, err, code = self.run_git("commit", "-m", message)
        return code == 0, err.strip() or "Committed."

    def push(self) -> tuple[bool, str]:
        out, err, code = self.run_git("push")
        msg = (out + err).strip()
        return code == 0, msg or ("Pushed." if code == 0 else "Push failed.")

    def pull(self) -> tuple[bool, str]:
        out, err, code = self.run_git("pull")
        msg = (out + err).strip()
        return code == 0, msg or ("Pulled." if code == 0 else "Pull failed.")

    def init_repo(self) -> tuple[bool, str]:
        _, err, code = self.run_git("init")
        return code == 0, err.strip() or "Repository initialized."

    def clone(self, url: str, destination: str) -> tuple[bool, str]:
        try:
            result = subprocess.run(
                ["git", "clone", url, destination],
                capture_output=True,
                text=True,
                timeout=300,
            )
            msg = (result.stdout + result.stderr).strip()
            return result.returncode == 0, msg
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, str(exc)

    def remote_url(self) -> str | None:
        out, _, code = self.run_git("remote", "get-url", "origin")
        url = out.strip()
        return url if code == 0 and url else None

    def github_web_url(self) -> str | None:
        url = self.remote_url()
        if not url:
            return None
        if url.startswith("git@github.com:"):
            slug = url.removeprefix("git@github.com:").removesuffix(".git")
            return f"https://github.com/{slug}"
        if "github.com" in url:
            return url.removesuffix(".git")
        return None

    def gh_auth_status(self) -> tuple[bool, str]:
        if not self.is_gh_installed():
            return False, "GitHub CLI (gh) is not installed."
        _, err, code = self.run_gh("auth", "status")
        return code == 0, err.strip()

    def gh_open_repo(self) -> tuple[bool, str]:
        out, err, code = self.run_gh("repo", "view", "--web")
        return code == 0, (out + err).strip()

    def gh_create_repo(self, name: str, private: bool = False) -> tuple[bool, str]:
        args = ["repo", "create", name, "--source", ".", "--remote", "origin"]
        if private:
            args.append("--private")
        else:
            args.append("--public")
        args.extend(["--push"])
        out, err, code = self.run_gh(*args)
        return code == 0, (out + err).strip()
