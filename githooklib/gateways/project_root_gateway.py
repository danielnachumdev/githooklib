from functools import lru_cache
from pathlib import Path

from ..exceptions import GitHookLibException
from ..logger import get_logger
from .git_gateway import GitGateway

logger = get_logger()


class ProjectRootGateway:
    @staticmethod
    @lru_cache
    def find_project_root() -> Path:
        git = GitGateway.get_git_root_path()
        if not git:
            logger.error("Could not find git repository")
            raise GitHookLibException("Could not find git repository")
        result = git.parent
        logger.trace("Project root: %s", result)
        return result


__all__ = ["ProjectRootGateway"]
