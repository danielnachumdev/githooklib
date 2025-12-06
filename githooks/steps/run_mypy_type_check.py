from githooklib.logger import Logger
from githooklib.command import CommandExecutor
from githooklib import HookResult


def _mypy_exists(command_executor: CommandExecutor) -> bool:
    check_result = command_executor.run(["python", "-m", "mypy", "--version"])
    if check_result.exit_code == 127:
        return False
    if not check_result.success and "No module named" in check_result.stderr:
        return False
    return True


def run_mypy_type_check(
    logger: Logger, command_executor: CommandExecutor
) -> HookResult:
    if not _mypy_exists(command_executor):
        logger.warning("mypy tool not found. Skipping type checking.")
        return HookResult(
            success=True,
            message="mypy tool not found. Check skipped.",
        )

    logger.info("Running mypy type checking...")
    result = command_executor.run(
        ["python", "-m", "mypy", "--config-file", ".\\mypy.ini"]
    )

    if not result.success:
        error_details = []
        if result.stdout:
            error_details.append(result.stdout.strip())
        if result.stderr:
            error_details.append(result.stderr.strip())

        error_message = "\n".join(error_details) if error_details else "Unknown error"
        separator = "-" * 70

        logger.error("mypy type checking failed. Push aborted.")
        logger.error(f"\n{separator}\n{error_message}\n{separator}")

        return HookResult(
            success=False,
            message=f"mypy type checking failed. Push aborted.\n{separator}\n{error_message}\n{separator}",
            exit_code=1,
        )

    logger.success("mypy type checking passed!")
    return HookResult(success=True, message="mypy type checking passed!")


__all__ = [
    "run_mypy_type_check",
]
