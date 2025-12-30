import sys
from enum import Enum
from typing import Optional, List

from githooklib import GitHook, GitHookContext, HookResult
from githooklib.command import CommandExecutor, CommandResult
from githooklib import get_logger

logger = get_logger(__name__, "pre-commit")


def _black_exists(command_executor: CommandExecutor) -> bool:
    check_result = command_executor.python_module("black", ["--version"])
    if check_result.exit_code == 127:
        return False
    if not check_result.success and "No module named" in check_result.stderr:
        return False
    return True


def _get_tracked_python_files(command_executor: CommandExecutor) -> List[str]:
    result = command_executor.run(["git", "diff", "--name-only"])
    if not result.success:
        return []
    modified_files = [
        line.strip() for line in result.stdout.strip().split("\n") if line.strip()
    ]
    return [f for f in modified_files if f.endswith(".py")]


def _get_previously_staged_python_files(
    command_executor: CommandExecutor,
) -> List[str]:
    result = command_executor.run(["git", "diff", "--name-only", "--cached"])
    if not result.success:
        return []
    staged_files = [
        line.strip() for line in result.stdout.strip().split("\n") if line.strip()
    ]
    return [f for f in staged_files if f.endswith(".py")]


def _stage_files(command_executor: CommandExecutor, files: List[str]) -> CommandResult:
    return command_executor.run(["git", "add"] + files)


class BlackFormatterPreCommit(GitHook):
    class StagePolicy(str, Enum):
        ALL = "all_tracked"
        CHANGED_FILES_ONLY = "previously_staged"

    @classmethod
    def get_file_patterns(cls) -> Optional[List[str]]:
        return ["*.py"]

    @classmethod
    def get_hook_name(cls) -> str:
        return "pre-commit"

    def __init__(
        self,
        stage_policy: "BlackFormatterPreCommit.StagePolicy" = StagePolicy.CHANGED_FILES_ONLY,
    ) -> None:
        super().__init__()
        self.stage_policy = stage_policy

    def execute(self, context: GitHookContext) -> HookResult:
        if not _black_exists(self.command_executor):
            logger.warning("Black tool not found. Skipping code formatting check.")
            return HookResult(
                success=True,
                message="Black tool not found. Check skipped.",
            )

        logger.info("Reformatting code with black...")
        result = self.command_executor.python_module("black", ["."])

        if not result.success:
            logger.error("Black formatting failed.")
            if result.stderr:
                logger.error(result.stderr)
            return HookResult(
                success=False,
                message="Black formatting failed.",
                exit_code=1,
            )

        tracked_files = _get_tracked_python_files(self.command_executor)
        files_to_stage = tracked_files
        if self.stage_policy == self.StagePolicy.CHANGED_FILES_ONLY:
            staged_files = _get_previously_staged_python_files(self.command_executor)
            files_to_stage = [file for file in tracked_files if file in staged_files]
        if files_to_stage:
            logger.info("Staging %d formatted file(s)...", len(files_to_stage))
            staging_result = _stage_files(self.command_executor, files_to_stage)
            if not staging_result.success:
                logger.error("Failed to stage formatted files.")
                return HookResult(
                    success=False,
                    message="Failed to stage formatted files.",
                    exit_code=1,
                )
            logger.success("Formatted files staged successfully!")
        return HookResult(success=True, message="Pre-commit checks passed!")


StagePolicy = BlackFormatterPreCommit.StagePolicy

__all__ = ["BlackFormatterPreCommit", "StagePolicy"]


if __name__ == "__main__":
    hook = BlackFormatterPreCommit()
    sys.exit(hook.run())
