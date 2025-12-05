import sys
from pathlib import Path
from typing import Optional

from .api import API


class CLI:
    def __init__(
        self,
        project_root: Optional[Path] = None,
        hook_search_paths: Optional[list[str]] = None,
    ):
        self._api = API(project_root=project_root,
                        hook_search_paths=hook_search_paths)

    def list(self) -> None:
        """List all available hooks in the project."""
        try:
            hook_names = self._api.list_hooks()
        except ValueError as e:
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

    def run(self, hook_name: str, debug: bool = False) -> int:
        """Run a hook manually for testing purposes.

        Args:
            hook_name: Name of the hook to run
            debug: Enable debug logging

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            if not self._validate_hook_exists(hook_name):
                return 1
            return self._api.run_hook(hook_name, debug=debug)
        except ValueError as e:
            self._print_error(str(e))
            return 1

    def install(self, hook_name: str) -> int:
        """Install a hook to .git/hooks/.

        Args:
            hook_name: Name of the hook to install

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            if not self._validate_hook_exists(hook_name):
                return 1
            success = self._api.install_hook(hook_name)
            return 0 if success else 1
        except ValueError as e:
            self._print_error(str(e))
            return 1

    def uninstall(self, hook_name: str) -> int:
        """Uninstall a hook from .git/hooks/.

        Args:
            hook_name: Name of the hook to uninstall

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            if not self._validate_hook_exists(hook_name):
                return 1
            success = self._api.uninstall_hook(hook_name)
            return 0 if success else 1
        except ValueError as e:
            self._print_error(str(e))
            return 1

    def _validate_hook_exists(self, hook_name: str) -> bool:
        hooks = self._api.discover_hooks()
        if hook_name not in hooks:
            error_msg = self._api.get_hook_not_found_error_message(hook_name)
            self._print_error(error_msg)
            return False
        return True

    def _print_error(self, message: str) -> None:
        print(f"Error: {message}", file=sys.stderr)

    def seed(self, example_name: Optional[str] = None) -> int:
        """Seed an example hook from the examples folder to githooks/.

        If no example_name is provided, lists all available examples.

        Args:
            example_name: Name of the example to seed (filename without .py extension)

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        if example_name is None:
            available_examples = self._api.get_available_examples()
            if not available_examples:
                print("No example hooks available")
                return 1
            print("Available example hooks:")
            for example in available_examples:
                print(f"  - {example}")
            return 0

        try:
            success = self._api.seed_hook(example_name)
            if not success:
                available_examples = self._api.get_available_examples()
                if example_name not in available_examples:
                    self._print_error(
                        f"Example '{example_name}' not found. "
                        f"Available examples: {', '.join(available_examples)}"
                    )
                else:
                    target_file = (
                            self._api.project_root /
                        "githooks" / f"{example_name}.py"
                    )
                    if target_file.exists():
                        self._print_error(
                            f"Example '{example_name}' already exists at {target_file}"
                        )
                    else:
                        self._print_error(
                            f"Failed to seed example '{example_name}'. "
                            "Project root not found."
                        )
                return 1
            print(f"Successfully seeded example '{example_name}' to githooks/")
            return 0
        except Exception as e:
            self._print_error(f"Error seeding example: {e}")
            return 1


__all__ = ["CLI"]
