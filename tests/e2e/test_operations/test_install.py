import sys
import tempfile
import unittest
from pathlib import Path

from tests.utils import PathUtils
from .base_test_case import OperationsBaseTestCase

TEST_HOOK = """
class TestHookForInstall(GitHook):
    @property
    def hook_name(self) -> str:
        return "test-hook"

    def execute(self, context: GitHookContext) -> HookResult:
        return HookResult(success=True, message="Test hook executed")
"""
PRE_COMMIT_HOOK = """
class CustomNamedHookFile(GitHook):
    @property
    def hook_name(self) -> str:
        return "pre-commit"

    def execute(self, context: GitHookContext) -> HookResult:
        return HookResult(success=True, message="Custom named hook executed")
"""


class TestInstallE2E(OperationsBaseTestCase):

    def test_install_creates_hook_script_with_hook_name(self):
        with tempfile.TemporaryDirectory() as root:
            root: Path = PathUtils.normalize(root)  # type: ignore[no-redef]
            self.git(["init"], cwd=root)
            self.get_githooks_folder(root).mkdir(parents=True)
            self.save_hook_to(
                TEST_HOOK, self.get_githooks_folder(root) / "test_hook.py"
            )
            result = self.githooklib(["list"], cwd=root)
            self.assertIn("test-hook", result.stdout)

            self.githooklib(["install", "test-hook"], cwd=root)

            hook_delegate_path = root / ".git" / "hooks" / "test-hook"
            self.assertTrue(hook_delegate_path.exists())


if __name__ == "__main__":
    unittest.main()
