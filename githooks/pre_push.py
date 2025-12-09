import sys

from githooklib import GitHook, GitHookContext, HookResult, get_logger
from githooks.steps import run_mypy_type_check

logger = get_logger(__name__, "pre-push")


class PrePush(GitHook):
    @classmethod
    def get_hook_name(cls) -> str:
        return "pre-push"

    def execute(self, context: GitHookContext) -> HookResult:
        mypy_result = run_mypy_type_check(logger, self.command_executor)
        if not mypy_result.success:
            return mypy_result

        return HookResult(success=True, message="All checks passed!")


__all__ = ["PrePush"]

if __name__ == "__main__":
    sys.exit(PrePush().run())
