import unittest
from unittest.mock import patch

from githooklib import GitHook, GitHookContext, HookResult, CommandExecutor


class TestPreCommit(unittest.TestCase):
    def setUp(self):
        self.mock_context = GitHookContext(
            hook_name="pre-commit", stdin_lines=["git commit"]
        )
        self.mock_patcher = patch(
            "githooklib.git_hook.GitHookContext.from_stdin",
            return_value=self.mock_context,
        )
        self.mock_patcher.start()
        self.addCleanup(self.mock_patcher.stop)

    def test_print(self):

        class PreCommit(GitHook):
            @classmethod
            def get_hook_name(cls) -> str:
                return "pre-commit"

            def execute(self, context: GitHookContext) -> HookResult:
                return HookResult(success=True)

        exit_code = PreCommit().run()
        self.assertEqual(exit_code, 0)
