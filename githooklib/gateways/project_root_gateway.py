from functools import lru_cache
from pathlib import Path

from ..exceptions import GitHookLibException
from ..logger import get_logger
from ..ui_messages import UI_MESSAGE_COULD_NOT_FIND_GIT_REPOSITORY
from .git_gateway import GitGateway

logger = get_logger()


class ProjectRootGateway:
    @staticmethod
    @lru_cache
    def find_project_root() -> Path:
        logger.debug("Finding project root")
        git_gateway = GitGateway()
        git = git_gateway.get_git_root_path()
        logger.trace("Git root path: %s", git)
        if not git:
            logger.error(UI_MESSAGE_COULD_NOT_FIND_GIT_REPOSITORY)
            logger.debug("Git repository not found, cannot determine project root")
            raise GitHookLibException(UI_MESSAGE_COULD_NOT_FIND_GIT_REPOSITORY)
        result = git.parent
        logger.debug("Project root: %s", result)
        logger.trace("Project root resolved from git root: %s -> %s", git, result)
        return result


__all__ = ["ProjectRootGateway"]
