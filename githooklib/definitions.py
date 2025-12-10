from dataclasses import dataclass
from pathlib import Path
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


@dataclass
class SeedFailureDetails:
    example_not_found: bool
    project_root_not_found: bool
    target_hook_already_exists: bool
    target_hook_path: Optional[Path]
    available_examples: List[str]


__all__ = [
    "CommandResult",
    "HookResult",
    "SeedFailureDetails",
]
