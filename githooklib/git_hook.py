from abc import ABC, abstractmethod
from typing import Optional, List, Type, Tuple
import traceback
import logging
from pathlib import Path

from .constants import DELEGATOR_SCRIPT_TEMPLATE, EXIT_SUCCESS, EXIT_FAILURE
from .context import GitHookContext
from .command import CommandExecutor
from .logger import get_logger
from .gateways import GitRepositoryGateway, ModuleImportGateway, ProjectRootGateway
from .definitions import HookResult


class GitHook(ABC):
    _registered_hooks: List[Type["GitHook"]] = []

    @staticmethod
    def _write_script_file(hook_script_path: Path, script_content: str) -> None:
        hook_script_path.write_text(script_content)

    @staticmethod
    def _make_script_executable(hook_script_path: Path) -> None:
        hook_script_path.chmod(0o755)

    @staticmethod
    def _generate_delegator_script(module_name: str, class_name: str) -> str:
        return DELEGATOR_SCRIPT_TEMPLATE.format(
            module_name=module_name, class_name=class_name
        )

    @classmethod
    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        GitHook._registered_hooks.append(cls)

    @classmethod
    def get_registered_hooks(cls) -> List[Type["GitHook"]]:
        return cls._registered_hooks.copy()

    @classmethod
    def _get_module_and_class(cls) -> Tuple[str, str]:
        module_name = cls.__module__
        class_name = cls.__name__
        return module_name, class_name

    @classmethod
    def get_log_level(cls) -> int:
        return logging.INFO

    @property
    @abstractmethod
    def hook_name(self) -> str: ...

    @abstractmethod
    def execute(self, context: GitHookContext) -> HookResult: ...

    def __init__(self) -> None:
        self.command_executor = CommandExecutor()

    def run(self) -> int:
        try:
            context = GitHookContext.from_stdin(self.hook_name)
            result = self.execute(context)
            return result.exit_code
        except Exception as e:  # pylint: disable=broad-exception-caught
            self._handle_error(e)
            return EXIT_FAILURE

    def _handle_error(self, error: Exception) -> None:
        self.logger.error("Unexpected error in hook: %s", error)
        self.logger.error(traceback.format_exc())

    def install(self) -> bool:
        hooks_dir = self._validate_installation_prerequisites()
        if not hooks_dir:
            self.logger.warning("Installation prerequisites validation failed")
            return False
        module_name, class_name = self._get_module_and_class()
        project_root = ProjectRootGateway.find_project_root()
        if not project_root:
            self.logger.error("Could not find project root containing %s", module_name)
            return False
        hook_script_path = hooks_dir / self.hook_name
        script_content = self._generate_delegator_script(module_name, class_name)
        return self._write_hook_delegation_script(hook_script_path, script_content)

    def _validate_installation_prerequisites(self) -> Optional[Path]:
        git_root = GitRepositoryGateway.find_git_root()
        if not git_root:
            self.logger.error("Not a git repository")
            return None
        hooks_dir = git_root / "hooks"
        if not hooks_dir.exists():
            self.logger.error("Hooks directory not found: %s", hooks_dir)
            return None
        return hooks_dir

    def uninstall(self) -> bool:
        git_root = GitRepositoryGateway.find_git_root()
        if not git_root:
            self.logger.error("Not a git repository")
            return False
        hook_script_path = git_root / ".git" / "hooks" / self.hook_name
        if not hook_script_path.exists():
            self.logger.warning("Hook script not found: %s", hook_script_path)
            return False
        try:
            hook_script_path.unlink()
            self.logger.success("Uninstalled hook: %s", self.hook_name)
            return True
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error("Failed to uninstall hook: %s", e)
            return False

    def _log_project_root_not_found(self, module_name: str) -> None:
        module_file_path = ModuleImportGateway.convert_module_name_to_file_path(
            module_name
        )
        current = Path.cwd()
        searched_paths = [current] + list(current.parents)
        full_module_path = current.resolve() / module_file_path
        searched_dirs = ", ".join(str(p.resolve()) for p in searched_paths)
        self.logger.error(
            "Could not find project root containing %s. "
            "Checked for module file at: %s "
            "(resolved from CWD: %s). "
            "Searched in directories: %s",
            module_name,
            full_module_path,
            current.resolve(),
            searched_dirs,
        )

    def _write_hook_delegation_script(
        self, hook_script_path: Path, script_content: str
    ) -> bool:
        try:
            self._write_script_file(hook_script_path, script_content)
            self._make_script_executable(hook_script_path)
            self.logger.success("Installed hook: %s", self.hook_name)
            return True
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error("Failed to install hook: %s", e)
            return False


__all__ = [
    "HookResult",
    "GitHook",
]
