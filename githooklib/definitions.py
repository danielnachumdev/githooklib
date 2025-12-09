from dataclasses import dataclass
from typing import List, Optional
from .constants import EXIT_SUCCESS, EXIT_FAILURE


@dataclass
class CommandResult:
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    command: List[str]

    def __bool__(self) -> bool:
        return self.success


@dataclass
class HookResult:
    success: bool
    message: Optional[str] = None
    exit_code: int = EXIT_SUCCESS

    def __post_init__(self) -> None:
        if self.exit_code == EXIT_SUCCESS and not self.success:
            self.exit_code = EXIT_FAILURE
        elif self.exit_code != EXIT_SUCCESS and self.success:
            self.exit_code = EXIT_SUCCESS

    def __bool__(self) -> bool:
        return self.success


__all__ = [
    "CommandResult",
    "HookResult",
]
