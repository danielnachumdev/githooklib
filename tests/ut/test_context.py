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

    def test_from_argv_pre_push_reads_stdin(self):
        with patch("sys.argv", ["script"]):
            stdin_content = "refs/heads/main refs/remotes/origin/main refs/heads/main refs/remotes/origin/main\n"
            with patch("sys.stdin", StringIO(stdin_content)):
                context = GitHookContext.from_argv("pre-push")
                self.assertEqual(context.hook_name, "pre-push")
                self.assertEqual(len(context.stdin_lines), 1)
                self.assertEqual(
                    context.stdin_lines[0],
                    "refs/heads/main refs/remotes/origin/main refs/heads/main refs/remotes/origin/main",
                )

    def test_from_argv_pre_push_empty_stdin(self):
        with patch("sys.argv", ["script"]):
            with patch("sys.stdin", StringIO("")):
                context = GitHookContext.from_argv("pre-push")
                self.assertEqual(context.hook_name, "pre-push")
                self.assertEqual(len(context.stdin_lines), 0)

    def test_from_argv_pre_push_skips_stdin_when_run_via_cli(self):
        with patch("sys.argv", ["githooklib", "run", "pre-push"]):
            stdin_content = "refs/heads/main refs/remotes/origin/main refs/heads/main refs/remotes/origin/main\n"
            with patch("sys.stdin", StringIO(stdin_content)):
                context = GitHookContext.from_argv("pre-push")
                self.assertEqual(context.hook_name, "pre-push")
                self.assertEqual(len(context.stdin_lines), 0)

    def test_parse_pre_push_refs_from_stdin_with_valid_input(self):
        context = GitHookContext(
            "pre-push",
            [],
            stdin_lines=[
                "refs/heads/main refs/remotes/origin/main refs/heads/main refs/remotes/origin/main"
            ],
        )
        remote_ref, local_ref = context._parse_pre_push_refs_from_stdin()
        self.assertEqual(local_ref, "refs/heads/main")
        self.assertEqual(remote_ref, "refs/heads/main")

    def test_parse_pre_push_refs_from_stdin_with_empty_input(self):
        context = GitHookContext("pre-push", [], stdin_lines=[])
        remote_ref, local_ref = context._parse_pre_push_refs_from_stdin()
        self.assertIsNone(remote_ref)
        self.assertIsNone(local_ref)

    def test_read_stdin_lines_with_content(self):
        stdin_content = "line1\nline2\nline3\n"
        with patch("sys.stdin", StringIO(stdin_content)):
            lines = GitHookContext._read_stdin_lines()
            self.assertEqual(lines, ["line1", "line2", "line3"])

    def test_read_stdin_lines_with_empty_input(self):
        with patch("sys.stdin", StringIO("")):
            lines = GitHookContext._read_stdin_lines()
            self.assertEqual(lines, [])

    def test_read_stdin_lines_handles_exception(self):
        with patch("sys.stdin.read", side_effect=Exception("Read error")):
            lines = GitHookContext._read_stdin_lines()
            self.assertEqual(lines, [])

    def test_from_argv_reads_stdin_for_all_hooks_with_stdin(self):
        for hook_name in ["pre-push", "pre-receive", "post-receive"]:
            with self.subTest(hook_name=hook_name):
                with patch("sys.argv", ["script"]):
                    stdin_content = "line1\nline2\n"
                    with patch("sys.stdin", StringIO(stdin_content)):
                        context = GitHookContext.from_argv(hook_name)
                        self.assertEqual(context.hook_name, hook_name)
                        self.assertEqual(len(context.stdin_lines), 2)
                        self.assertEqual(context.stdin_lines, ["line1", "line2"])

    def test_get_changed_files_with_pre_push_stdin_uses_diff(self):
        context = GitHookContext(
            "pre-push",
            [],
            stdin_lines=[
                "refs/heads/main refs/remotes/origin/main refs/heads/main refs/remotes/origin/main"
            ],
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
                    mock_diff.assert_called_once_with(
                        "refs/heads/main", "refs/heads/main"
                    )
                    mock_cached.assert_not_called()
                    mock_all.assert_not_called()

    def test_get_changed_files_with_pre_push_no_stdin_falls_back(self):
        context = GitHookContext("pre-push", [], stdin_lines=[])
        with patch.object(
            GitGateway, "get_cached_index_files", return_value=["file1.py"]
        ) as mock_cached:
            with patch.object(GitGateway, "get_all_modified_files") as mock_all:
                with patch.object(
                    GitGateway, "get_diff_files_between_refs"
                ) as mock_diff:
                    files = context.get_changed_files()
                    self.assertEqual(files, ["file1.py"])
                    mock_cached.assert_called_once()
                    mock_all.assert_not_called()
                    mock_diff.assert_not_called()

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
