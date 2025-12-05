import sys
import fire
from pathlib import Path
from typing import Optional

from .api import HookAPI


class CLI:
    def __init__(
        self,
        project_root: Optional[Path] = None,
        hook_search_paths: Optional[list[str]] = None,
    ):
        self.api = HookAPI(
            project_root=project_root, hook_search_paths=hook_search_paths
        )

    def list(self) -> None:
        try:
            hook_names = self.api.list_hooks()
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
        installed_hooks = self.api.get_installed_hooks()

        if not installed_hooks:
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
        try:
            if not self._validate_hook_exists(hook_name):
                return 1
            return self.api.run_hook(hook_name, debug=debug)
        except ValueError as e:
            self._print_error(str(e))
            return 1

    def install(self, hook_name: str) -> int:
        try:
            if not self._validate_hook_exists(hook_name):
                return 1
            success = self.api.install_hook(hook_name)
            return 0 if success else 1
        except ValueError as e:
            self._print_error(str(e))
            return 1

    def uninstall(self, hook_name: str) -> int:
        try:
            if not self._validate_hook_exists(hook_name):
                return 1
            success = self.api.uninstall_hook(hook_name)
            return 0 if success else 1
        except ValueError as e:
            self._print_error(str(e))
            return 1

    def _validate_hook_exists(self, hook_name: str) -> bool:
        hooks = self.api.discover_hooks()
        if hook_name not in hooks:
            error_msg = self.api.get_hook_not_found_error_message(hook_name)
            self._print_error(error_msg)
            return False
        return True

    def _print_error(self, message: str) -> None:
        print(f"Error: {message}", file=sys.stderr)

    def set_hook_paths(self, *hook_paths: str) -> None:
        self.api.set_hook_paths(*hook_paths)


def main() -> None:
    cli = CLI()
    exit_code = fire.Fire(cli)
    if isinstance(exit_code, int):
        sys.exit(exit_code)
    sys.exit(0)


if __name__ == "__main__":
    main()

__all__ = ["CLI"]
