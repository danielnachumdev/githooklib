from githooklib.logger import Logger
from githooklib.command import CommandExecutor
from githooklib import HookResult


def _check_black_exists(logger: Logger, command_executor: CommandExecutor) -> bool:
    check_result = command_executor.run(["python", "-m", "black", "--version"])
    if check_result.exit_code == 127:
        return False
    if not check_result.success and "No module named" in check_result.stderr:
        return False
    return True


def format_project_with_black(
    logger: Logger, command_executor: CommandExecutor
) -> HookResult:
    if not _check_black_exists(logger, command_executor):
        logger.warning("Black tool not found. Skipping code formatting check.")
        return HookResult(
            success=True,
            message="Black tool not found. Check skipped.",
        )

    logger.info("Reformatting code with black...")
    result = command_executor.run(["python", "-m", "black", "."])

    if not result.success:
        logger.error("Black formatting failed.")
        if result.stderr:
            logger.error(result.stderr)
        return HookResult(
            success=False,
            message="Black formatting failed.",
            exit_code=1,
        )

    logger.success("Code reformatted successfully!")
    return HookResult(success=True, message="Code reformatted successfully!")
