import sys
from typing import Optional, List

from githooklib import GitHook, GitHookContext, HookResult
from githooklib.command import CommandExecutor, CommandResult
from githooklib import get_logger

logger = get_logger(__name__, "pre-commit")


def _black_exists(command_executor: CommandExecutor) -> bool:
    check_result = command_executor.run(["python", "-m", "black", "--version"])
    if check_result.exit_code == 127:
        return False
    if not check_result.success and "No module named" in check_result.stderr:
        return False
    return True


def _get_modified_python_files(command_executor: CommandExecutor) -> List[str]:
    result = command_executor.run(["git", "diff", "--name-only"])
    if not result.success:
        return []
    modified_files = [
        line.strip() for line in result.stdout.strip().split("\n") if line.strip()
    ]
    return [f for f in modified_files if f.endswith(".py")]


def _stage_files(command_executor: CommandExecutor, files: List[str]) -> CommandResult:
    return command_executor.run(["git", "add"] + files)


class BlackFormatterPreCommit(GitHook):
    @classmethod
    def get_file_patterns(cls) -> Optional[List[str]]:
        return ["*.py"]

    @classmethod
    def get_hook_name(cls) -> str:
        return "pre-commit"

    def __init__(
        self,
        stage_changes: bool = True,
    ) -> None:
        super().__init__()
        self.stage_changes = stage_changes

    def execute(self, context: GitHookContext) -> HookResult:
        if not _black_exists(self.command_executor):
            logger.warning("Black tool not found. Skipping code formatting check.")
            return HookResult(
                success=True,
                message="Black tool not found. Check skipped.",
            )

        logger.info("Reformatting code with black...")
        result = self.command_executor.run(["python", "-m", "black", "."])

        if not result.success:
            logger.error("Black formatting failed.")
            if result.stderr:
                logger.error(result.stderr)
            return HookResult(
                success=False,
                message="Black formatting failed.",
                exit_code=1,
            )

        if self.stage_changes:
            modified_files = _get_modified_python_files(self.command_executor)
            if modified_files:
                logger.info(f"Staging {len(modified_files)} formatted file(s)...")
                staging_result = _stage_files(self.command_executor, modified_files)
                if not staging_result.success:
                    logger.error("Failed to stage formatted files.")
                    return HookResult(
                        success=False,
                        message="Failed to stage formatted files.",
                        exit_code=1,
                    )
                logger.success("Formatted files staged successfully!")

        logger.success("Code reformatted successfully!")
        return HookResult(success=True, message="Pre-commit checks passed!")


__all__ = ["BlackFormatterPreCommit"]


if __name__ == "__main__":
    sys.exit(BlackFormatterPreCommit().run())
