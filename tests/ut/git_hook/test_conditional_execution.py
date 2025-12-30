import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from githooklib import GitHook, GitHookContext, HookResult
from githooklib.gateways import GitGateway
from tests.base_test_case import BaseTestCase


class HookWithoutPatterns(GitHook):
    @classmethod
    def get_hook_name(cls) -> str:
        return "test-hook"

    @classmethod
    def get_file_patterns(cls):
        return None

    def execute(self, context: GitHookContext) -> HookResult:
        return HookResult(success=True, message="Executed")


class HookWithPatterns(GitHook):
    @classmethod
    def get_hook_name(cls) -> str:
        return "test-hook-patterns"

    @classmethod
    def get_file_patterns(cls):
        return ["*.py", "src/**/*.ts"]

    def execute(self, context: GitHookContext) -> HookResult:
        return HookResult(success=True, message="Executed")


class HookWithEmptyPatterns(GitHook):
    @classmethod
    def get_hook_name(cls) -> str:
        return "test-hook-empty-patterns"

    @classmethod
    def get_file_patterns(cls):
        return []

    def execute(self, context: GitHookContext) -> HookResult:
        return HookResult(success=True, message="Executed")


class PreCommitHookWithPatterns(GitHook):
    @classmethod
    def get_hook_name(cls) -> str:
        return "pre-commit"

    @classmethod
    def get_file_patterns(cls):
        return ["*.py"]

    def execute(self, context: GitHookContext) -> HookResult:
        return HookResult(success=True, message="Executed")


class PrePushHookWithPatterns(GitHook):
    @classmethod
    def get_hook_name(cls) -> str:
        return "pre-push"

    @classmethod
    def get_file_patterns(cls):
        return ["*.py"]

    def execute(self, context: GitHookContext) -> HookResult:
        return HookResult(success=True, message="Executed")


class TestConditionalExecution(BaseTestCase):
    def setUp(self):
        self.hook_without_patterns = HookWithoutPatterns()
        self.hook_with_patterns = HookWithPatterns()
        self.hook_with_empty_patterns = HookWithEmptyPatterns()
        self.pre_commit_hook = PreCommitHookWithPatterns()
        self.pre_push_hook = PrePushHookWithPatterns()

    def test_hook_without_patterns_always_runs(self):
        context = GitHookContext("test-hook", [])
        should_run = self.hook_without_patterns._should_run_based_on_patterns(context)
        self.assertTrue(should_run)

    def test_hook_with_empty_patterns_list_always_runs(self):
        context = GitHookContext("test-hook-empty-patterns", [])
        should_run = self.hook_with_empty_patterns._should_run_based_on_patterns(
            context
        )
        self.assertTrue(should_run)

    def test_hook_with_patterns_no_changed_files_does_not_run(self):
        context = GitHookContext("test-hook-patterns", [])
        with patch.object(GitGateway, "get_cached_index_files", return_value=[]):
            with patch.object(GitGateway, "get_all_modified_files", return_value=[]):
                should_run = self.hook_with_patterns._should_run_based_on_patterns(
                    context
                )
                self.assertFalse(should_run)

    def test_hook_with_patterns_matching_file_runs(self):
        context = GitHookContext("test-hook-patterns", [])
        with patch.object(GitGateway, "get_cached_index_files", return_value=[]):
            with patch.object(
                GitGateway, "get_all_modified_files", return_value=["test.py"]
            ):
                should_run = self.hook_with_patterns._should_run_based_on_patterns(
                    context
                )
                self.assertTrue(should_run)

    def test_hook_with_patterns_non_matching_file_does_not_run(self):
        context = GitHookContext("test-hook-patterns", [])
        with patch.object(GitGateway, "get_cached_index_files", return_value=[]):
            with patch.object(
                GitGateway, "get_all_modified_files", return_value=["test.txt"]
            ):
                should_run = self.hook_with_patterns._should_run_based_on_patterns(
                    context
                )
                self.assertFalse(should_run)

    def test_hook_with_patterns_multiple_files_one_matches_runs(self):
        context = GitHookContext("test-hook-patterns", [])
        with patch.object(GitGateway, "get_cached_index_files", return_value=[]):
            with patch.object(
                GitGateway,
                "get_all_modified_files",
                return_value=["test.txt", "test.py", "other.txt"],
            ):
                should_run = self.hook_with_patterns._should_run_based_on_patterns(
                    context
                )
                self.assertTrue(should_run)

    def test_hook_with_patterns_glob_pattern_matching(self):
        context = GitHookContext("test-hook-patterns", [])
        with patch.object(GitGateway, "get_cached_index_files", return_value=[]):
            with patch.object(
                GitGateway,
                "get_all_modified_files",
                return_value=["src/components/App.ts"],
            ):
                should_run = self.hook_with_patterns._should_run_based_on_patterns(
                    context
                )
                self.assertTrue(should_run)

    def test_pre_commit_hook_uses_staged_files(self):
        context = GitHookContext("pre-commit", [])
        with patch.object(
            GitGateway, "get_cached_index_files", return_value=["test.py"]
        ) as mock_staged:
            with patch.object(GitGateway, "get_all_modified_files") as mock_all:
                should_run = self.pre_commit_hook._should_run_based_on_patterns(context)
                self.assertTrue(should_run)
                mock_staged.assert_called_once()
                mock_all.assert_not_called()

    def test_pre_commit_hook_no_matching_staged_files_does_not_run(self):
        context = GitHookContext("pre-commit", [])
        with patch.object(
            GitGateway, "get_cached_index_files", return_value=["test.txt"]
        ):
            should_run = self.pre_commit_hook._should_run_based_on_patterns(context)
            self.assertFalse(should_run)

    def test_pre_push_hook_uses_changed_files_for_push(self):
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
            return_value=["test.py"],
        ) as mock_push:
            with patch.object(GitGateway, "get_all_modified_files") as mock_all:
                should_run = self.pre_push_hook._should_run_based_on_patterns(context)
                self.assertTrue(should_run)
                mock_push.assert_called_once_with("refs/heads/main", "refs/heads/main")
                mock_all.assert_not_called()

    def test_pre_push_hook_no_refs_falls_back_to_staged_then_all_changed_files(self):
        context = GitHookContext("pre-push", [], stdin_lines=[])
        with patch.object(
            GitGateway, "get_cached_index_files", return_value=[]
        ) as mock_staged:
            with patch.object(
                GitGateway, "get_all_modified_files", return_value=["test.py"]
            ) as mock_all:
                with patch.object(
                    GitGateway, "get_diff_files_between_refs"
                ) as mock_push:
                    should_run = self.pre_push_hook._should_run_based_on_patterns(
                        context
                    )
                    self.assertTrue(should_run)
                    mock_staged.assert_called_once()
                    mock_all.assert_called_once()
                    mock_push.assert_not_called()

    def test_context_get_changed_files_with_refs_uses_push_diff(self):
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
            return_value=["file1.py"],
        ) as mock_push:
            files = context.get_changed_files()
            self.assertEqual(files, ["file1.py"])
            mock_push.assert_called_once_with("refs/heads/main", "refs/heads/main")

    def test_context_get_changed_files_no_refs_uses_staged_then_all(self):
        context = GitHookContext("pre-commit", [])
        with patch.object(
            GitGateway, "get_cached_index_files", return_value=["file1.py", "file2.txt"]
        ) as mock_staged:
            with patch.object(GitGateway, "get_all_modified_files") as mock_all:
                files = context.get_changed_files()
                self.assertEqual(files, ["file1.py", "file2.txt"])
                mock_staged.assert_called_once()
                mock_all.assert_not_called()

    def test_context_get_changed_files_no_staged_falls_back_to_all(self):
        context = GitHookContext("pre-commit", [])
        with patch.object(
            GitGateway, "get_cached_index_files", return_value=[]
        ) as mock_staged:
            with patch.object(
                GitGateway, "get_all_modified_files", return_value=["file1.py"]
            ) as mock_all:
                files = context.get_changed_files()
                self.assertEqual(files, ["file1.py"])
                mock_staged.assert_called_once()
                mock_all.assert_called_once()

    def test_run_skips_execution_when_patterns_dont_match(self):
        context = GitHookContext("test-hook-patterns", [])
        with patch.object(GitHookContext, "from_argv", return_value=context):
            with patch.object(GitGateway, "get_cached_index_files", return_value=[]):
                with patch.object(
                    GitGateway, "get_all_modified_files", return_value=["test.txt"]
                ):
                    with patch.object(
                        self.hook_with_patterns, "execute"
                    ) as mock_execute:
                        with patch.object(
                            self.hook_with_patterns.logger, "info"
                        ) as mock_info:
                            with patch.object(
                                self.hook_with_patterns.logger, "debug"
                            ) as mock_debug:
                                with patch.object(
                                    self.hook_with_patterns.logger, "trace"
                                ) as mock_trace:
                                    exit_code = self.hook_with_patterns.run()
                                    self.assertEqual(exit_code, 0)
                                    mock_execute.assert_not_called()
                                    mock_info.assert_called_once_with(
                                        "Hook '%s' skipped: no changed files match the specified patterns",
                                        "test-hook-patterns",
                                    )
                                    mock_debug.assert_any_call(
                                        "Hook '%s' skipped: patterns checked: %s",
                                        "test-hook-patterns",
                                        ["*.py", "src/**/*.ts"],
                                    )
                                    mock_trace.assert_any_call(
                                        "Hook '%s' skipped: changed files checked: %s",
                                        "test-hook-patterns",
                                        ["test.txt"],
                                    )

    def test_run_executes_when_patterns_match(self):
        context = GitHookContext("test-hook-patterns", [])
        with patch.object(GitHookContext, "from_argv", return_value=context):
            with patch.object(GitGateway, "get_cached_index_files", return_value=[]):
                with patch.object(
                    GitGateway, "get_all_modified_files", return_value=["test.py"]
                ):
                    exit_code = self.hook_with_patterns.run()
                    self.assertEqual(exit_code, 0)

    def test_run_executes_when_no_patterns_defined(self):
        context = GitHookContext("test-hook", [])
        with patch.object(GitHookContext, "from_argv", return_value=context):
            exit_code = self.hook_without_patterns.run()
            self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
