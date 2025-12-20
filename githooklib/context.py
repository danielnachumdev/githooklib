import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .gateways import ProjectRootGateway
from .logger import get_logger

logger = get_logger()


@dataclass
class GitHookContext:
    hook_name: str
    argv: List[str]
    project_root: Path = ProjectRootGateway.find_project_root()

    @classmethod
    def from_argv(cls, hook_name: str) -> "GitHookContext":
        logger.trace("debug: %s", sys.argv)
        return cls(hook_name=hook_name, argv=sys.argv)


__all__ = ["GitHookContext"]
