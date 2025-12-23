import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from .constants import HOOKS_WITH_STDIN
from .gateways import ProjectRootGateway, GitGateway
from .logger import get_logger

logger = get_logger()


@dataclass
class GitHookContext:
    hook_name: str
    argv: List[str]
    project_root: Path = field(default_factory=ProjectRootGateway.find_project_root)
    stdin_lines: List[str] = field(default_factory=list)

    def get_changed_files(self) -> List[str]:
        git_gateway = GitGateway()

        if self.hook_name == "pre-push" and self.stdin_lines:
            remote_ref, local_ref = self._parse_pre_push_refs_from_stdin()
            if remote_ref and local_ref:
                logger.trace(
                    "Getting diff files between refs: remote_ref=%s, local_ref=%s",
                    remote_ref,
                    local_ref,
                )
                files = git_gateway.get_diff_files_between_refs(remote_ref, local_ref)
                logger.trace("Found %d diff files between refs", len(files))
                return files

        logger.trace("Getting cached index files")
        files = git_gateway.get_cached_index_files()
        if files:
            logger.trace("Found %d cached index files", len(files))
            return files

        logger.trace("No cached index files, getting all modified files")
        files = git_gateway.get_all_modified_files()
        logger.trace("Found %d modified files", len(files))
        return files

    def _parse_pre_push_refs_from_stdin(self) -> Tuple[Optional[str], Optional[str]]:
        logger.trace("Parsing pre-push refs from stdin_lines")
        if not self.stdin_lines:
            logger.trace("No stdin lines to parse, returning None for both refs")
            return None, None

        remote_ref = None
        local_ref = None

        for line in self.stdin_lines:
            if line.strip():
                parts = line.strip().split()
                if len(parts) >= 4:
                    local_ref_part = parts[0]
                    remote_ref_part = parts[2]
                    logger.trace(
                        "Parsed refs from line: local=%s, remote=%s",
                        local_ref_part,
                        remote_ref_part,
                    )
                    if not local_ref:
                        local_ref = local_ref_part
                    if not remote_ref:
                        remote_ref = remote_ref_part
                    break

        logger.trace(
            "Final parsed refs: remote_ref=%s, local_ref=%s", remote_ref, local_ref
        )
        return remote_ref, local_ref

    @classmethod
    def from_argv(cls, hook_name: str) -> "GitHookContext":
        logger.debug("Creating GitHookContext from argv for hook '%s'", hook_name)
        logger.trace("sys.argv: %s", sys.argv)
        stdin_lines: List[str] = []

        is_manual_run = "run" in sys.argv
        if hook_name in HOOKS_WITH_STDIN and not is_manual_run:
            logger.trace("Reading stdin for hook '%s'", hook_name)
            stdin_lines = cls._read_stdin_lines()
            logger.trace("Read %d lines from stdin", len(stdin_lines))

        context = cls(
            hook_name=hook_name,
            argv=sys.argv,
            stdin_lines=stdin_lines,
        )
        logger.trace(
            "GitHookContext created: hook_name=%s, project_root=%s, stdin_lines_count=%d",
            context.hook_name,
            context.project_root,
            len(context.stdin_lines),
        )
        return context

    @staticmethod
    def _read_stdin_lines() -> List[str]:
        logger.trace("Reading stdin lines")
        try:
            stdin_content = sys.stdin.read().strip()
            logger.trace("Stdin content length: %d characters", len(stdin_content))
            if not stdin_content:
                logger.trace("Stdin is empty, returning empty list")
                return []

            lines = [line for line in stdin_content.split("\n") if line.strip()]
            logger.trace("Parsed %d non-empty lines from stdin", len(lines))
            return lines
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.trace("Error reading stdin: %s", e)
            return []


__all__ = ["GitHookContext"]
