import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

from .definitions import CommandResult
from .logger import get_logger
from .utils.command_result_factory import CommandResultFactory

logger = get_logger()


class CommandExecutor:

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
        result = self._execute_command(
            cmd_list, normalized_cwd, capture_output, check, text, shell
        )
        return result

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
            logger.warning("Command failed with CalledProcessError: %s", e)
            return CommandResultFactory.create_error_result(e, cmd_list, capture_output)
        except FileNotFoundError:
            logger.error("Command not found: %s", cmd_list[0])
            return CommandResultFactory.create_not_found_result(cmd_list)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Unexpected error executing command: %s", e)
            return CommandResultFactory.create_generic_error_result(e, cmd_list)

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
        return CommandResultFactory.create_success_result(
            result, cmd_list, capture_output
        )


__all__ = ["CommandResult", "CommandExecutor", "CommandResultFactory"]
