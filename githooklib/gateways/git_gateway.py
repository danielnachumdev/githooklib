import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Optional, Dict

from ..logger import get_logger

logger = get_logger()


class GitGateway:
    @staticmethod
    @lru_cache
    def get_git_root_path() -> Optional[Path]:
        result = (
            GitGateway._find_git_root_via_command()
            or GitGateway._find_git_root_via_filesystem()
        )
        logger.trace("git root: %s", result)
        return result

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
                git_dir = git_root / ".git"
                return git_dir
            return None
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            return None

    @staticmethod
    def _find_git_root_via_filesystem() -> Optional[Path]:
        current = Path.cwd()
        for path in [current] + list(current.parents):
            if (path / ".git").exists():
                resolved = path.resolve()
                return resolved
        return None

    @lru_cache
    def get_installed_hooks(self, hooks_dir: Path) -> Dict[str, bool]:
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
            has_delegation_pattern = (
                "-m" in content and "githooklib" in content and "run" in content
            )
            return has_delegation_pattern
        except (OSError, IOError, UnicodeDecodeError) as e:
            return False


__all__ = ["GitGateway"]
