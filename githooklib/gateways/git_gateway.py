import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Optional, Dict

from ..logger import get_logger
from ..utils import singleton

logger = get_logger()


@singleton
class GitGateway:
    @staticmethod
    @lru_cache
    def get_git_root_path() -> Optional[Path]:
        logger.debug("Getting git root path")
        logger.trace("Attempting to find git root via command")
        result_via_command = GitGateway._find_git_root_via_command()
        if result_via_command:
            logger.debug("Found git root via command: %s", result_via_command)
            logger.trace("git root: %s", result_via_command)
            return result_via_command

        logger.trace("Command method failed, trying filesystem search")
        result_via_filesystem = GitGateway._find_git_root_via_filesystem()
        if result_via_filesystem:
            logger.debug("Found git root via filesystem: %s", result_via_filesystem)
            logger.trace("git root: %s", result_via_filesystem)
            return result_via_filesystem

        logger.debug("Git root not found")
        logger.trace("git root: None")
        return None

    @staticmethod
    def _find_git_root_via_command() -> Optional[Path]:
        logger.trace("Finding git root via 'git rev-parse --show-toplevel' command")
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
            git_root = Path(result.stdout.strip()).resolve()
            logger.trace(
                "Command output: %s, resolved to: %s", result.stdout.strip(), git_root
            )
            if (git_root / ".git").exists():
                git_dir = git_root / ".git"
                logger.trace("Found .git directory at: %s", git_dir)
                return git_dir
            logger.trace(".git directory not found at: %s", git_root / ".git")
            return None
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.trace("Command failed: %s", e)
            return None

    @staticmethod
    def _find_git_root_via_filesystem() -> Optional[Path]:
        logger.trace("Finding git root via filesystem traversal")
        current = Path.cwd()
        logger.trace("Starting from current directory: %s", current)
        search_paths = [current] + list(current.parents)
        logger.trace("Search paths: %s", search_paths)
        for path in search_paths:
            git_path = path / ".git"
            logger.trace("Checking for .git at: %s", git_path)
            if git_path.exists():
                resolved = path.resolve()
                logger.trace("Found .git at: %s, resolved to: %s", path, resolved)
                return resolved
        logger.trace("No .git directory found in search paths")
        return None

    @lru_cache
    def get_installed_hooks(self, hooks_dir: Path) -> Dict[str, bool]:
        logger.debug("Getting installed hooks from directory: %s", hooks_dir)
        installed = {}
        logger.trace("Iterating over files in hooks directory")
        for hook_file in hooks_dir.iterdir():
            logger.trace("Checking file: %s", hook_file)
            if hook_file.is_file() and not hook_file.name.endswith(".sample"):
                hook_name = hook_file.name
                logger.trace("Processing hook file: %s", hook_name)
                is_tool_installed = self._is_hook_from_githooklib(hook_file)
                logger.trace(
                    "Hook '%s' installed via githooklib: %s",
                    hook_name,
                    is_tool_installed,
                )
                installed[hook_name] = is_tool_installed
            else:
                logger.trace(
                    "Skipping file (not a hook file or is sample): %s", hook_file.name
                )
        logger.debug("Found %d installed hooks", len(installed))
        logger.trace("Installed hooks: %s", installed)
        return installed

    @staticmethod
    def _is_hook_from_githooklib(hook_path: Path) -> bool:
        logger.trace("Checking if hook is from githooklib: %s", hook_path)
        try:
            content = hook_path.read_text()
            logger.trace("Hook file content length: %d characters", len(content))
            has_delegation_pattern = (
                "-m" in content and "githooklib" in content and "run" in content
            )
            logger.trace("Delegation pattern found: %s", has_delegation_pattern)
            return has_delegation_pattern
        except (OSError, IOError, UnicodeDecodeError) as e:
            logger.trace("Error reading hook file: %s", e)
            return False


__all__ = ["GitGateway"]
