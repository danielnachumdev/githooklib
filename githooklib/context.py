import sys
from dataclasses import dataclass
from typing import List

from .logger import get_logger

logger = get_logger()


@dataclass
class GitHookContext:
    hook_name: str
    argv: List[str]

    @classmethod
    def from_argv(cls, hook_name: str) -> "GitHookContext":
        logger.trace("debug: %s", sys.argv)
        return cls(hook_name=hook_name, argv=sys.argv)


__all__ = ["GitHookContext"]
