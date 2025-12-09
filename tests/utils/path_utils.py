import os
from pathlib import Path
from typing import Union, Optional

from githooklib.gateways import ProjectRootGateway


class PathUtils:
    @staticmethod
    def normalize(path: Union[Path, str]) -> Path:
        if isinstance(path, str):
            path = Path(path)
        return path.resolve().absolute()

    @staticmethod
    def set_cwd(path: Union[Path, str]) -> None:
        os.chdir(str(path))

    @staticmethod
    def get_cwd() -> Path:
        return PathUtils.normalize(os.getcwd())

    @staticmethod
    def get_project_root() -> Optional[Path]:
        return ProjectRootGateway.find_project_root()


__all__ = ["PathUtils"]
