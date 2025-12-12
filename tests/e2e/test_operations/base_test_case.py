import re
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Generator, Dict

from githooklib import CommandExecutor, get_logger, CommandResult
from tests.base_test_case import BaseTestCase
from tests.utils import PathUtils


def to_snake_case(name: str) -> str:
    s = re.sub(r"[\-\s]+", "_", str(name))
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.lower()


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
            success,
            result.success,
            f"Expected command to succeed, but failed with\nstdout: {result.stdout}\nstderr: {result.stderr}",
        )
        self.assertEqual(exit_code, result.exit_code)
        self.logger.debug("STDOUT: %s", result.stdout)
        return result

    def list(self, cwd: Optional[Path] = None) -> List[str]:
        return [
            hook.strip()[2:]
            for hook in self.githooklib(["list"], cwd=cwd).stdout.splitlines()[1:-1]
        ]

    def show(self, cwd: Optional[Path] = None) -> List[str]:
        return [
            hook.strip()[2:].strip()
            for hook in self.githooklib(["show"], cwd=cwd).stdout.splitlines()[1:-1]
        ]

    @contextmanager
    def new_temp_project(
        self, hook_setup: Optional[Dict[str, str]] = None
    ) -> Generator[Path]:
        if hook_setup is None:
            hook_setup = {
                name: self.create_basic_hook(name)
                for name in [
                    "pre-commit",
                    "pre-push",
                ]
            }
        with tempfile.TemporaryDirectory(delete=True) as temp_dir_str:
            root = Path(temp_dir_str)
            self.git(["init"], cwd=root)
            (root / "githooks").mkdir(parents=True)
            for hook, content in hook_setup.items():
                (root / "githooks" / f"{to_snake_case(hook)}.py").write_text(content)
            yield root

    @staticmethod
    def get_default_print(hook: str) -> str:
        return f"I am {hook}, Hi!"

    @staticmethod
    def create_basic_hook(hook_name: str, print_content: Optional[str] = None) -> str:
        if print_content is None:
            print_content = OperationsBaseTestCase.get_default_print(hook_name)
        class_name = "".join(
            word.capitalize() for word in hook_name.replace("-", "_").split("_")
        )
        return f"""import sys

from githooklib import GitHook, GitHookContext, HookResult


class {class_name}(GitHook):
    @classmethod
    def get_hook_name(cls) -> str:
        return "{hook_name}"

    def execute(self, context: GitHookContext) -> HookResult:
        self.logger.info("{print_content}")
        return HookResult(success=True, message="Hook executed successfully")


__all__ = ["{class_name}"]

if __name__ == "__main__":
    sys.exit({class_name}().run())
"""


__all__ = ["OperationsBaseTestCase"]
