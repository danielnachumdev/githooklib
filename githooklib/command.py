import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

from .logger import Logger
from .constants import EXIT_FAILURE


@dataclass
class CommandResult:
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    command: List[str]

    def __bool__(self) -> bool:
        return self.success


class CommandExecutor:
    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger

    def run(  # pylint: disable=too-many-positional-arguments
        self,
        command: Union[str, List[str]],
        cwd: Optional[Union[str, Path]] = None,
        capture_output: bool = True,
        check: bool = False,
        text: bool = True,
        shell: bool = False,
    ) -> CommandResult:
        cmd_list = self._normalize_command(command, shell)
        normalized_cwd = self._normalize_cwd(cwd)
        self._log_command(cmd_list)
        return self._execute_command(
            cmd_list, normalized_cwd, capture_output, check, text, shell
        )

    def _normalize_command(
        self, command: Union[str, List[str]], shell: bool
    ) -> List[str]:
        if isinstance(command, str):
            return command.split() if not shell else [command]
        return command

    def _normalize_cwd(self, cwd: Optional[Union[str, Path]]) -> Optional[Path]:
        if cwd is None:
            return None
        return Path(cwd) if isinstance(cwd, str) else cwd

    def _log_command(self, cmd_list: List[str]):
        if self.logger:
            cmd_str = " ".join(cmd_list)
            self.logger.debug(f"Executing: {cmd_str}")

    def _execute_command(  # pylint: disable=too-many-positional-arguments
        self,
        cmd_list: List[str],
        cwd: Optional[Path],
        capture_output: bool,
        check: bool,
        text: bool,
        shell: bool,
    ) -> CommandResult:
        try:
            return self._run_subprocess(
                cmd_list, cwd, capture_output, check, text, shell
            )
        except subprocess.CalledProcessError as e:
            return self._create_error_result(e, cmd_list, capture_output)
        except FileNotFoundError:
            return self._create_not_found_result(cmd_list)
        except Exception as e:  # pylint: disable=broad-exception-caught
            return self._create_generic_error_result(e, cmd_list)

    def _run_subprocess(  # pylint: disable=too-many-positional-arguments
        self,
        cmd_list: List[str],
        cwd: Optional[Path],
        capture_output: bool,
        check: bool,
        text: bool,
        shell: bool,
    ) -> CommandResult:
        result = subprocess.run(
            cmd_list,
            cwd=cwd,
            capture_output=capture_output,
            check=check,
            text=text,
            shell=shell,
        )
        return self._create_success_result(result, cmd_list, capture_output)

    def _create_success_result(
        self,
        result: subprocess.CompletedProcess,
        cmd_list: List[str],
        capture_output: bool,
    ) -> CommandResult:
        return self._create_result(
            success=result.returncode == 0,
            exit_code=result.returncode,
            stdout=result.stdout if capture_output else "",
            stderr=result.stderr if capture_output else "",
            command=cmd_list,
        )

    def _create_error_result(
        self,
        error: subprocess.CalledProcessError,
        cmd_list: List[str],
        capture_output: bool,
    ) -> CommandResult:
        return self._create_result(
            success=False,
            exit_code=error.returncode,
            stdout=error.stdout if capture_output else "",
            stderr=error.stderr if capture_output else "",
            command=cmd_list,
        )

    def _create_not_found_result(self, cmd_list: List[str]) -> CommandResult:
        command_name = cmd_list[0]
        error_msg = f"Command not found: {command_name}"
        if self.logger:
            self.logger.error(error_msg)
        return self._create_result(
            success=False,
            exit_code=127,
            stdout="",
            stderr=error_msg,
            command=cmd_list,
        )

    def _create_generic_error_result(
        self, error: Exception, cmd_list: List[str]
    ) -> CommandResult:
        error_msg = f"Error executing command: {error}"
        if self.logger:
            self.logger.error(error_msg)
        return self._create_result(
            success=False,
            exit_code=EXIT_FAILURE,
            stdout="",
            stderr=error_msg,
            command=cmd_list,
        )

    def _create_result(  # pylint: disable=too-many-positional-arguments
        self,
        success: bool,
        exit_code: int,
        stdout: str,
        stderr: str,
        command: List[str],
    ) -> CommandResult:
        return CommandResult(
            success=success,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            command=command,
        )


__all__ = ["CommandResult", "CommandExecutor"]
