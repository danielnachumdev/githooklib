import sys
from typing import Optional

from .api import API
from .constants import EXIT_SUCCESS, EXIT_FAILURE
from .logger import get_logger
from .ui_messages import (
    UI_MESSAGE_AVAILABLE_HOOKS_HEADER,
    UI_MESSAGE_NO_HOOKS_FOUND,
    UI_MESSAGE_INSTALLED_HOOKS_HEADER,
    UI_MESSAGE_NOT_IN_GIT_REPOSITORY,
    UI_MESSAGE_NO_HOOKS_DIRECTORY_FOUND,
    UI_MESSAGE_NO_HOOKS_INSTALLED,
    UI_MESSAGE_AVAILABLE_EXAMPLE_HOOKS_HEADER,
    UI_MESSAGE_NO_EXAMPLE_HOOKS_AVAILABLE,
    UI_MESSAGE_ERROR_PREFIX,
    UI_MESSAGE_HOOK_SOURCE_GITHOOKLIB,
    UI_MESSAGE_HOOK_SOURCE_EXTERNAL,
    UI_MESSAGE_EXAMPLE_NOT_FOUND_PREFIX,
    UI_MESSAGE_EXAMPLE_NOT_FOUND_SUFFIX,
    UI_MESSAGE_EXAMPLE_ALREADY_EXISTS_PREFIX,
    UI_MESSAGE_EXAMPLE_ALREADY_EXISTS_SUFFIX,
    UI_MESSAGE_FAILED_TO_SEED_EXAMPLE_PREFIX,
    UI_MESSAGE_FAILED_TO_SEED_EXAMPLE_PROJECT_ROOT_NOT_FOUND,
    UI_MESSAGE_ERROR_SEEDING_EXAMPLE_PREFIX,
)

logger = get_logger()


def print_error(message: str) -> None:
    print(f"{UI_MESSAGE_ERROR_PREFIX}{message}", file=sys.stderr)


class CLI:
    """Command-line interface for githooklib.

    This class provides a command-line interface for managing Git hooks in Python
    projects. It enables discovery, installation, uninstallation, and execution of
    Git hooks defined in the project. Hooks are automatically discovered from the
    'githooks' directory or project root.

    All commands support --debug flag for additional logging
    information.
    """

    def __init__(self) -> None:
        logger.trace("Initializing CLI")
        self._api = API()

    def list(self) -> None:
        """List all available hooks in the project."""
        try:
            hook_names = self._api.list_available_hook_names()
        except ValueError as e:
            logger.error("%s%s", UI_MESSAGE_ERROR_PREFIX, e)
            logger.trace("Exception details: %s", e, exc_info=True)
            print_error(str(e))
            return

        if not hook_names:
            logger.error(UI_MESSAGE_NO_HOOKS_FOUND)
            logger.debug("No hooks found in project")
            return

        print(UI_MESSAGE_AVAILABLE_HOOKS_HEADER)
        for hook_name in hook_names:
            print(f"  - {hook_name}")

    def show(self) -> None:
        """Show all installed git hooks and their installation source."""
        logger.debug("Executing show command")
        context = self._api.get_installed_hooks_with_context()

        if not context.installed_hooks:
            if not context.git_root:
                logger.error(UI_MESSAGE_NOT_IN_GIT_REPOSITORY)
                logger.debug("Not in a git repository")
            elif not context.hooks_dir_exists:
                logger.error(UI_MESSAGE_NO_HOOKS_DIRECTORY_FOUND)
                logger.debug("Hooks directory does not exist")
            else:
                logger.error(UI_MESSAGE_NO_HOOKS_INSTALLED)
                logger.debug("No hooks installed")
            return

        logger.debug("Displaying %d installed hooks", len(context.installed_hooks))
        logger.trace("Installed hooks: %s", context.installed_hooks)
        print(UI_MESSAGE_INSTALLED_HOOKS_HEADER)
        for hook_name, installed_via_tool in sorted(context.installed_hooks.items()):
            source = (
                UI_MESSAGE_HOOK_SOURCE_GITHOOKLIB
                if installed_via_tool
                else UI_MESSAGE_HOOK_SOURCE_EXTERNAL
            )
            logger.trace("Hook '%s' source: %s", hook_name, source)
            print(f"  - {hook_name} ({source})")

    def run(self, hook_name: str) -> int:
        """Run a hook manually for testing purposes.

        Args:
            hook_name: Name of the hook to run

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        logger.debug("Executing run command for hook '%s'", hook_name)
        try:
            if not self._api.check_hook_exists(hook_name):
                error_msg = self._api.get_hook_not_found_error_message(hook_name)
                print_error(error_msg)
                logger.warning("Hook '%s' does not exist", hook_name)
                logger.debug("Hook '%s' not found, cannot run", hook_name)
                return EXIT_FAILURE
            logger.debug("Running hook '%s'", hook_name)
            exit_code = self._api.run_hook_by_name(hook_name)
            logger.debug("Hook '%s' completed with exit code %d", hook_name, exit_code)
            return exit_code
        except ValueError as e:
            logger.error("Error running hook '%s': %s", hook_name, e)
            logger.trace("Exception details: %s", e, exc_info=True)
            print_error(str(e))
            return EXIT_FAILURE

    def install(self, hook_name: str) -> int:
        """Install a hook to .git/hooks/.

        Args:
            hook_name: Name of the hook to install

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        logger.debug("Executing install command for hook '%s'", hook_name)
        try:
            if not self._api.check_hook_exists(hook_name):
                error_msg = self._api.get_hook_not_found_error_message(hook_name)
                print_error(error_msg)
                logger.warning("Hook '%s' does not exist, cannot install", hook_name)
                logger.debug("Hook '%s' not found, cannot install", hook_name)
                return EXIT_FAILURE
            logger.debug("Installing hook '%s'", hook_name)
            success = self._api.install_hook_by_name(hook_name)
            if success:
                logger.success("Installed hook '%s'", hook_name)
                logger.debug("Hook '%s' installation completed successfully", hook_name)
            else:
                logger.warning("Failed to install hook '%s'", hook_name)
                logger.debug("Hook '%s' installation failed", hook_name)
            return EXIT_SUCCESS if success else EXIT_FAILURE
        except Exception as e:
            logger.error("Error installing hook '%s': %s", hook_name, e)
            logger.trace("Exception details: %s", e, exc_info=True)
            print_error(str(e))
            return EXIT_FAILURE

    def uninstall(self, hook_name: str) -> int:
        """Uninstall a hook from .git/hooks/.

        Args:
            hook_name: Name of the hook to uninstall

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        logger.debug("Executing uninstall command for hook '%s'", hook_name)
        try:
            if not self._api.check_hook_exists(hook_name):
                error_msg = self._api.get_hook_not_found_error_message(hook_name)
                print_error(error_msg)
                logger.warning("Hook '%s' does not exist, cannot uninstall", hook_name)
                logger.debug("Hook '%s' not found, cannot uninstall", hook_name)
                return EXIT_FAILURE
            logger.debug("Uninstalling hook '%s'", hook_name)
            success = self._api.uninstall_hook_by_name(hook_name)
            if success:
                logger.info("Successfully uninstalled hook '%s'", hook_name)
                logger.debug(
                    "Hook '%s' uninstallation completed successfully", hook_name
                )
            else:
                logger.warning("Failed to uninstall hook '%s'", hook_name)
                logger.debug("Hook '%s' uninstallation failed", hook_name)
            return EXIT_SUCCESS if success else EXIT_FAILURE
        except ValueError as e:
            logger.error("Error uninstalling hook '%s': %s", hook_name, e)
            logger.trace("Exception details: %s", e, exc_info=True)
            print_error(str(e))
            return EXIT_FAILURE

    def seed(self, example_name: Optional[str] = None) -> int:
        """Seed an example hook from the examples folder to githooks/.

        If no example_name is provided, lists all available examples.

        Args:
            example_name: Name of the example to seed (filename without .py extension)

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        logger.debug(
            "Executing seed command%s",
            f" for example '{example_name}'" if example_name else "",
        )
        if example_name is None:
            logger.debug("No example name provided, listing available examples")
            available_examples = self._api.list_available_example_names()
            if not available_examples:
                logger.error(UI_MESSAGE_NO_EXAMPLE_HOOKS_AVAILABLE)
                logger.debug("No examples available")
                return EXIT_FAILURE
            logger.debug("Displaying %d available examples", len(available_examples))
            print(UI_MESSAGE_AVAILABLE_EXAMPLE_HOOKS_HEADER)
            for example in available_examples:
                print(f"  - {example}")
            return EXIT_SUCCESS

        try:
            logger.debug("Seeding example '%s' to project", example_name)
            success = self._api.seed_example_hook_to_project(example_name)
            if success:
                logger.info(
                    "Successfully seeded example '%s' to githooks/", example_name
                )
                logger.debug(
                    "Example '%s' seeding completed successfully", example_name
                )
                return EXIT_SUCCESS

            logger.warning("Failed to seed example '%s'", example_name)
            logger.debug("Getting failure details for example '%s'", example_name)
            failure_details = self._api.get_seed_failure_details(example_name)

            if failure_details.example_not_found:
                logger.warning(
                    "Example '%s' not found. Available: %s",
                    example_name,
                    failure_details.available_examples,
                )
                logger.debug(
                    "Example '%s' not found in available examples", example_name
                )
                print_error(
                    f"{UI_MESSAGE_EXAMPLE_NOT_FOUND_PREFIX}"
                    f"{example_name}"
                    f"{UI_MESSAGE_EXAMPLE_NOT_FOUND_SUFFIX}"
                    f"{', '.join(failure_details.available_examples)}"
                )
                return EXIT_FAILURE

            if failure_details.project_root_not_found:
                logger.warning("Project root not found for example '%s'", example_name)
                logger.debug(
                    "Project root not found, cannot seed example '%s'", example_name
                )
                print_error(
                    f"{UI_MESSAGE_FAILED_TO_SEED_EXAMPLE_PREFIX}"
                    f"{example_name}"
                    f"{UI_MESSAGE_FAILED_TO_SEED_EXAMPLE_PROJECT_ROOT_NOT_FOUND}"
                )
                return EXIT_FAILURE

            if failure_details.target_hook_already_exists:
                target_path = failure_details.target_hook_path
                logger.warning(
                    "Example '%s' already exists at %s", example_name, target_path
                )
                logger.debug("Target hook already exists at %s", target_path)
                if target_path:
                    print_error(
                        f"{UI_MESSAGE_EXAMPLE_ALREADY_EXISTS_PREFIX}"
                        f"{example_name}"
                        f"{UI_MESSAGE_EXAMPLE_ALREADY_EXISTS_SUFFIX}"
                        f"{target_path}"
                    )
                return EXIT_FAILURE

            logger.warning(
                "Failed to seed example '%s'. Project root not found.", example_name
            )
            logger.debug(
                "Unknown failure reason for seeding example '%s'", example_name
            )
            print_error(
                f"{UI_MESSAGE_FAILED_TO_SEED_EXAMPLE_PREFIX}"
                f"{example_name}"
                f"{UI_MESSAGE_FAILED_TO_SEED_EXAMPLE_PROJECT_ROOT_NOT_FOUND}"
            )
            return EXIT_FAILURE
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error seeding example '%s': %s", example_name, e)
            logger.trace("Exception details: %s", e, exc_info=True)
            print_error(f"{UI_MESSAGE_ERROR_SEEDING_EXAMPLE_PREFIX}{e}")
            return EXIT_FAILURE


__all__ = ["CLI"]
