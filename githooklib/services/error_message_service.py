from pathlib import Path

from ..logger import get_logger
from ..ui_messages import (
    UI_MESSAGE_HOOK_NOT_FOUND_PREFIX,
    UI_MESSAGE_HOOK_NOT_FOUND_SUFFIX,
    UI_MESSAGE_COULD_NOT_FIND_HOOKS_UNDER,
)
from .hook_discovery_service import HookDiscoveryService

logger = get_logger()


class ErrorMessageService:

    @staticmethod
    def _resolve_search_path(search_path: str, cwd: Path) -> Path:
        if Path(search_path).is_absolute():
            return Path(search_path)
        return cwd / search_path

    @staticmethod
    def _add_search_dir_info(error_lines: list[str], search_dir: Path) -> None:
        if not search_dir.exists() or not search_dir.is_dir():
            error_lines.append(f"  - {search_dir} (directory does not exist)")
            return

        py_files = [f for f in search_dir.glob("*.py") if f.name != "__init__.py"]
        if py_files:
            error_lines.append(f"  - {search_dir} (found {len(py_files)} .py files)")
        else:
            error_lines.append(f"  - {search_dir} (no .py files found)")

    def __init__(self) -> None:
        self.hook_discovery_service = HookDiscoveryService()

    def get_hook_not_found_error_message(self, hook_name: str) -> str:
        error_lines = [
            f"{UI_MESSAGE_HOOK_NOT_FOUND_PREFIX}{hook_name}{UI_MESSAGE_HOOK_NOT_FOUND_SUFFIX}"
        ]
        error_lines.append(UI_MESSAGE_COULD_NOT_FIND_HOOKS_UNDER)

        self._add_project_root_search_info(error_lines)
        self._add_hook_search_paths_info(error_lines)

        error_message = "\n".join(error_lines)
        return error_message

    def _add_project_root_search_info(self, error_lines: list[str]) -> None:
        project_root = self.hook_discovery_service.project_root
        if not project_root:
            return

        root_hooks = list(project_root.glob("*_hook.py"))
        if root_hooks:
            error_lines.append(
                f"  - {project_root} (found {len(root_hooks)} *_hook.py files)"
            )
        else:
            error_lines.append(f"  - {project_root} (no *_hook.py files found)")

    def _add_hook_search_paths_info(self, error_lines: list[str]) -> None:
        cwd = Path.cwd()
        hook_search_paths = self.hook_discovery_service.hook_search_paths
        for search_path in hook_search_paths:
            search_dir = self._resolve_search_path(search_path, cwd)
            self._add_search_dir_info(error_lines, search_dir)


__all__ = ["ErrorMessageService"]
