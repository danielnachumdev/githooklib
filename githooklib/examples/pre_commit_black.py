from githooklib import GitHook, GitHookContext, HookResult
from githooklib.logger import Logger
from githooklib.command import CommandExecutor


def _check_black_exists(logger: Logger, command_executor: CommandExecutor) -> bool:
    check_result = command_executor.run(["python", "-m", "black", "--version"])
    if check_result.exit_code == 127:
        return False
    if not check_result.success and "No module named" in check_result.stderr:
        return False
    return True


class PreCommit(GitHook):
    @property
    def hook_name(self) -> str:
        return "pre-commit"

    def execute(self, context: GitHookContext) -> HookResult:
        if not _check_black_exists(self.logger, self.command_executor):
            self.logger.warning("Black tool not found. Skipping code formatting check.")
            return HookResult(
                success=True,
                message="Black tool not found. Check skipped.",
            )

        self.logger.info("Reformatting code with black...")
        result = self.command_executor.run(["python", "-m", "black", "."])

        if not result.success:
            self.logger.error("Black formatting failed.")
            if result.stderr:
                self.logger.error(result.stderr)
            return HookResult(
                success=False,
                message="Black formatting failed.",
                exit_code=1,
            )

        self.logger.success("Code reformatted successfully!")
        return HookResult(success=True, message="Pre-commit checks passed!")
