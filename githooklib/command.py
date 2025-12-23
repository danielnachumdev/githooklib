import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Union

from .definitions import CommandResult
from .logger import get_logger
from .utils.command_result_factory import CommandResultFactory
from .utils.singleton import singleton

logger = get_logger()


@singleton
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
        logger.trace(
            "Command: %s, cwd: %s, capture_output: %s, check: %s, text: %s, shell: %s",
            command,
            cwd,
            capture_output,
            check,
            text,
            shell,
        )
        cmd_list = self._normalize_command(command, shell)
        normalized_cwd = self._normalize_cwd(cwd)
        logger.debug("Running command: %s", " ".join(cmd_list))
        logger.trace(
            "Normalized command: %s, normalized cwd: %s", cmd_list, normalized_cwd
        )
        result = self._execute_command(
            cmd_list, normalized_cwd, capture_output, check, text, shell
        )
        logger.trace(
            "Command result: exit_code=%d, stdout_length=%d, stderr_length=%d",
            result.exit_code,
            len(result.stdout) if result.stdout else 0,
            len(result.stderr) if result.stderr else 0,
        )
        return result

    def python(
        self,
        cmd: List[str],
        cwd: Optional[Union[str, Path]] = None,
        capture_output: bool = True,
        check: bool = False,
        text: bool = True,
        shell: bool = False,
    ) -> CommandResult:
        logger.trace("Python executable: %s, command: %s", sys.executable, cmd)
        full_command = [sys.executable] + cmd
        logger.trace("Full Python command: %s", full_command)
        return self.run(full_command, cwd, capture_output, check, text, shell)

    def python_module(
        self,
        module: str,
        cmd: List[str],
        cwd: Optional[Union[str, Path]] = None,
        capture_output: bool = True,
        check: bool = False,
        text: bool = True,
        shell: bool = False,
    ):
        logger.trace("Module: %s, command: %s", module, cmd)
        full_command = ["-m", module] + cmd
        logger.trace("Full module command: %s", full_command)
        return self.python(full_command, cwd, capture_output, check, text, shell)

    def _normalize_command(
        self, command: Union[str, List[str]], shell: bool
    ) -> List[str]:
        logger.trace("Normalizing command: %s, shell: %s", command, shell)
        if isinstance(command, str):
            normalized = command.split() if not shell else [command]
            logger.trace("Normalized command (from string): %s", normalized)
            return normalized
        logger.trace("Normalized command (from list): %s", command)
        return command

    def _normalize_cwd(self, cwd: Optional[Union[str, Path]]) -> Optional[Path]:
        logger.trace("Normalizing cwd: %s", cwd)
        if cwd is None:
            logger.trace("CWD is None")
            return None
        normalized = Path(cwd) if isinstance(cwd, str) else cwd
        logger.trace("Normalized cwd: %s", normalized)
        return normalized

    def _execute_command(  # pylint: disable=too-many-positional-arguments
        self,
        cmd_list: List[str],
        cwd: Optional[Path],
        capture_output: bool,
        check: bool,
        text: bool,
        shell: bool,
    ) -> CommandResult:
        logger.trace("Executing command: %s", cmd_list)
        logger.trace(
            "Execution parameters: cwd=%s, capture_output=%s, check=%s, text=%s, shell=%s",
            cwd,
            capture_output,
            check,
            text,
            shell,
        )
        try:
            return self._run_subprocess(
                cmd_list, cwd, capture_output, check, text, shell
            )
        except subprocess.CalledProcessError as e:
            logger.warning("Command failed with CalledProcessError: %s", e)
            logger.debug("Command exit code: %d", e.returncode)
            logger.trace("Exception details: %s", e, exc_info=True)
            return CommandResultFactory.create_error_result(e, cmd_list, capture_output)
        except FileNotFoundError as e:
            logger.error("Command not found: %s", cmd_list[0])
            logger.debug("Command '%s' not found in PATH", cmd_list[0])
            logger.trace("Exception details: %s", e, exc_info=True)
            return CommandResultFactory.create_not_found_result(cmd_list)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Unexpected error executing command: %s", e)
            logger.trace("Exception details: %s", e, exc_info=True)
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
        logger.trace("Calling subprocess.run with: %s", cmd_list)
        logger.trace(
            "Subprocess parameters: cwd=%s, capture_output=%s, check=%s, text=%s, shell=%s",
            cwd,
            capture_output,
            check,
            text,
            shell,
        )
        result = subprocess.run(
            cmd_list,
            cwd=cwd,
            capture_output=capture_output,
            check=check,
            text=text,
            shell=shell,
            encoding="utf-8" if text else None,
            errors="replace" if text else None,
        )
        logger.trace("Subprocess completed: returncode=%d", result.returncode)
        logger.trace(
            "Subprocess stdout length: %d, stderr length: %d",
            len(result.stdout) if result.stdout else 0,
            len(result.stderr) if result.stderr else 0,
        )
        return CommandResultFactory.create_success_result(
            result, cmd_list, capture_output
        )


__all__ = ["CommandResult", "CommandExecutor", "CommandResultFactory"]
