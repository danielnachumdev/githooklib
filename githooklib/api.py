import sys
import logging
from pathlib import Path
from typing import Optional

from .git_hook import GitHook


class HookAPI:
    DEFAULT_HOOK_SEARCH_DIR = "githooks"

    def __init__(
        self,
        project_root: Optional[Path] = None,
        hook_search_paths: Optional[list[str]] = None,
    ):
        self.project_root = project_root or self._find_project_root()
        if hook_search_paths is None:
            self.hook_search_paths = [self.DEFAULT_HOOK_SEARCH_DIR]
        else:
            self.hook_search_paths = hook_search_paths
        self._hooks: Optional[dict[str, type[GitHook]]] = None

    def _find_project_root(self) -> Optional[Path]:
        current = Path.cwd()
        for path in [current] + list(current.parents):
            if (path / "githooklib").exists():
                return path.resolve()
        return None

    def _find_hook_modules(self) -> list[Path]:
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

    def _import_hook_module(self, module_path: Path):
        module_path = module_path.resolve()
        base_dir = self.project_root or Path.cwd()

        try:
            relative_path = module_path.relative_to(base_dir)
            self._import_relative_module(relative_path, base_dir)
        except ValueError:
            self._import_absolute_module(module_path)

    def _import_relative_module(self, relative_path: Path, base_dir: Path):
        parts = relative_path.parts[:-1] + (relative_path.stem,)
        module_name = ".".join(parts)
        self._add_to_sys_path_if_needed(base_dir)
        __import__(module_name)

    def _import_absolute_module(self, module_path: Path):
        parent_dir = module_path.parent.resolve()
        self._add_to_sys_path_if_needed(parent_dir)
        module_name = module_path.stem
        __import__(module_name)

    def _add_to_sys_path_if_needed(self, directory: Path):
        if str(directory) not in sys.path:
            sys.path.insert(0, str(directory))

    def discover_hooks(self) -> dict[str, type[GitHook]]:
        if self._hooks is not None:
            return self._hooks
        if not self.project_root:
            return {}

        self._import_all_hook_modules()
        hook_classes_by_name = self._collect_hook_classes_by_name()
        self._validate_no_duplicate_hooks(hook_classes_by_name)

        hooks = {name: classes[0]
                 for name, classes in hook_classes_by_name.items()}
        self._hooks = hooks
        return hooks

    def _import_all_hook_modules(self):
        hook_modules = self._find_hook_modules()
        for module_path in hook_modules:
            self._import_hook_module(module_path)

    def _collect_hook_classes_by_name(self) -> dict[str, list[type[GitHook]]]:
        hook_classes_by_name: dict[str, list[type[GitHook]]] = {}
        for hook_class in GitHook.get_registered_hooks():
            instance = hook_class()
            hook_name = instance.hook_name
            if hook_name not in hook_classes_by_name:
                hook_classes_by_name[hook_name] = []
            hook_classes_by_name[hook_name].append(hook_class)
        return hook_classes_by_name

    def _validate_no_duplicate_hooks(self, hook_classes_by_name: dict[str, list[type[GitHook]]]):
        duplicates = {
            name: classes
            for name, classes in hook_classes_by_name.items()
            if len(classes) > 1
        }
        if duplicates:
            self._raise_duplicate_hook_error(duplicates)

    def _raise_duplicate_hook_error(self, duplicates: dict[str, list[type[GitHook]]]):
        error_lines = ["Duplicate hook implementations found:"]
        for hook_name, hook_classes in duplicates.items():
            error_lines.append(
                f"\n  Hook '{hook_name}' is defined in multiple classes:"
            )
            for hook_class in hook_classes:
                module_name = hook_class.__module__
                class_name = hook_class.__name__
                module_file = self._find_module_file(module_name)
                if module_file:
                    error_lines.append(f"    - {class_name} in {module_file}")
                else:
                    error_lines.append(
                        f"    - {class_name} in module '{module_name}'")
        error_message = "\n".join(error_lines)
        raise ValueError(error_message)

    def _find_module_file(self, module_name: str) -> Optional[str]:
        try:
            import importlib.util

            spec = importlib.util.find_spec(module_name)
            if spec and spec.origin:
                if self.project_root:
                    try:
                        module_path = Path(spec.origin)
                        relative_path = module_path.relative_to(
                            self.project_root)
                        return str(relative_path)
                    except ValueError:
                        return spec.origin
                return spec.origin
        except (ImportError, AttributeError, ValueError):
            pass
        return None

    def list_hooks(self) -> list[str]:
        hooks = self.discover_hooks()
        return sorted(hooks.keys())

    def install_hook(self, hook_name: str) -> bool:
        hooks = self.discover_hooks()
        if hook_name not in hooks:
            return False
        hook_class = hooks[hook_name]
        hook = hook_class()
        return hook.install()

    def uninstall_hook(self, hook_name: str) -> bool:
        hooks = self.discover_hooks()
        if hook_name not in hooks:
            return False
        hook_class = hooks[hook_name]
        hook = hook_class()
        return hook.uninstall()

    def run_hook(self, hook_name: str, debug: bool = False) -> int:
        hooks = self.discover_hooks()
        if hook_name not in hooks:
            return 1
        hook_class = hooks[hook_name]
        log_level = logging.DEBUG if debug else logging.INFO
        hook = hook_class(log_level=log_level)
        return hook.run()

    def get_installed_hooks(self) -> dict[str, bool]:
        git_root = self._find_git_root()
        if not git_root:
            return {}
        hooks_dir = git_root / ".git" / "hooks"
        if not hooks_dir.exists():
            return {}
        return self._get_installed_hooks(hooks_dir)

    def get_git_root(self) -> Optional[Path]:
        return self._find_git_root()

    def _find_git_root(self) -> Optional[Path]:
        current = Path.cwd()
        for path in [current] + list(current.parents):
            if (path / ".git").exists():
                return path.resolve()
        return None

    def _get_installed_hooks(self, hooks_dir: Path) -> dict[str, bool]:
        installed = {}
        for hook_file in hooks_dir.iterdir():
            if hook_file.is_file() and not hook_file.name.endswith(".sample"):
                hook_name = hook_file.name
                is_tool_installed = self._is_tool_installed_hook(hook_file)
                installed[hook_name] = is_tool_installed
        return installed

    def _is_tool_installed_hook(self, hook_path: Path) -> bool:
        try:
            content = hook_path.read_text()
            return "githooklib" in content and "find_project_root" in content
        except (OSError, IOError, UnicodeDecodeError):
            return False

    def set_hook_paths(self, *hook_paths: str) -> None:
        self.hook_search_paths = list(hook_paths)
        self._hooks = None

    def get_hook_not_found_error_message(self, hook_name: str) -> str:
        error_lines = [f"Error: Hook '{hook_name}' not found"]
        error_lines.append("Could not find hooks under:")

        self._add_project_root_search_info(error_lines)
        self._add_hook_search_paths_info(error_lines)

        return "\n".join(error_lines)

    def _add_project_root_search_info(self, error_lines: list[str]):
        if not self.project_root:
            return

        root_hooks = list(self.project_root.glob("*_hook.py"))
        if root_hooks:
            error_lines.append(
                f"  - {self.project_root} (found {len(root_hooks)} *_hook.py files)"
            )
        else:
            error_lines.append(
                f"  - {self.project_root} (no *_hook.py files found)"
            )

    def _add_hook_search_paths_info(self, error_lines: list[str]):
        cwd = Path.cwd()
        for search_path in self.hook_search_paths:
            search_dir = self._resolve_search_path(search_path, cwd)
            self._add_search_dir_info(error_lines, search_dir)

    def _resolve_search_path(self, search_path: str, cwd: Path) -> Path:
        if Path(search_path).is_absolute():
            return Path(search_path)
        return cwd / search_path

    def _add_search_dir_info(self, error_lines: list[str], search_dir: Path):
        if not search_dir.exists() or not search_dir.is_dir():
            error_lines.append(f"  - {search_dir} (directory does not exist)")
            return

        py_files = [f for f in search_dir.glob(
            "*.py") if f.name != "__init__.py"]
        if py_files:
            error_lines.append(
                f"  - {search_dir} (found {len(py_files)} .py files)"
            )
        else:
            error_lines.append(f"  - {search_dir} (no .py files found)")


__all__ = ["HookAPI"]
