from typing import Optional

from githooklib import GitHook, GitHookContext, HookResult
from githooklib.command import CommandExecutor, CommandResult


def _is_black_existing(command_executor: CommandExecutor) -> bool:
    check_result = command_executor.run(["python", "-m", "black", "--version"])
    if check_result.exit_code == 127:
        return False
    if not check_result.success and "No module named" in check_result.stderr:
        return False
    return True


def _get_modified_python_files(command_executor: CommandExecutor) -> list[str]:
    result = command_executor.run(["git", "diff", "--name-only"])
    if not result.success:
        return []
    modified_files = [
        line.strip() for line in result.stdout.strip().split("\n") if line.strip()
    ]
    return [f for f in modified_files if f.endswith(".py")]


def _stage_files(command_executor: CommandExecutor, files: list[str]) -> CommandResult:
    return command_executor.run(["git", "add"] + files)


class BlackFormatterPreCommit(GitHook):
    @property
    def hook_name(self) -> str:
        return "pre-commit"

    def __init__(
        self,
        fail_on_change: bool = False,
        stage_changes: bool = True,
        log_level: Optional[int] = None,
    ) -> None:
        super().__init__(log_level=log_level)
        self.fail_on_change = fail_on_change
        self.stage_changes = stage_changes

    def execute(self, context: GitHookContext) -> HookResult:
        if not _is_black_existing(self.command_executor):
            self.logger.warning("Black tool not found. Skipping code formatting check.")
            return HookResult(
                success=True,
                message="Black tool not found. Check skipped.",
            )

        if self.fail_on_change:
            self.logger.info("Checking if code needs formatting with black...")
            check_result = self.command_executor.run(
                ["python", "-m", "black", "--check", "."]
            )
            if not check_result.success:
                self.logger.error("Code is not properly formatted. Commit aborted.")
                if check_result.stdout:
                    self.logger.error(check_result.stdout)
                return HookResult(
                    success=False,
                    message="Code is not properly formatted. Commit aborted.",
                    exit_code=1,
                )
            self.logger.success("Code is properly formatted!")
            return HookResult(success=True, message="Pre-commit checks passed!")

        self.logger.info("Reformatting code with black...")
        result = self.command_executor.run(["python", "-m", "black", "--quiet", "."])

        if not result.success:
            self.logger.error("Black formatting failed.")
            if result.stderr:
                self.logger.error(result.stderr)
            return HookResult(
                success=False,
                message="Black formatting failed.",
                exit_code=1,
            )

        if self.stage_changes:
            modified_files = _get_modified_python_files(self.command_executor)
            if modified_files:
                self.logger.info(f"Staging {len(modified_files)} formatted file(s)...")
                staging_result = _stage_files(self.command_executor, modified_files)
                if not staging_result.success:
                    self.logger.error("Failed to stage formatted files.")
                    return HookResult(
                        success=False,
                        message="Failed to stage formatted files.",
                        exit_code=1,
                    )
                self.logger.success("Formatted files staged successfully!")

        self.logger.success("Code reformatted successfully!")
        return HookResult(success=True, message="Pre-commit checks passed!")


__all__ = ["BlackFormatterPreCommit"]
