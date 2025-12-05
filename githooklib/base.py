from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import traceback
import logging
from pathlib import Path

from .context import GitHookContext
from .command import CommandExecutor
from .logger import Logger


DELEGATOR_SCRIPT_TEMPLATE = """#!/usr/bin/env python3

import sys
from pathlib import Path


def find_project_root(module_name):
    # Convert module name to file path (e.g., "githooks.pre_push" -> "githooks/pre_push.py")
    module_path_parts = module_name.split(".")
    module_file_path = Path(*module_path_parts).with_suffix(".py")
    
    current = Path(__file__).resolve()
    for path in [current] + list(current.parents):
        resolved_path = path.resolve()
        # Check if the module file exists at this path and githooklib exists
        module_file = resolved_path / module_file_path
        if module_file.exists() and (resolved_path / "githooklib").exists():
            return resolved_path
    return None


def main():
    module_name = "{module_name}"
    project_root = find_project_root(module_name)
    if not project_root:
        print("Error: Could not find project root containing " + module_name, file=sys.stderr)
        module_file_path = "/".join(module_name.split(".")) + ".py"
        print("Looked for module file: " + module_file_path, file=sys.stderr)
        sys.exit(1)
    sys.path.insert(0, str(project_root))
    from {module_name} import {class_name}
    hook = {class_name}()
    exit_code = hook.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
"""


@dataclass
class HookResult:
    success: bool
    message: Optional[str] = None
    exit_code: int = 0

    def __post_init__(self):
        if self.exit_code == 0 and not self.success:
            self.exit_code = 1
        elif self.exit_code != 0 and self.success:
            self.exit_code = 0

    def __bool__(self) -> bool:
        return self.success


class BaseHook(ABC):
    _registered_hooks: list[type["BaseHook"]] = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseHook._validate_hook_constructor(cls)
        BaseHook._registered_hooks.append(cls)

    @staticmethod
    def _validate_hook_constructor(hook_class: type["BaseHook"]):
        try:
            instance = hook_class()
            if not isinstance(instance, BaseHook):
                raise TypeError(f"{hook_class.__name__} must be a subclass of BaseHook")
        except TypeError as e:
            if "required" in str(e).lower() or "missing" in str(e).lower():
                raise TypeError(
                    f"{hook_class.__name__} must have a constructor that can be called with no arguments. "
                    f"Error: {e}"
                ) from e
            raise
        except Exception as e:
            raise TypeError(
                f"{hook_class.__name__} constructor raised an error when called with no arguments: {e}"
            ) from e

    @classmethod
    def get_registered_hooks(cls) -> list[type["BaseHook"]]:
        return cls._registered_hooks.copy()

    def __init__(self, hook_name: str, logger_prefix: Optional[str] = None, log_level: int = logging.INFO):
        self.hook_name = hook_name
        prefix = logger_prefix or f"[{hook_name}]"
        self.logger = Logger(prefix=prefix, level=log_level)
        self.command_executor = CommandExecutor(logger=self.logger)

    def run(self) -> int:
        try:
            context = GitHookContext.from_stdin(self.hook_name)
            result = self.execute(context)
            return result.exit_code
        except Exception as e:
            self._handle_error(e)
            return 1

    def _handle_error(self, error: Exception):
        self.logger.error(f"Unexpected error in hook: {error}")
        self.logger.error(traceback.format_exc())

    @abstractmethod
    def execute(self, context: GitHookContext) -> HookResult:
        pass

    def install(self) -> bool:
        hooks_dir = self._validate_installation_prerequisites()
        if not hooks_dir:
            return False
        module_name, class_name = self._get_module_and_class()
        project_root = self._find_project_root(module_name)
        if not project_root:
            self.logger.error(f"Could not find project root containing {module_name}")
            return False
        hook_script_path = hooks_dir / self.hook_name
        script_content = self._generate_delegator_script(module_name, class_name)
        return self._write_hook_script(hook_script_path, script_content)

    def _validate_installation_prerequisites(self) -> Optional[Path]:
        git_root = self._find_git_root()
        if not git_root:
            self.logger.error("Not a git repository")
            return None
        hooks_dir = git_root / ".git" / "hooks"
        if not hooks_dir.exists():
            self.logger.error(f"Hooks directory not found: {hooks_dir}")
            return None
        return hooks_dir

    def uninstall(self) -> bool:
        git_root = self._find_git_root()
        if not git_root:
            self.logger.error("Not a git repository")
            return False
        hook_script_path = git_root / ".git" / "hooks" / self.hook_name
        if not hook_script_path.exists():
            self.logger.warning(f"Hook script not found: {hook_script_path}")
            return False
        try:
            hook_script_path.unlink()
            self.logger.success(f"Uninstalled hook: {self.hook_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to uninstall hook: {e}")
            return False

    def _find_git_root(self) -> Optional[Path]:
        current = Path.cwd()
        for path in [current] + list(current.parents):
            if (path / ".git").exists():
                return path.resolve()
        return None

    def _get_module_and_class(self) -> tuple[str, str]:
        module_name = self.__class__.__module__
        class_name = self.__class__.__name__
        return module_name, class_name

    def _find_project_root(self, module_name: str) -> Optional[Path]:
        # Convert module name to file path (e.g., "githooks.pre_push" -> "githooks/pre_push.py")
        module_path_parts = module_name.split(".")
        module_file_path = Path(*module_path_parts).with_suffix(".py")
        
        current = Path.cwd()
        searched_paths = []
        for path in [current] + list(current.parents):
            resolved_path = path.resolve()
            searched_paths.append(resolved_path)
            
            # Check if the module file exists at this path and githooklib exists
            module_file = resolved_path / module_file_path
            if module_file.exists() and (resolved_path / "githooklib").exists():
                return resolved_path
        
        # If not found, show the full resolved path that was checked
        full_module_path = current.resolve() / module_file_path
        self.logger.error(
            f"Could not find project root containing {module_name}. "
            f"Checked for module file at: {full_module_path} "
            f"(resolved from CWD: {current.resolve()}). "
            f"Searched in directories: {', '.join(str(p) for p in searched_paths)}"
        )
        return None

    def _generate_delegator_script(self, module_name: str, class_name: str) -> str:
        return DELEGATOR_SCRIPT_TEMPLATE.format(
            module_name=module_name,
            class_name=class_name
        )

    def _write_hook_script(self, hook_script_path: Path, script_content: str) -> bool:
        try:
            self._write_script_file(hook_script_path, script_content)
            self._make_script_executable(hook_script_path)
            self.logger.success(f"Installed hook: {self.hook_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to install hook: {e}")
            return False

    def _write_script_file(self, hook_script_path: Path, script_content: str):
        hook_script_path.write_text(script_content)

    def _make_script_executable(self, hook_script_path: Path):
        hook_script_path.chmod(0o755)


__all__ = [
    "HookResult",
    "BaseHook"
]
