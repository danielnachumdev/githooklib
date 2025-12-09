import subprocess
from typing import List

from ..command import CommandResult
from ..constants import EXIT_FAILURE


class CommandResultFactory:
    @staticmethod
    def create_success_result(
        result: subprocess.CompletedProcess,
        cmd_list: List[str],
        capture_output: bool,
    ) -> CommandResult:
        return CommandResult(
            success=result.returncode == 0,
            exit_code=result.returncode,
            stdout=result.stdout if capture_output else "",
            stderr=result.stderr if capture_output else "",
            command=cmd_list,
        )

    @staticmethod
    def create_error_result(
        error: subprocess.CalledProcessError,
        cmd_list: List[str],
        capture_output: bool,
    ) -> CommandResult:
        return CommandResult(
            success=False,
            exit_code=error.returncode,
            stdout=error.stdout if capture_output else "",
            stderr=error.stderr if capture_output else "",
            command=cmd_list,
        )

    @staticmethod
    def create_not_found_result(cmd_list: List[str]) -> CommandResult:
        command_name = cmd_list[0]
        error_msg = f"Command not found: {command_name}"
        return CommandResult(
            success=False,
            exit_code=127,
            stdout="",
            stderr=error_msg,
            command=cmd_list,
        )

    @staticmethod
    def create_generic_error_result(
        error: Exception, cmd_list: List[str]
    ) -> CommandResult:
        error_msg = f"Error executing command: {error}"
        return CommandResult(
            success=False,
            exit_code=EXIT_FAILURE,
            stdout="",
            stderr=error_msg,
            command=cmd_list,
        )


__all__ = [
    "CommandResultFactory",
]
