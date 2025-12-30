from pathlib import Path
from typing import List

from ..logger import get_logger
from ..utils.singleton import singleton
from ..ui_messages import (
    UI_MESSAGE_HOOK_NOT_FOUND_PREFIX,
    UI_MESSAGE_HOOK_NOT_FOUND_SUFFIX,
    UI_MESSAGE_COULD_NOT_FIND_HOOKS_UNDER,
)
from .hook_discovery_service import HookDiscoveryService

logger = get_logger()


@singleton
class ErrorMessageService:

    @staticmethod
    def _resolve_search_path(search_path: str, cwd: Path) -> Path:
        logger.trace("Resolving search path: %s", search_path)
        if Path(search_path).is_absolute():
            resolved = Path(search_path)
            logger.trace("Path is absolute: %s", resolved)
            return resolved
        resolved = cwd / search_path
        logger.trace("Path is relative, resolved to: %s", resolved)
        return resolved

    @staticmethod
    def _add_search_dir_info(error_lines: List[str], search_dir: Path) -> None:
        logger.trace("Adding search directory info: %s", search_dir)
        if not search_dir.exists() or not search_dir.is_dir():
            logger.trace("Directory does not exist or is not a directory")
            error_lines.append(f"  - {search_dir} (directory does not exist)")
            return

        logger.trace("Searching for Python files in directory")
        py_files = [f for f in search_dir.glob("*.py") if f.name != "__init__.py"]
        logger.trace("Found %d Python files", len(py_files))
        if py_files:
            error_lines.append(f"  - {search_dir} (found {len(py_files)} .py files)")
        else:
            error_lines.append(f"  - {search_dir} (no .py files found)")

    def __init__(self) -> None:
        self.hook_discovery_service = HookDiscoveryService()
        logger.trace("ErrorMessageService initialized")

    def get_hook_not_found_error_message(self, hook_name: str) -> str:
        logger.debug("Getting error message for hook '%s' not found", hook_name)
        error_lines = [
            f"{UI_MESSAGE_HOOK_NOT_FOUND_PREFIX}{hook_name}{UI_MESSAGE_HOOK_NOT_FOUND_SUFFIX}"
        ]
        error_lines.append(UI_MESSAGE_COULD_NOT_FIND_HOOKS_UNDER)

        logger.trace("Adding project root search info")
        self._add_project_root_search_info(error_lines)
        logger.trace("Adding hook search paths info")
        self._add_hook_search_paths_info(error_lines)

        error_message = "\n".join(error_lines)
        logger.debug(
            "Error message generated, length: %d characters", len(error_message)
        )
        logger.trace("Error message: %s", error_message)
        return error_message

    def _add_project_root_search_info(self, error_lines: List[str]) -> None:
        project_root = self.hook_discovery_service.project_root
        logger.trace("Project root: %s", project_root)
        if not project_root:
            logger.trace("No project root, skipping project root search info")
            return

        logger.trace("Searching for *_hook.py files in project root")
        root_hooks = list(project_root.glob("*_hook.py"))
        logger.trace("Found %d *_hook.py files in project root", len(root_hooks))
        if root_hooks:
            error_lines.append(
                f"  - {project_root} (found {len(root_hooks)} *_hook.py files)"
            )
        else:
            error_lines.append(f"  - {project_root} (no *_hook.py files found)")

    def _add_hook_search_paths_info(self, error_lines: List[str]) -> None:
        cwd = Path.cwd()
        hook_search_paths = self.hook_discovery_service.hook_search_paths
        logger.trace("Current working directory: %s", cwd)
        logger.trace("Hook search paths: %s", hook_search_paths)
        for search_path in hook_search_paths:
            logger.trace("Processing search path: %s", search_path)
            search_dir = self._resolve_search_path(search_path, cwd)
            logger.trace("Resolved search directory: %s", search_dir)
            self._add_search_dir_info(error_lines, search_dir)


__all__ = ["ErrorMessageService"]
