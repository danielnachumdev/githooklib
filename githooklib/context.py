import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from .gateways import ProjectRootGateway, GitGateway
from .logger import get_logger

logger = get_logger()


@dataclass
class GitHookContext:
    hook_name: str
    argv: List[str]
    project_root: Path = field(default_factory=ProjectRootGateway.find_project_root)
    remote_ref: Optional[str] = None
    local_ref: Optional[str] = None

    def get_changed_files(self) -> List[str]:
        git_gateway = GitGateway()
        if self.remote_ref and self.local_ref:
            logger.trace(
                "Getting diff files between refs: remote_ref=%s, local_ref=%s",
                self.remote_ref,
                self.local_ref,
            )
            files = git_gateway.get_diff_files_between_refs(
                self.remote_ref, self.local_ref
            )
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

    @classmethod
    def from_argv(cls, hook_name: str) -> "GitHookContext":
        logger.debug("Creating GitHookContext from argv for hook '%s'", hook_name)
        logger.trace("sys.argv: %s", sys.argv)
        remote_ref = None
        local_ref = None

        if hook_name == "pre-push":
            logger.trace("Parsing pre-push hook stdin for ref information")
            remote_ref, local_ref = cls._parse_pre_push_stdin()
            logger.trace(
                "Pre-push refs parsed: remote_ref=%s, local_ref=%s",
                remote_ref,
                local_ref,
            )

        context = cls(
            hook_name=hook_name,
            argv=sys.argv,
            remote_ref=remote_ref,
            local_ref=local_ref,
        )
        logger.trace(
            "GitHookContext created: hook_name=%s, project_root=%s, remote_ref=%s, local_ref=%s",
            context.hook_name,
            context.project_root,
            context.remote_ref,
            context.local_ref,
        )
        return context

    @staticmethod
    def _parse_pre_push_stdin() -> Tuple[Optional[str], Optional[str]]:
        logger.trace("Reading stdin for pre-push hook")
        try:
            stdin_content = sys.stdin.read().strip()
            logger.trace("Stdin content: %s", stdin_content)
            if not stdin_content:
                logger.trace("Stdin is empty, returning None for both refs")
                return None, None

            lines = stdin_content.split("\n")
            if not lines:
                logger.trace("No lines in stdin, returning None for both refs")
                return None, None

            remote_ref = None
            local_ref = None

            for line in lines:
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
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.trace("Error parsing pre-push stdin: %s", e)
            return None, None


__all__ = ["GitHookContext"]
