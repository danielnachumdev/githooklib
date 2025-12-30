from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Type

from ..constants import DEFAULT_HOOK_SEARCH_DIR
from ..git_hook import GitHook
from ..gateways.project_root_gateway import ProjectRootGateway
from ..gateways.module_import_gateway import ModuleImportGateway
from ..logger import get_logger
from ..utils.singleton import singleton

logger = get_logger()


@singleton
class HookDiscoveryService:
    DEFAULT_HOOK_SEARCH_DIR = "githooks"

    @staticmethod
    def _collect_hook_classes_by_name() -> Dict[str, List[Type[GitHook]]]:
        hook_classes_by_name: Dict[str, List[Type[GitHook]]] = defaultdict(list)
        registered_hooks = GitHook.get_registered_hooks()
        logger.trace("Found %d registered hook classes", len(registered_hooks))
        for hook_class in registered_hooks:
            logger.trace("Processing hook class: %s", hook_class.__name__)
            try:
                instance = hook_class()
                hook_name = instance.get_hook_name()
                hook_classes_by_name[hook_name].append(hook_class)
            except Exception as e:
                logger.error(
                    "Failed to instantiate hook class %s: %s", hook_class.__name__, e
                )
                logger.trace("Exception details: %s", e, exc_info=True)
                continue
        return dict(hook_classes_by_name)

    def __init__(self) -> None:
        self.project_root = ProjectRootGateway.find_project_root()
        self.hook_search_paths = [DEFAULT_HOOK_SEARCH_DIR]
        logger.trace("Default hook search paths: %s", self.hook_search_paths)
        self.module_import_gateway = ModuleImportGateway()
        self._hooks: Optional[Dict[str, Type[GitHook]]] = None
        logger.trace("HookDiscoveryService initialized")

    def discover_hooks(self) -> Dict[str, Type[GitHook]]:
        if self._hooks is not None:
            logger.debug("Using cached hooks (%d hooks)", len(self._hooks))
            logger.trace("Cached hooks: %s", list(self._hooks.keys()))
            return self._hooks
        if not self.project_root:
            logger.debug("No project root found, returning empty hooks dict")
            return {}

        self._import_all_hook_modules()
        hook_classes_by_name = self._collect_hook_classes_by_name()
        self._validate_no_duplicate_hooks(hook_classes_by_name)
        hooks = {name: classes[0] for name, classes in hook_classes_by_name.items()}
        self._hooks = hooks
        return hooks

    def _find_hook_modules(self) -> list[Path]:
        hook_modules = []

        if self.project_root:
            logger.trace(
                "Searching for *_hook.py files in project root: %s", self.project_root
            )
            for py_file in self.project_root.glob("*_hook.py"):
                logger.trace("Found hook file in project root: %s", py_file)
                hook_modules.append(py_file)

        cwd = Path.cwd()
        logger.trace("Current working directory: %s", cwd)
        logger.trace("Search paths: %s", self.hook_search_paths)
        for search_path in self.hook_search_paths:
            if Path(search_path).is_absolute():
                search_dir = Path(search_path)
                logger.trace("Using absolute search path: %s", search_dir)
            else:
                search_dir = cwd / search_path
                logger.trace("Using relative search path: %s", search_dir)

            if search_dir.exists() and search_dir.is_dir():
                logger.trace("Searching for Python files in: %s", search_dir)
                for py_file in search_dir.glob("*.py"):
                    if py_file.name != "__init__.py":
                        logger.trace("Found hook module: %s", py_file)
                        hook_modules.append(py_file)
            else:
                logger.trace(
                    "Search directory does not exist or is not a directory: %s",
                    search_dir,
                )

        logger.debug("Found %d hook modules", len(hook_modules))
        return hook_modules

    def _invalidate_cache(self) -> None:
        logger.debug("Invalidating hook discovery cache")
        self._hooks = None
        logger.trace("Cache cleared")

    def set_hook_search_paths(self, hook_search_paths: List[str]) -> None:
        logger.debug("Setting hook search paths: %s", hook_search_paths)
        old_paths = self.hook_search_paths
        self.hook_search_paths = hook_search_paths
        logger.trace(
            "Hook search paths changed from %s to %s", old_paths, hook_search_paths
        )
        self._invalidate_cache()

    def hook_exists(self, hook_name: str) -> bool:
        logger.debug("Checking if hook '%s' exists", hook_name)
        hooks = self.discover_hooks()
        exists = hook_name in hooks
        logger.debug("Hook '%s' exists: %s", hook_name, exists)
        return exists

    def _import_all_hook_modules(self) -> None:
        hook_modules = self._find_hook_modules()
        for module_path in hook_modules:
            self.module_import_gateway.import_module(module_path, self.project_root)

    def _validate_no_duplicate_hooks(
        self, hook_classes_by_name: Dict[str, List[Type[GitHook]]]
    ) -> None:
        logger.trace("Validating no duplicate hooks")
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
        self, duplicates: Dict[str, List[Type[GitHook]]]
    ) -> None:
        logger.debug("Raising duplicate hook error")
        logger.trace("Duplicates: %s", list(duplicates.keys()))
        error_lines = ["Duplicate hook implementations found:"]
        for hook_name, hook_classes in duplicates.items():
            logger.trace(
                "Processing duplicate hook '%s' with %d classes",
                hook_name,
                len(hook_classes),
            )
            error_lines.append(
                f"\n  Hook '{hook_name}' is defined in multiple classes:"
            )
            for hook_class in hook_classes:
                module_name = hook_class.__module__
                class_name = hook_class.__name__
                logger.trace("Finding module file for: %s", module_name)
                module_file = self.module_import_gateway.find_module_file(
                    module_name, self.project_root
                )
                if module_file:
                    logger.trace("Module file found: %s", module_file)
                    error_lines.append(f"    - {class_name} in {module_file}")
                else:
                    logger.trace(
                        "Module file not found, using module name: %s", module_name
                    )
                    error_lines.append(f"    - {class_name} in module '{module_name}'")
        error_message = "\n".join(error_lines)
        logger.trace(
            "Error message constructed, length: %d characters", len(error_message)
        )
        raise ValueError(error_message)


__all__ = ["HookDiscoveryService"]
