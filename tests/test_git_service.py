import unittest

from core.git_service import GitService


class TestGitService(unittest.TestCase):
    def test_not_a_repo(self):
        svc = GitService(".")
        if svc.is_git_installed():
            branch = svc.current_branch()
            self.assertTrue(branch is None or isinstance(branch, str))

    def test_porcelain_empty_when_no_repo(self):
        svc = GitService(".")
        if not svc.is_repo():
            self.assertEqual(svc.status_changes(), [])


if __name__ == "__main__":
    unittest.main()
