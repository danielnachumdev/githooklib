from githooklib import GitHook, GitHookContext, HookResult
from githooks.steps.format_with_black import format_project_with_black
from githooks.steps.run_mypy_type_check import run_mypy_type_check


class PrePush(GitHook):
    @property
    def hook_name(self) -> str:
        return "pre-push"

    def execute(self, context: GitHookContext) -> HookResult:
        format_result = format_project_with_black(
            self.logger, self.command_executor
        )
        if not format_result.success:
            return format_result

        mypy_result = run_mypy_type_check(self.logger, self.command_executor)
        if not mypy_result.success:
            return mypy_result

        return HookResult(success=True, message="All checks passed!")
