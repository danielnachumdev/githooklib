import logging
from pathlib import Path
from typing import Optional

from ..logger import get_logger
from .git_repository_gateway import GitRepositoryGateway

logger = get_logger()


class ProjectRootGateway:
    @staticmethod
    def find_project_root() -> Optional[Path]:
        git = GitRepositoryGateway.find_git_root()
        result = git.parent if git else None
        logger.trace("Project root: %s", result)
        return result


__all__ = ["ProjectRootGateway"]
