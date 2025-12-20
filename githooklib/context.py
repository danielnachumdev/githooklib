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
        logger.debug("Creating GitHookContext from argv for hook '%s'", hook_name)
        logger.trace("sys.argv: %s", sys.argv)
        context = cls(hook_name=hook_name, argv=sys.argv)
        logger.trace(
            "GitHookContext created: hook_name=%s, project_root=%s",
            context.hook_name,
            context.project_root,
        )
        return context


__all__ = ["GitHookContext"]
