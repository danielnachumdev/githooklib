import sys
from typing import Optional

from .api import API
from .constants import EXIT_SUCCESS, EXIT_FAILURE
from .logger import get_logger

logger = get_logger()


class CLI:
    @staticmethod
    def _print_error(message: str) -> None:
        print(f"Error: {message}", file=sys.stderr)

    def __init__(self) -> None:
        self._api = API()

    def list(self) -> None:
        """List all available hooks in the project."""
        try:
            hook_names = self._api.list_hooks()
        except ValueError as e:
            logger.error("Error listing hooks: %s", e)
            self._print_error(str(e))
            return

        if not hook_names:
            print("No hooks found")
            return

        print("Available hooks:")
        for hook_name in hook_names:
            print(f"  - {hook_name}")

    def show(self) -> None:
        """Show all installed git hooks and their installation source."""
        installed_hooks = self._api.get_installed_hooks()

        if not installed_hooks:
            git_root = self._api.get_git_root()
            if not git_root:
                print("Not in a git repository", file=sys.stderr)
            else:
                hooks_dir = git_root / ".git" / "hooks"
                if not hooks_dir.exists():
                    print("No hooks directory found")
                else:
                    print("No hooks installed")
            return

        print("Installed hooks:")
        for hook_name, installed_via_tool in sorted(installed_hooks.items()):
            source = "via tool" if installed_via_tool else "external"
            print(f"  - {hook_name} ({source})")

    def run(self, hook_name: str) -> int:
        """Run a hook manually for testing purposes.

        Args:
            hook_name: Name of the hook to run

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            if not self._hook_exists(hook_name):
                logger.warning("Hook '%s' does not exist", hook_name)
                return EXIT_FAILURE
            return self._api.run_hook(hook_name)
        except ValueError as e:
            logger.error("Error running hook '%s': %s", hook_name, e)
            self._print_error(str(e))
            return EXIT_FAILURE

    def install(self, hook_name: str) -> int:
        """Install a hook to .git/hooks/.

        Args:
            hook_name: Name of the hook to install

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            if not self._hook_exists(hook_name):
                logger.warning("Hook '%s' does not exist, cannot install", hook_name)
                return EXIT_FAILURE
            success = self._api.install_hook(hook_name)
            if success:
                logger.success("Installed hook '%s'", hook_name)
            else:
                logger.warning("Failed to install hook '%s'", hook_name)
            return EXIT_SUCCESS if success else EXIT_FAILURE
        except Exception as e:
            logger.error("Error installing hook '%s': %s", hook_name, e)
            self._print_error(str(e))
            return EXIT_FAILURE

    def uninstall(self, hook_name: str) -> int:
        """Uninstall a hook from .git/hooks/.

        Args:
            hook_name: Name of the hook to uninstall

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            if not self._hook_exists(hook_name):
                logger.warning("Hook '%s' does not exist, cannot uninstall", hook_name)
                return EXIT_FAILURE
            success = self._api.uninstall_hook(hook_name)
            if success:
                logger.info("Successfully uninstalled hook '%s'", hook_name)
            else:
                logger.warning("Failed to uninstall hook '%s'", hook_name)
            return EXIT_SUCCESS if success else EXIT_FAILURE
        except ValueError as e:
            logger.error("Error uninstalling hook '%s': %s", hook_name, e)
            self._print_error(str(e))
            return EXIT_FAILURE

    def _hook_exists(self, hook_name: str) -> bool:
        hooks = self._api.discover_hooks()
        if hook_name not in hooks:
            error_msg = self._api.get_hook_not_found_error_message(hook_name)
            self._print_error(error_msg)
            return False
        return True

    def seed(self, example_name: Optional[str] = None) -> int:
        """Seed an example hook from the examples folder to githooks/.

        If no example_name is provided, lists all available examples.

        Args:
            example_name: Name of the example to seed (filename without .py extension)

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        if example_name is None:
            return self._list_available_examples()
        return self._seed_example_hook(example_name)

    def _list_available_examples(self) -> int:
        available_examples = self._api.get_available_examples()
        if not available_examples:
            print("No example hooks available")
            return EXIT_FAILURE
        print("Available example hooks:")
        for example in available_examples:
            print(f"  - {example}")
        return EXIT_SUCCESS

    def _seed_example_hook(self, example_name: str) -> int:
        try:
            success = self._api.seed_hook(example_name)
            if success:
                logger.info(
                    "Successfully seeded example '%s' to githooks/", example_name
                )
                return EXIT_SUCCESS
            logger.warning("Failed to seed example '%s'", example_name)
            return self._handle_seed_failure(example_name)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error seeding example '%s': %s", example_name, e)
            self._print_error(f"Error seeding example: {e}")
            return EXIT_FAILURE

    def _handle_seed_failure(self, example_name: str) -> int:
        if not self._api.is_example_available(example_name):
            available_examples = self._api.get_available_examples()
            logger.warning(
                "Example '%s' not found. Available: %s",
                example_name,
                available_examples,
            )
            self._print_error(
                f"Example '{example_name}' not found. "
                f"Available examples: {', '.join(available_examples)}"
            )
            return EXIT_FAILURE

        target_path = self._api.get_target_hook_path(example_name)
        if target_path is None:
            logger.warning("Project root not found for example '%s'", example_name)
            self._print_error(
                f"Failed to seed example '{example_name}'. " "Project root not found."
            )
            return EXIT_FAILURE

        if self._api.does_target_hook_exist(example_name):
            logger.warning(
                "Example '%s' already exists at %s", example_name, target_path
            )
            self._print_error(
                f"Example '{example_name}' already exists at {target_path}"
            )
            return EXIT_FAILURE

        logger.warning(
            "Failed to seed example '%s'. Project root not found.", example_name
        )
        self._print_error(
            f"Failed to seed example '{example_name}'. Project root not found."
        )
        return EXIT_FAILURE


__all__ = ["CLI"]
