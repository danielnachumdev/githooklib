from functools import lru_cache
from pathlib import Path
from typing import Optional, Dict, List

from ..command import CommandExecutor
from ..logger import get_logger
from ..utils import singleton

logger = get_logger()


@singleton
class GitGateway:
    def __init__(self) -> None:
        self.command_executor = CommandExecutor()

    @lru_cache
    def get_git_root_path(self) -> Optional[Path]:
        logger.debug("Finding Git root")
        logger.trace("Attempting to find git root via command")
        result_via_command = self._find_git_root_via_command()
        if result_via_command:
            logger.debug("Git root: %s", result_via_command)
            logger.trace("git root: %s", result_via_command)
            return result_via_command

        logger.trace("Command method failed, trying filesystem search")
        result_via_filesystem = self._find_git_root_via_filesystem()
        if result_via_filesystem:
            logger.debug("Git root: %s", result_via_filesystem)
            logger.trace("git root: %s", result_via_filesystem)
            return result_via_filesystem

        logger.debug("Git root not found")
        return None

    def _find_git_root_via_command(self) -> Optional[Path]:
        logger.trace("Finding git root via 'git rev-parse --show-toplevel' command")
        result = self.command_executor.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
        )
        if not result.success:
            logger.trace("Command failed: exit_code=%d", result.exit_code)
            return None
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

    def get_cached_index_files(self) -> List[str]:
        logger.debug("Getting cached index files (staged files)")
        logger.trace("Running 'git diff --cached --name-only'")
        result = self.command_executor.run(
            ["git", "diff", "--cached", "--name-only"],
            check=True,
        )
        if not result.success:
            logger.trace("Command failed: exit_code=%d", result.exit_code)
            logger.debug("Failed to get cached index files, returning empty list")
            return []
        files = [
            line.strip() for line in result.stdout.strip().split("\n") if line.strip()
        ]
        logger.trace("Cached index files: %s", files)
        return files

    def get_diff_files_between_refs(self, remote_ref: str, local_ref: str) -> List[str]:
        logger.debug(
            "Getting diff files between refs: remote_ref=%s, local_ref=%s",
            remote_ref,
            local_ref,
        )
        logger.trace("Running 'git diff %s %s --name-only'", remote_ref, local_ref)
        result = self.command_executor.run(
            ["git", "diff", remote_ref, local_ref, "--name-only"],
            check=True,
        )
        if not result.success:
            logger.trace("Command failed: exit_code=%d", result.exit_code)
            logger.debug("Failed to get diff files between refs, returning empty list")
            return []
        files = [
            line.strip() for line in result.stdout.strip().split("\n") if line.strip()
        ]
        logger.debug("Found %d diff files between refs", len(files))
        logger.trace("Diff files: %s", files)
        return files

    def get_all_modified_files(self) -> List[str]:
        logger.debug("Getting all modified files (staged, unstaged, and untracked)")
        logger.trace("Running 'git status --porcelain -uall'")
        result = self.command_executor.run(
            ["git", "status", "--porcelain", "-uall"],
            check=True,
        )
        if not result.success:
            logger.trace("Command failed: exit_code=%d", result.exit_code)
            logger.debug("Failed to get all modified files, returning empty list")
            return []
        files = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                file_path = line.strip().split(None, 1)[-1]
                if file_path:
                    files.append(file_path)
        logger.debug("Found %d modified files", len(files))
        logger.trace("Modified files: %s", files)
        return files


__all__ = ["GitGateway"]
