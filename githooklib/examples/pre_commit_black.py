from githooklib import GitHook, GitHookContext, HookResult


class PreCommit(GitHook):
    @property
    def hook_name(self) -> str:
        return "pre-commit"

    def execute(self, context: GitHookContext) -> HookResult:
        self.logger.info("Reformatting code with black...")
        result = self.command_executor.run(["python", "-m", "black", "."])

        if not result.success:
            self.logger.error("Black formatting failed.")
            if result.stderr:
                self.logger.error(result.stderr)
            return HookResult(
                success=False,
                message="Black formatting failed.",
                exit_code=1,
            )

        self.logger.success("Code reformatted successfully!")
        return HookResult(success=True, message="Pre-commit checks passed!")

