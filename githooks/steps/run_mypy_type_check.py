from githooklib.logger import Logger
from githooklib.command import CommandExecutor
from githooklib import HookResult


def _check_mypy_exists(
    logger: Logger, command_executor: CommandExecutor
) -> bool:
    check_result = command_executor.run(["python", "-m", "mypy", "--version"])
    if check_result.exit_code == 127:
        return False
    if not check_result.success and "No module named" in check_result.stderr:
        return False
    return True


def run_mypy_type_check(
    logger: Logger, command_executor: CommandExecutor
) -> HookResult:
    if not _check_mypy_exists(logger, command_executor):
        logger.warning("mypy tool not found. Skipping type checking.")
        return HookResult(
            success=True,
            message="mypy tool not found. Check skipped.",
        )

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
