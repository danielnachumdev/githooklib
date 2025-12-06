from pathlib import Path
from typing import Optional

from .git_repository_gateway import GitRepositoryGateway


class ProjectRootGateway:
    @staticmethod
    def find_project_root() -> Optional[Path]:
        git = GitRepositoryGateway.find_git_root()
        return git.parent if git else None


__all__ = ["ProjectRootGateway"]
