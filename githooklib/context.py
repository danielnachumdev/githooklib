import sys
from dataclasses import dataclass
from typing import List

from .logger import get_logger

logger = get_logger()


@dataclass
class GitHookContext:

    hook_name: str
    stdin_lines: List[str]

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


__all__ = ["GitHookContext"]
