import sys
from pathlib import Path
from typing import List, Optional

from githooklib import CommandExecutor, get_logger, CommandResult
from tests.base_test_case import BaseTestCase
from tests.utils import PathUtils


class OperationsBaseTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.executor = CommandExecutor()
        self.print_cwd()

    def get_installed_hooks_path(self, root: Path) -> Path:
        return root / ".git" / "hooks"

    def get_githooks_folder(self, root: Path) -> Path:
        return root / "githooks"

    def save_hook_to(self, code: str, path: Path) -> None:
        with open(str(path), "w", encoding="utf8") as f:
            f.write(code)

    def print_cwd(self) -> None:
        self.logger.debug("CWD: " + str(PathUtils.get_cwd()))

    def git(
        self,
        cmd: List[str],
        success: bool = True,
        exit_code: int = 0,
        cwd: Optional[Path] = None,
    ) -> CommandResult:
        result = self.executor.run(["git"] + cmd, cwd=cwd)
        self.assertEqual(
            success, result.success, f"Expected command to succeed, but failed"
        )
        self.assertEqual(exit_code, result.exit_code)
        self.logger.debug("STDOUT: " + result.stdout)
        return result

    def githooklib(
        self,
        cmd: List[str],
        success: bool = True,
        exit_code: int = 0,
        cwd: Optional[Path] = PathUtils.get_project_root(),
    ) -> CommandResult:
        result = self.executor.run([sys.executable, "-m", "githooklib"] + cmd, cwd=cwd)
        self.assertEqual(
            success, result.success, "Expected command to succeed, but failed"
        )
        self.assertEqual(exit_code, result.exit_code)
        self.logger.debug("STDOUT: " + result.stdout)
        return result


__all__ = ["OperationsBaseTestCase"]
