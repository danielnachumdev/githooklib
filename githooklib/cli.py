import sys
import fire
from pathlib import Path
from typing import Optional

from .api import HookAPI


class CLI:
    """CLI interface for managing Git hooks. Delegates all business logic to HookAPI."""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        hook_search_paths: Optional[list[str]] = None,
    ):
        """Initialize the CLI with an API instance.

        Args:
            project_root: Optional project root path. If not provided, will be auto-detected.
            hook_search_paths: Optional list of hook search paths. Defaults to ["githooks"].
        """
        self.api = HookAPI(
            project_root=project_root, hook_search_paths=hook_search_paths
        )

    def list(self) -> None:
        """List all available hooks."""
        try:
            hook_names = self.api.list_hooks()
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return

        if not hook_names:
            print("No hooks found")
            return

        print("Available hooks:")
        for hook_name in hook_names:
            print(f"  - {hook_name}")

    def show(self) -> None:
        """Show currently installed hooks."""
        installed_hooks = self.api.get_installed_hooks()

        if not installed_hooks:
            # get_installed_hooks returns empty dict if not in git repo or no hooks dir
            # We need to check which case it is for better error messages
            git_root = self.api.get_git_root()
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
        """Run a hook explicitly (useful for debugging).

        Args:
            hook_name: Name of the hook to run
            debug: Enable debug level logging

        Returns:
            0 on success, 1 on failure
        """
        try:
            hooks = self.api.discover_hooks()
            if hook_name not in hooks:
                error_msg = self.api.get_hook_not_found_error_message(hook_name)
                print(error_msg, file=sys.stderr)
                return 1
            # Hook exists, run it
            return self.api.run_hook(hook_name, debug=debug)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def install(self, hook_name: str) -> int:
        """Install a hook.

        Args:
            hook_name: Name of the hook to install

        Returns:
            0 on success, 1 on failure
        """
        try:
            hooks = self.api.discover_hooks()
            if hook_name not in hooks:
                error_msg = self.api.get_hook_not_found_error_message(hook_name)
                print(error_msg, file=sys.stderr)
                return 1
            # Hook exists, install it
            success = self.api.install_hook(hook_name)
            return 0 if success else 1
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def uninstall(self, hook_name: str) -> int:
        """Uninstall a hook.

        Args:
            hook_name: Name of the hook to uninstall

        Returns:
            0 on success, 1 on failure
        """
        try:
            hooks = self.api.discover_hooks()
            if hook_name not in hooks:
                error_msg = self.api.get_hook_not_found_error_message(hook_name)
                print(error_msg, file=sys.stderr)
                return 1
            # Hook exists, uninstall it
            success = self.api.uninstall_hook(hook_name)
            return 0 if success else 1
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def set_hook_paths(self, *hook_paths: str) -> None:
        """Set hook search paths. Can specify multiple paths.

        Example:
            cli.set_hook_paths("githooks", "custom_hooks")
        """
        self.api.set_hook_paths(*hook_paths)


def main() -> None:
    cli = CLI()
    result = fire.Fire(cli)
    if isinstance(result, int):
        sys.exit(result)
    sys.exit(0)


if __name__ == "__main__":
    main()

__all__ = ["CLI"]
