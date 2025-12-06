import subprocess
from pathlib import Path
from typing import Optional


class GitRepositoryGateway:
    @staticmethod
    def find_git_root() -> Optional[Path]:
        git_root = GitRepositoryGateway._find_git_root_via_command()
        return git_root or GitRepositoryGateway._find_git_root_via_filesystem()

    @staticmethod
    def _find_git_root_via_command() -> Optional[Path]:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
            git_root = Path(result.stdout.strip()).resolve()
            if (git_root / ".git").exists():
                return git_root / ".git"
            return None
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    @staticmethod
    def _find_git_root_via_filesystem() -> Optional[Path]:
        current = Path.cwd()
        for path in [current] + list(current.parents):
            if (path / ".git").exists():
                return path.resolve()
        return None

    def get_installed_hooks(self, hooks_dir: Path) -> dict[str, bool]:
        installed = {}
        for hook_file in hooks_dir.iterdir():
            if hook_file.is_file() and not hook_file.name.endswith(".sample"):
                hook_name = hook_file.name
                is_tool_installed = self._is_hook_from_githooklib(hook_file)
                installed[hook_name] = is_tool_installed
        return installed

    @staticmethod
    def _is_hook_from_githooklib(hook_path: Path) -> bool:
        try:
            content = hook_path.read_text()
            return "githooklib" in content and "find_project_root" in content
        except (OSError, IOError, UnicodeDecodeError):
            return False

    @staticmethod
    def is_git_root(path: Path) -> bool:
        return (path / ".git").exists()


__all__ = ["GitRepositoryGateway"]
