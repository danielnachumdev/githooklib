from abc import ABC, abstractmethod
from typing import Optional, List, Type, Tuple
import traceback
import logging
import sys
import fnmatch
from pathlib import Path

from .constants import DELEGATOR_SCRIPT_TEMPLATE, EXIT_SUCCESS, EXIT_FAILURE
from .context import GitHookContext
from .command import CommandExecutor
from .logger import get_logger, Logger
from .gateways import GitGateway, ModuleImportGateway, ProjectRootGateway
from .definitions import HookResult


class GitHook(ABC):
    logger: Logger
    _registered_hooks: List[Type["GitHook"]] = []

    @staticmethod
    def _write_script_file(hook_script_path: Path, script_content: str) -> None:
        logger = get_logger()
        logger.trace("Writing script file to: %s", hook_script_path)
        logger.trace("Script content length: %d characters", len(script_content))
        hook_script_path.write_text(script_content)
        logger.trace("Script file written successfully")

    @staticmethod
    def _make_script_executable(hook_script_path: Path) -> None:
        logger = get_logger()
        logger.trace("Making script executable: %s", hook_script_path)
        hook_script_path.chmod(0o755)
        logger.trace("Script made executable (mode 0o755)")

    def _generate_delegator_script(self) -> str:
        hook_name = self.get_hook_name()
        self.logger.trace("Generating delegator script for hook '%s'", hook_name)
        project_root = str(ProjectRootGateway.find_project_root())
        python_executable = sys.executable
        from githooklib import __version__

        return DELEGATOR_SCRIPT_TEMPLATE.format(
            hook_name=self.get_hook_name(),
            project_root=project_root.replace("\\", "\\\\"),
            python_executable=python_executable.replace("\\", "\\\\"),
            installed_version=__version__,
        )

    @classmethod
    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        logger = get_logger()
        GitHook._registered_hooks.append(cls)
        hook_name = cls.get_hook_name()
        cls.logger = get_logger(__name__, hook_name)
        logger.trace("Hook subclass registered: %s -> %s", cls.__name__, hook_name)

    @classmethod
    def get_registered_hooks(cls) -> List[Type["GitHook"]]:
        return cls._registered_hooks.copy()

    @classmethod
    def _get_module_and_class(cls) -> Tuple[str, str]:
        logger = get_logger()
        module_name = cls.__module__
        class_name = cls.__name__
        logger.trace(
            "Getting module and class for %s: module=%s, class=%s",
            cls.__name__,
            module_name,
            class_name,
        )
        return module_name, class_name

    @classmethod
    def get_log_level(cls) -> int:
        logger = get_logger()
        log_level = logging.INFO
        logger.trace("Getting log level for %s: %s", cls.__name__, log_level)
        return log_level

    @classmethod
    @abstractmethod
    def get_hook_name(cls) -> str:
        """
        Return the name of the Git hook this class implements.

        This method must return the exact name of the Git hook (e.g., "pre-commit",
        "pre-push", "post-merge"). The hook name determines when Git will invoke
        this hook during the Git workflow.

        Returns:
            str: The Git hook name (e.g., "pre-commit", "pre-push", "post-merge").

        Examples:
            For a pre-commit hook:
                return "pre-commit"

            For a pre-push hook:
                return "pre-push"
        """

    @classmethod
    @abstractmethod
    def get_file_patterns(cls) -> Optional[List[str]]:
        """
        Return file patterns to determine when this hook should run.

        This method allows hooks to conditionally execute based on which files
        have changed. The hook will only run if at least one changed file matches
        any of the specified patterns.

        Returns:
            Optional[List[str]]: A list of glob patterns (e.g., ["*.py", "src/**/*.ts"]).
                - Return None to always run the hook (no conditional execution).
                - Return an empty list [] to always run the hook.
                - Return a list of patterns to run only when matching files change.

        Examples:
            To run only when Python files change:
                return ["*.py"]

            To run only when Python or TypeScript files change:
                return ["*.py", "src/**/*.ts"]

            To always run (no conditional execution):
                return None

        Note:
            Patterns use fnmatch syntax. The hook checks changed files based on
            hook type: staged files for pre-commit, diff between refs for pre-push,
            or all modified files for other hooks.
        """

    @abstractmethod
    def execute(self, context: GitHookContext) -> HookResult:
        """
        Execute the hook logic.

        This method contains the main logic for the Git hook. It is called when
        the hook is triggered by Git, after checking file patterns (if specified).

        Args:
            context: The GitHookContext containing hook information, command-line
                arguments, project root, and ref information (for pre-push hooks).

        Returns:
            HookResult: A result object indicating success/failure, optional message,
                and exit code. The exit code determines whether Git should proceed
                (0) or abort the operation (non-zero).

        Examples:
            A simple hook that always succeeds:
                return HookResult(success=True, message="All checks passed!")

            A hook that fails with a message:
                return HookResult(
                    success=False,
                    message="Tests failed. Commit aborted.",
                    exit_code=1
                )

        Note:
            - The hook will only be executed if file patterns match (if specified).
            - Use self.command_executor to run shell commands.
            - Use self.logger for logging messages.
        """
        ...

    def __init__(self) -> None:
        hook_name = self.get_hook_name()
        self.command_executor = CommandExecutor()
        self.logger.trace("Hook instance initialized: %s", hook_name)

    def run(self) -> int:
        hook_name = self.get_hook_name()
        self.logger.debug("Running hook '%s'", hook_name)
        try:
            self.logger.trace("Creating hook context from argv")
            context = GitHookContext.from_argv(hook_name)
            self.logger.trace(
                "Hook context: hook_name=%s, argv=%s", context.hook_name, context.argv
            )

            if not self._should_run_based_on_patterns(context):
                self.logger.debug(
                    "Hook '%s' skipped: no changed files match the specified patterns",
                    hook_name,
                )
                return EXIT_SUCCESS

            self.logger.debug("Executing hook '%s'", hook_name)
            result = self.execute(context)
            self.logger.debug(
                "Hook '%s' execution completed with exit code %d",
                hook_name,
                result.exit_code,
            )
            self.logger.trace("Hook result: exit_code=%d", result.exit_code)
            return result.exit_code
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.debug("Exception occurred during hook execution: %s", e)
            self._handle_error(e)
            return EXIT_FAILURE

    def _handle_error(self, error: Exception) -> None:
        self.logger.error("Unexpected error in hook: %s", error)
        self.logger.error(traceback.format_exc())

    def _should_run_based_on_patterns(self, context: GitHookContext) -> bool:
        patterns = self.get_file_patterns()
        if patterns is None:
            self.logger.trace("No file patterns specified, hook will run")
            return True

        if not patterns:
            self.logger.trace("Empty file patterns list, hook will run")
            return True

        changed_files = context.get_changed_files()
        if not changed_files:
            self.logger.trace("No changed files found, hook will not run")
            return False

        self.logger.trace(
            "Checking %d changed files against %d patterns",
            len(changed_files),
            len(patterns),
        )
        for file_path in changed_files:
            for pattern in patterns:
                if fnmatch.fnmatch(file_path, pattern):
                    self.logger.trace(
                        "File '%s' matches pattern '%s', hook will run",
                        file_path,
                        pattern,
                    )
                    return True

        self.logger.trace("No changed files match any pattern, hook will not run")
        return False

    def install(self) -> bool:
        hook_name = self.get_hook_name()
        self.logger.debug("Installing hook '%s'", hook_name)
        hooks_dir = self._validate_installation_prerequisites()
        if not hooks_dir:
            self.logger.warning("Installation prerequisites validation failed")
            self.logger.debug(
                "Cannot install hook '%s': prerequisites not met", hook_name
            )
            return False
        self.logger.trace("Hooks directory validated: %s", hooks_dir)
        project_root = ProjectRootGateway.find_project_root()
        if not project_root:
            self.logger.error("Could not find project root")
            self.logger.debug(
                "Cannot install hook '%s': project root not found", hook_name
            )
            return False
        self.logger.trace("Project root: %s", project_root)
        hook_script_path = hooks_dir / hook_name
        self.logger.trace("Hook script path: %s", hook_script_path)
        self.logger.debug("Generating delegator script for hook '%s'", hook_name)
        script_content = self._generate_delegator_script()
        self.logger.trace(
            "Delegator script generated, length: %d characters", len(script_content)
        )
        self.logger.debug("Writing hook delegation script to %s", hook_script_path)
        return self._write_hook_delegation_script(hook_script_path, script_content)

    def _validate_installation_prerequisites(self) -> Optional[Path]:
        self.logger.debug("Validating installation prerequisites")
        git_gateway = GitGateway()
        git_root = git_gateway.get_git_root_path()
        self.logger.trace("Git root: %s", git_root)
        if not git_root:
            self.logger.error("Not a git repository")
            self.logger.debug("Installation prerequisites failed: not a git repository")
            return None
        hooks_dir = git_root / "hooks"
        self.logger.trace("Hooks directory: %s", hooks_dir)
        if not hooks_dir.exists():
            self.logger.error("Hooks directory not found: %s", hooks_dir)
            self.logger.debug(
                "Installation prerequisites failed: hooks directory does not exist"
            )
            return None
        self.logger.debug("Installation prerequisites validated successfully")
        return hooks_dir

    def uninstall(self) -> bool:
        hook_name = self.get_hook_name()
        self.logger.debug("Uninstalling hook '%s'", hook_name)
        git_gateway = GitGateway()
        git_root = git_gateway.get_git_root_path()
        self.logger.trace("Git root: %s", git_root)
        if not git_root:
            self.logger.error("Not a git repository")
            self.logger.debug(
                "Cannot uninstall hook '%s': not a git repository", hook_name
            )
            return False
        hook_script_path = git_root / "hooks" / hook_name
        self.logger.trace("Hook script path: %s", hook_script_path)
        if not hook_script_path.exists():
            self.logger.warning("Hook script not found: %s", hook_script_path)
            self.logger.debug(
                "Cannot uninstall hook '%s': script file does not exist", hook_name
            )
            return False
        try:
            self.logger.debug("Removing hook script file: %s", hook_script_path)
            hook_script_path.unlink()
            self.logger.success("Uninstalled hook: %s", hook_name)
            self.logger.debug(
                "Hook '%s' uninstallation completed successfully", hook_name
            )
            return True
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error("Failed to uninstall hook: %s", e)
            self.logger.trace("Exception details: %s", e, exc_info=True)
            self.logger.debug("Hook '%s' uninstallation failed", hook_name)
            return False

    def _log_project_root_not_found(self, module_name: str) -> None:
        self.logger.debug("Logging project root not found for module: %s", module_name)
        module_file_path = ModuleImportGateway.convert_module_name_to_file_path(
            module_name
        )
        self.logger.trace("Module file path: %s", module_file_path)
        current = Path.cwd()
        searched_paths = [current] + list(current.parents)
        self.logger.trace("Searched paths: %s", searched_paths)
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
        self.logger.trace("Project root not found error logged")

    def _write_hook_delegation_script(
        self, hook_script_path: Path, script_content: str
    ) -> bool:
        hook_name = self.get_hook_name()
        self.logger.debug("Writing hook delegation script to %s", hook_script_path)
        self.logger.trace("Script content length: %d characters", len(script_content))
        try:
            self.logger.trace("Writing script file")
            self._write_script_file(hook_script_path, script_content)
            self.logger.trace("Making script executable")
            self._make_script_executable(hook_script_path)
            self.logger.debug(
                "Hook '%s' installation completed successfully", hook_name
            )
            return True
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error("Failed to install hook: %s", e)
            self.logger.trace("Exception details: %s", e, exc_info=True)
            self.logger.debug("Hook '%s' installation failed", hook_name)
            return False


__all__ = [
    "HookResult",
    "GitHook",
]
