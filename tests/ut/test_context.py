import sys
import unittest
from io import StringIO
from unittest.mock import patch, MagicMock

from githooklib.context import GitHookContext
from githooklib.gateways.git_gateway import GitGateway
from tests.base_test_case import BaseTestCase


class TestGitHookContext(BaseTestCase):
    def test_from_argv_creates_context(self):
        with patch("sys.argv", ["script", "arg1", "arg2"]):
            context = GitHookContext.from_argv("pre-commit")
            self.assertEqual(context.hook_name, "pre-commit")
            self.assertEqual(context.argv, ["script", "arg1", "arg2"])

    def test_from_argv_pre_push_parses_stdin(self):
        with patch("sys.argv", ["script"]):
            stdin_content = "refs/heads/main refs/remotes/origin/main refs/heads/main refs/remotes/origin/main\n"
            with patch("sys.stdin", StringIO(stdin_content)):
                context = GitHookContext.from_argv("pre-push")
                self.assertEqual(context.hook_name, "pre-push")
                self.assertIsNotNone(context.remote_ref)
                self.assertIsNotNone(context.local_ref)

    def test_from_argv_pre_push_empty_stdin(self):
        with patch("sys.argv", ["script"]):
            with patch("sys.stdin", StringIO("")):
                context = GitHookContext.from_argv("pre-push")
                self.assertEqual(context.hook_name, "pre-push")
                self.assertIsNone(context.remote_ref)
                self.assertIsNone(context.local_ref)

    def test_parse_pre_push_stdin_with_valid_input(self):
        stdin_content = "refs/heads/main refs/remotes/origin/main refs/heads/main refs/remotes/origin/main\n"
        with patch("sys.stdin", StringIO(stdin_content)):
            remote_ref, local_ref = GitHookContext._parse_pre_push_stdin()
            self.assertEqual(local_ref, "refs/heads/main")
            self.assertEqual(remote_ref, "refs/heads/main")

    def test_parse_pre_push_stdin_with_empty_input(self):
        with patch("sys.stdin", StringIO("")):
            remote_ref, local_ref = GitHookContext._parse_pre_push_stdin()
            self.assertIsNone(remote_ref)
            self.assertIsNone(local_ref)

    def test_parse_pre_push_stdin_handles_exception(self):
        with patch("sys.stdin.read", side_effect=Exception("Read error")):
            remote_ref, local_ref = GitHookContext._parse_pre_push_stdin()
            self.assertIsNone(remote_ref)
            self.assertIsNone(local_ref)

    def test_get_changed_files_with_refs_uses_diff(self):
        context = GitHookContext(
            "pre-push", [], remote_ref="origin/main", local_ref="refs/heads/main"
        )
        with patch.object(
            GitGateway,
            "get_diff_files_between_refs",
            return_value=["file1.py", "file2.py"],
        ) as mock_diff:
            with patch.object(GitGateway, "get_cached_index_files") as mock_cached:
                with patch.object(GitGateway, "get_all_modified_files") as mock_all:
                    files = context.get_changed_files()
                    self.assertEqual(files, ["file1.py", "file2.py"])
                    mock_diff.assert_called_once_with("origin/main", "refs/heads/main")
                    mock_cached.assert_not_called()
                    mock_all.assert_not_called()

    def test_get_changed_files_without_refs_uses_cached_index(self):
        context = GitHookContext("pre-commit", [])
        with patch.object(
            GitGateway, "get_cached_index_files", return_value=["file1.py"]
        ) as mock_cached:
            with patch.object(GitGateway, "get_all_modified_files") as mock_all:
                files = context.get_changed_files()
                self.assertEqual(files, ["file1.py"])
                mock_cached.assert_called_once()
                mock_all.assert_not_called()

    def test_get_changed_files_falls_back_to_all_modified(self):
        context = GitHookContext("pre-commit", [])
        with patch.object(GitGateway, "get_cached_index_files", return_value=[]):
            with patch.object(
                GitGateway, "get_all_modified_files", return_value=["file1.py"]
            ) as mock_all:
                files = context.get_changed_files()
                self.assertEqual(files, ["file1.py"])
                mock_all.assert_called_once()


if __name__ == "__main__":
    unittest.main()
