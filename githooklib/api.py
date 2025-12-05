import sys
import logging
from pathlib import Path
from typing import Optional

from .git_hook import GitHook


class HookAPI:
    """API for managing Git hooks. Contains all business logic for hook discovery and management."""

    DEFAULT_HOOK_SEARCH_DIR = "githooks"

    def __init__(
        self,
        project_root: Optional[Path] = None,
        hook_search_paths: Optional[list[str]] = None,
    ):
        self.project_root = project_root or self._find_project_root()
        # Default to CWD/githooks (relative path, resolved relative to CWD when used)
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

        # Search in project root for *_hook.py files (backward compatibility)
        if self.project_root:
            for py_file in self.project_root.glob("*_hook.py"):
                hook_modules.append(py_file)

        # Search in configured hook search paths - all .py files are considered hook files
        cwd = Path.cwd()
        for search_path in self.hook_search_paths:
            # Handle both absolute and relative paths
            if Path(search_path).is_absolute():
                search_dir = Path(search_path)
            else:
                # Always relative to current working directory
                search_dir = cwd / search_path

            if search_dir.exists() and search_dir.is_dir():
                # All Python files in the search directory are considered hook files
                # The hook name comes from the class, not the filename
                for py_file in search_dir.glob("*.py"):
                    # Skip __init__.py files
                    if py_file.name != "__init__.py":
                        hook_modules.append(py_file)

        return hook_modules

    def _import_hook_module(self, module_path: Path):
        """Import a hook module, handling both root-level and subdirectory modules."""
        # Resolve to absolute path
        module_path = module_path.resolve()

        # Try to find the base directory for imports
        # First try project root, then fall back to CWD
        base_dir = self.project_root or Path.cwd()

        # Calculate relative path from base directory
        try:
            relative_path = module_path.relative_to(base_dir)
        except ValueError:
            # If not relative to base_dir, try to use the path as-is
            # Add the parent directory to sys.path
            parent_dir = module_path.parent.resolve()
            if str(parent_dir) not in sys.path:
                sys.path.insert(0, str(parent_dir))
            # Use just the filename as module name
            module_name = module_path.stem
            __import__(module_name)
            return

        # Convert path to module name (e.g., githooks/pre_push.py -> githooks.pre_push)
        parts = relative_path.parts[:-1] + (relative_path.stem,)
        module_name = ".".join(parts)

        # Add base directory to path if not already there
        if str(base_dir) not in sys.path:
            sys.path.insert(0, str(base_dir))

        __import__(module_name)

    def discover_hooks(self) -> dict[str, type[GitHook]]:
        """Discover all available hooks from configured search paths.

        Returns:
            Dictionary mapping hook names to their hook classes.

        Raises:
            ValueError: If duplicate hook implementations are found.
        """
        if self._hooks is not None:
            return self._hooks
        if not self.project_root:
            return {}
        hook_modules = self._find_hook_modules()
        for module_path in hook_modules:
            self._import_hook_module(module_path)

        # Collect all hooks and check for duplicates
        hook_classes_by_name: dict[str, list[type[GitHook]]] = {}
        for hook_class in GitHook.get_registered_hooks():
            # type: ignore[call-arg]  # Hook subclasses properly initialize GitHook
            instance = hook_class()
            hook_name = instance.hook_name
            if hook_name not in hook_classes_by_name:
                hook_classes_by_name[hook_name] = []
            hook_classes_by_name[hook_name].append(hook_class)

        # Check for duplicates and raise error if found
        duplicates = {
            name: classes
            for name, classes in hook_classes_by_name.items()
            if len(classes) > 1
        }
        if duplicates:
            self._raise_duplicate_hook_error(duplicates)

        # Build final hooks dict (should be no duplicates at this point)
        hooks = {name: classes[0] for name, classes in hook_classes_by_name.items()}
        self._hooks = hooks
        return hooks

    def _raise_duplicate_hook_error(self, duplicates: dict[str, list[type[GitHook]]]):
        """Raise an error with details about duplicate hook implementations."""
        error_lines = ["Duplicate hook implementations found:"]
        for hook_name, hook_classes in duplicates.items():
            error_lines.append(
                f"\n  Hook '{hook_name}' is defined in multiple classes:"
            )
            for hook_class in hook_classes:
                module_name = hook_class.__module__
                class_name = hook_class.__name__
                # Try to find the file path for better error message
                module_file = self._find_module_file(module_name)
                if module_file:
                    error_lines.append(f"    - {class_name} in {module_file}")
                else:
                    error_lines.append(f"    - {class_name} in module '{module_name}'")
        error_message = "\n".join(error_lines)
        raise ValueError(error_message)

    def _find_module_file(self, module_name: str) -> Optional[str]:
        """Try to find the file path for a module."""
        try:
            import importlib.util

            spec = importlib.util.find_spec(module_name)
            if spec and spec.origin:
                # Try to make path relative to project root for cleaner output
                if self.project_root:
                    try:
                        module_path = Path(spec.origin)
                        relative_path = module_path.relative_to(self.project_root)
                        return str(relative_path)
                    except ValueError:
                        return spec.origin
                return spec.origin
        except (ImportError, AttributeError, ValueError):
            pass
        return None

    def list_hooks(self) -> list[str]:
        """List all available hook names.

        Returns:
            List of hook names, sorted alphabetically.

        Raises:
            ValueError: If duplicate hook implementations are found.
        """
        hooks = self.discover_hooks()
        return sorted(hooks.keys())

    def install_hook(self, hook_name: str) -> bool:
        """Install a hook.

        Args:
            hook_name: Name of the hook to install.

        Returns:
            True if installation was successful, False otherwise.

        Raises:
            ValueError: If duplicate hook implementations are found.
        """
        hooks = self.discover_hooks()
        if hook_name not in hooks:
            return False
        hook_class = hooks[hook_name]
        # type: ignore[call-arg]  # Hook subclasses properly initialize GitHook
        hook = hook_class()
        return hook.install()

    def uninstall_hook(self, hook_name: str) -> bool:
        """Uninstall a hook.

        Args:
            hook_name: Name of the hook to uninstall.

        Returns:
            True if uninstallation was successful, False otherwise.

        Raises:
            ValueError: If duplicate hook implementations are found.
        """
        hooks = self.discover_hooks()
        if hook_name not in hooks:
            return False
        hook_class = hooks[hook_name]
        # type: ignore[call-arg]  # Hook subclasses properly initialize GitHook
        hook = hook_class()
        return hook.uninstall()

    def run_hook(self, hook_name: str, debug: bool = False) -> int:
        """Run a hook explicitly.

        Args:
            hook_name: Name of the hook to run.
            debug: Enable debug level logging.

        Returns:
            Exit code from the hook execution (0 for success, non-zero for failure).

        Raises:
            ValueError: If duplicate hook implementations are found.
        """
        hooks = self.discover_hooks()
        if hook_name not in hooks:
            return 1
        hook_class = hooks[hook_name]
        log_level = logging.DEBUG if debug else logging.INFO
        # type: ignore[call-arg]  # Hook subclasses properly initialize GitHook
        hook = hook_class(log_level=log_level)
        return hook.run()

    def get_installed_hooks(self) -> dict[str, bool]:
        """Get information about currently installed hooks.

        Returns:
            Dictionary mapping hook names to a boolean indicating if they were
            installed via this tool (True) or externally (False).
            Returns empty dict if not in a git repository or no hooks directory found.
        """
        git_root = self._find_git_root()
        if not git_root:
            return {}
        hooks_dir = git_root / ".git" / "hooks"
        if not hooks_dir.exists():
            return {}
        return self._get_installed_hooks(hooks_dir)

    def get_git_root(self) -> Optional[Path]:
        """Get the git repository root path.

        Returns:
            Path to the git repository root, or None if not in a git repository.
        """
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
        """Set hook search paths. Can specify multiple paths.

        Args:
            *hook_paths: Variable number of hook search paths.
        """
        self.hook_search_paths = list(hook_paths)
        # Reset cached hooks to force rediscovery with new paths
        self._hooks = None

    def get_hook_not_found_error_message(self, hook_name: str) -> str:
        """Generate an error message when a hook is not found.

        Args:
            hook_name: Name of the hook that was not found.

        Returns:
            Error message string describing where hooks were searched.
        """
        error_lines = [f"Error: Hook '{hook_name}' not found"]
        error_lines.append("Could not find hooks under:")

        # Show project root search (if available)
        if self.project_root:
            root_hooks = list(self.project_root.glob("*_hook.py"))
            if root_hooks:
                error_lines.append(
                    f"  - {self.project_root} (found {len(root_hooks)} *_hook.py files)"
                )
            else:
                error_lines.append(
                    f"  - {self.project_root} (no *_hook.py files found)"
                )

        # Show configured search paths
        cwd = Path.cwd()
        for search_path in self.hook_search_paths:
            # Handle both absolute and relative paths
            if Path(search_path).is_absolute():
                search_dir = Path(search_path)
            else:
                # Always relative to current working directory
                search_dir = cwd / search_path

            if search_dir.exists() and search_dir.is_dir():
                py_files = [
                    f for f in search_dir.glob("*.py") if f.name != "__init__.py"
                ]
                if py_files:
                    error_lines.append(
                        f"  - {search_dir} (found {len(py_files)} .py files)"
                    )
                else:
                    error_lines.append(f"  - {search_dir} (no .py files found)")
            else:
                error_lines.append(f"  - {search_dir} (directory does not exist)")

        return "\n".join(error_lines)


__all__ = ["HookAPI"]
