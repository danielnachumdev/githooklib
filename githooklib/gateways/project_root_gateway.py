from pathlib import Path
from typing import Optional

from ..exceptions import GitHookLibException
from ..logger import get_logger
from .git_repository_gateway import GitRepositoryGateway

logger = get_logger()


class ProjectRootGateway:
    @staticmethod
    def find_project_root() -> Path:
        git = GitRepositoryGateway.find_git_root()
        if not git:
            logger.error("Could not find git repository")
            raise GitHookLibException("Could not find git repository")
        result = git.parent
        logger.trace("Project root: %s", result)
        return result


__all__ = ["ProjectRootGateway"]
