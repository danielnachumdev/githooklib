from githooklib import GitHook, GitHookContext, HookResult
from githooklib.logger import Logger
from githooklib.command import CommandExecutor


def format_code_with_black(
    logger: Logger, command_executor: CommandExecutor
) -> HookResult:
    logger.info("Reformatting code with black...")
    result = command_executor.run(["python", "-m", "black", "."])

    if not result.success:
        logger.error("Black formatting failed. Push aborted.")
        if result.stderr:
            logger.error(result.stderr)
        return HookResult(
            success=False,
            message="Black formatting failed. Push aborted.",
            exit_code=1,
        )

    logger.success("Code reformatted successfully!")
    return HookResult(success=True, message="Code reformatted successfully!")


def run_mypy_type_check(
    logger: Logger, command_executor: CommandExecutor
) -> HookResult:
    logger.info("Running mypy type checking...")
    result = command_executor.run(["python", "-m", "mypy", "."])

    if not result.success:
        logger.error("mypy type checking failed. Push aborted.")
        if result.stderr:
            logger.error(result.stderr)
        return HookResult(
            success=False,
            message="mypy type checking failed. Push aborted.",
            exit_code=1,
        )

    logger.success("mypy type checking passed!")
    return HookResult(success=True, message="mypy type checking passed!")


class PrePush(GitHook):
    @property
    def hook_name(self) -> str:
        return "pre-push"

    def execute(self, context: GitHookContext) -> HookResult:
        format_result = format_code_with_black(
            self.logger, self.command_executor)
        if not format_result.success:
            return format_result

        mypy_result = run_mypy_type_check(self.logger, self.command_executor)
        if not mypy_result.success:
            return mypy_result

        return HookResult(success=True, message="All checks passed!")
