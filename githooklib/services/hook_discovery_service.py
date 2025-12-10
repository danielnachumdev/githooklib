import logging
from collections import defaultdict
from pathlib import Path
from typing import Optional

from ..git_hook import GitHook
from ..gateways.project_root_gateway import ProjectRootGateway
from ..gateways.module_import_gateway import ModuleImportGateway
from ..logger import get_logger

logger = get_logger()


class HookDiscoveryService:
    DEFAULT_HOOK_SEARCH_DIR = "githooks"

    @staticmethod
    def _collect_hook_classes_by_name() -> dict[str, list[type[GitHook]]]:
        hook_classes_by_name: dict[str, list[type[GitHook]]] = defaultdict(list)
        registered_hooks = GitHook.get_registered_hooks()
        for hook_class in registered_hooks:
            try:
                instance = hook_class()
            except Exception as e:
                logger.error(
                    "Failed to instantiate hook class %s: %s", hook_class.__name__, e
                )
                continue
            hook_name = instance.get_hook_name()
            hook_classes_by_name[hook_name].append(hook_class)
        return dict(hook_classes_by_name)

    def __init__(
        self,
        hook_search_paths: list[str],
        module_import_gateway: ModuleImportGateway,
    ) -> None:
        self.project_root = ProjectRootGateway.find_project_root()
        self.hook_search_paths = hook_search_paths
        self.module_import_gateway = module_import_gateway
        self._hooks: Optional[dict[str, type[GitHook]]] = None

    def discover_hooks(self) -> dict[str, type[GitHook]]:
        if self._hooks is not None:
            return self._hooks
        if not self.project_root:
            return {}

        self._import_all_hook_modules()
        hook_classes_by_name = self._collect_hook_classes_by_name()
        self._validate_no_duplicate_hooks(hook_classes_by_name)
        hooks = {name: classes[0] for name, classes in hook_classes_by_name.items()}
        self._hooks = hooks
        return hooks

    def find_hook_modules(self) -> list[Path]:
        hook_modules = []

        if self.project_root:
            for py_file in self.project_root.glob("*_hook.py"):
                hook_modules.append(py_file)

        cwd = Path.cwd()
        for search_path in self.hook_search_paths:
            if Path(search_path).is_absolute():
                search_dir = Path(search_path)
            else:
                search_dir = cwd / search_path

            if search_dir.exists() and search_dir.is_dir():
                for py_file in search_dir.glob("*.py"):
                    if py_file.name != "__init__.py":
                        hook_modules.append(py_file)

        return hook_modules

    def invalidate_cache(self) -> None:
        self._hooks = None

    def set_hook_search_paths(self, hook_search_paths: list[str]) -> None:
        self.hook_search_paths = hook_search_paths
        self.invalidate_cache()

    def _import_all_hook_modules(self) -> None:
        hook_modules = self.find_hook_modules()
        for module_path in hook_modules:
            self.module_import_gateway.import_module(module_path, self.project_root)

    def _validate_no_duplicate_hooks(
        self, hook_classes_by_name: dict[str, list[type[GitHook]]]
    ) -> None:
        duplicates = {
            name: classes
            for name, classes in hook_classes_by_name.items()
            if len(classes) > 1
        }
        if duplicates:
            logger.error(
                "Found %d duplicate hook names: %s",
                len(duplicates),
                list(duplicates.keys()),
            )
            self._raise_duplicate_hook_error(duplicates)

    def _raise_duplicate_hook_error(
        self, duplicates: dict[str, list[type[GitHook]]]
    ) -> None:
        error_lines = ["Duplicate hook implementations found:"]
        for hook_name, hook_classes in duplicates.items():
            error_lines.append(
                f"\n  Hook '{hook_name}' is defined in multiple classes:"
            )
            for hook_class in hook_classes:
                module_name = hook_class.__module__
                class_name = hook_class.__name__
                module_file = self.module_import_gateway.find_module_file(
                    module_name, self.project_root
                )
                if module_file:
                    error_lines.append(f"    - {class_name} in {module_file}")
                else:
                    error_lines.append(f"    - {class_name} in module '{module_name}'")
        error_message = "\n".join(error_lines)
        raise ValueError(error_message)


__all__ = ["HookDiscoveryService"]
