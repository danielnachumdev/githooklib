from githooklib import GitHook, GitHookContext, HookResult
from githooks.steps.format_with_black import format_project_with_black


class PreCommit(GitHook):
    @property
    def hook_name(self) -> str:
        return "pre-commit"

    def execute(self, context: GitHookContext) -> HookResult:
        format_result = format_project_with_black(self.logger, self.command_executor)
        if not format_result.success:
            return format_result

        return HookResult(success=True, message="Pre-commit checks passed!")
