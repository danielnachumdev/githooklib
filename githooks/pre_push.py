from githooklib import GitHook, GitHookContext, HookResult
from githooklib.logger import Logger
from githooklib.command import CommandExecutor


def format_code_with_black(
    logger: Logger, command_executor: CommandExecutor
) -> HookResult:
    """Format the entire project using black formatter.

    This function handles all aspects of black formatting from start to finish:
    - Logging the start of formatting
    - Running the black formatter
    - Checking results
    - Logging success or failure
    - Returning appropriate HookResult

    Args:
        logger: Logger instance for logging messages
        command_executor: CommandExecutor instance for running commands

    Returns:
        HookResult indicating success or failure of the formatting operation
    """
    logger.info("Reformatting code with black...")

    # Run black formatter
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


def run_mypy_check(logger: Logger, command_executor: CommandExecutor) -> HookResult:
    """Run mypy type checking on the entire project.

    This function handles all aspects of mypy type checking from start to finish:
    - Logging the start of type checking
    - Running mypy
    - Checking results
    - Logging success or failure
    - Returning appropriate HookResult

    Args:
        logger: Logger instance for logging messages
        command_executor: CommandExecutor instance for running commands

    Returns:
        HookResult indicating success or failure of the type checking operation
    """
    logger.info("Running mypy type checking...")

    # Run mypy type checking
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
        # Format code with black
        format_result = format_code_with_black(self.logger, self.command_executor)
        if not format_result.success:
            return format_result

        # Run mypy type checking
        mypy_result = run_mypy_check(self.logger, self.command_executor)
        if not mypy_result.success:
            return mypy_result

        return HookResult(success=True, message="All checks passed!")
