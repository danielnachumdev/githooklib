import sys
from functools import lru_cache
from pathlib import Path
from typing import Optional

from ..logger import get_logger
from ..utils.singleton import singleton

logger = get_logger()


@singleton
class ModuleImportGateway:
    @staticmethod
    @lru_cache
    def find_module_file(
        module_name: str, project_root: Optional[Path]
    ) -> Optional[str]:
        logger.trace("Finding module file for module: %s", module_name)
        logger.trace("Project root: %s", project_root)
        try:
            import importlib.util

            spec = importlib.util.find_spec(module_name)
            logger.trace("Module spec: %s", spec)
            if spec and spec.origin:
                logger.trace("Module origin: %s", spec.origin)
                if project_root:
                    try:
                        module_path = Path(spec.origin)
                        relative_path = module_path.relative_to(project_root)
                        logger.trace("Relative path: %s", relative_path)
                        return str(relative_path)
                    except ValueError as e:
                        logger.trace("Cannot make relative path: %s", e)
                        return spec.origin
                return spec.origin
        except (ImportError, AttributeError, ValueError) as e:
            logger.trace("Error finding module file: %s", e)
            pass
        logger.trace("Module file not found for: %s", module_name)
        return None

    @staticmethod
    @lru_cache
    def convert_module_name_to_file_path(module_name: str) -> Path:
        logger.trace("Converting module name to file path: %s", module_name)
        module_path_parts = module_name.split(".")
        logger.trace("Module path parts: %s", module_path_parts)
        file_path = Path(*module_path_parts).with_suffix(".py")
        logger.trace("Converted file path: %s", file_path)
        return file_path

    @staticmethod
    def _add_to_sys_path_if_needed(directory: Path) -> None:
        directory_str = str(directory)
        if directory_str not in sys.path:
            logger.trace("Adding directory to sys.path: %s", directory_str)
            sys.path.insert(0, directory_str)
        else:
            logger.trace("Directory already in sys.path: %s", directory_str)

    @lru_cache
    def import_module(self, module_path: Path, base_dir: Path) -> None:
        logger.debug("Importing module: %s", module_path)
        module_path = module_path.resolve()
        logger.trace("Resolved path: %s", module_path)
        try:
            relative_path = module_path.relative_to(base_dir)
            self._import_relative_module(relative_path, base_dir)
        except ValueError as e:
            logger.trace("Cannot make relative path: %s, importing as absolute", e)
            self._import_absolute_module(module_path)

    def _import_relative_module(self, relative_path: Path, base_dir: Path) -> None:
        parts = relative_path.parts[:-1] + (relative_path.stem,)
        module_name = ".".join(parts)
        self._add_to_sys_path_if_needed(base_dir)
        __import__(module_name)
        logger.trace("Module imported successfully: %s", module_name)

    def _import_absolute_module(self, module_path: Path) -> None:
        parent_dir = module_path.parent.resolve()
        module_name = module_path.stem
        logger.trace("Absolute module name: %s", module_name)
        logger.trace("Parent directory: %s", parent_dir)
        logger.trace("Adding parent directory to sys.path if needed: %s", parent_dir)
        self._add_to_sys_path_if_needed(parent_dir)
        logger.trace("Importing module: %s", module_name)
        __import__(module_name)
        logger.trace("Module imported successfully: %s", module_name)


__all__ = ["ModuleImportGateway"]
