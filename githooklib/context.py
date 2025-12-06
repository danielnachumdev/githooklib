import sys
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class GitHookContext:
    hook_name: str
    stdin_lines: List[str]
    project_root: Optional[Path] = None

    def __post_init__(self) -> None:
        if self.project_root is None:
            self.project_root = self._find_project_root()

    @classmethod
    def from_stdin(cls, hook_name: str) -> "GitHookContext":
        stdin_lines = cls._read_stdin_lines()
        return cls(hook_name=hook_name, stdin_lines=stdin_lines)

    @classmethod
    def empty(cls, hook_name: str) -> "GitHookContext":
        return cls(hook_name=hook_name, stdin_lines=[])

    @staticmethod
    def _read_stdin_lines() -> List[str]:
        if sys.stdin.isatty():
            return []
        return sys.stdin.read().strip().split("\n")

    def _find_project_root(self) -> Optional[Path]:
        git_root = self._find_git_root_via_command()
        if git_root:
            return git_root
        return self._find_git_root_via_filesystem()

    def _find_git_root_via_command(self) -> Optional[Path]:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                check=True,
            )
            git_dir = Path(result.stdout.strip())
            return git_dir.parent.resolve()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def _find_git_root_via_filesystem(self) -> Optional[Path]:
        current = Path.cwd()
        for path in [current] + list(current.parents):
            if (path / ".git").exists():
                return path.resolve()
        return None

    def get_stdin_line(
        self, index: int, default: Optional[str] = None
    ) -> Optional[str]:
        if 0 <= index < len(self.stdin_lines):
            return self.stdin_lines[index]
        return default

    def has_stdin(self) -> bool:
        return len(self.stdin_lines) > 0


__all__ = ["GitHookContext"]
