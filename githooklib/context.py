import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .gateways.project_root_gateway import ProjectRootGateway
from .logger import get_logger

logger = get_logger()


@dataclass
class GitHookContext:

    hook_name: str
    stdin_lines: List[str]
    project_root: Optional[Path] = None

    @staticmethod
    def _read_stdin_lines() -> List[str]:
        if sys.stdin.isatty():
            return []
        lines = sys.stdin.read().strip().split("\n")
        logger.trace("stdin=%s", lines)
        return lines

    @classmethod
    def from_stdin(cls, hook_name: str) -> "GitHookContext":
        stdin_lines = cls._read_stdin_lines()
        context = cls(hook_name=hook_name, stdin_lines=stdin_lines)
        return context

    @classmethod
    def empty(cls, hook_name: str) -> "GitHookContext":
        context = cls(hook_name=hook_name, stdin_lines=[])
        return context

    def __post_init__(self) -> None:
        if self.project_root is None:
            self.project_root = ProjectRootGateway.find_project_root()

    def get_stdin_line(
        self, index: int, default: Optional[str] = None
    ) -> Optional[str]:
        if 0 <= index < len(self.stdin_lines):
            return self.stdin_lines[index]
        return default

    def has_stdin(self) -> bool:
        return len(self.stdin_lines) > 0


__all__ = ["GitHookContext"]
