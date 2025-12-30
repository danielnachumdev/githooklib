import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import List

from githooklib import GitHookContext
from githooklib.command import CommandExecutor, CommandResult
from githooklib.examples.pre_commit_black import BlackFormatterPreCommit, StagePolicy
from ...base_test_case import BaseTestCase
from ...utils import PathUtils


class TestPreCommitBlack(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.executor = CommandExecutor()

    def test_stage_policy_previously_staged_keeps_unstaged_out(self) -> None:
        if not self._black_available():
            self.skipTest("Black is not available")

        with self._repo_with_unformatted_files() as (
            repo,
            staged_file,
            unstaged_file,
        ):
            hook = BlackFormatterPreCommit(stage_policy=StagePolicy.CHANGED_FILES_ONLY)
            with self._in_repo(repo):
                result = hook.execute(GitHookContext("pre-commit", []))

            self.assertTrue(result.success)
            staged_after_hook = self._staged_files(repo)
            self._assert_staged_files(staged_after_hook, [staged_file.name])
            self.assertNotIn(unstaged_file.name, staged_after_hook)

    def test_stage_policy_all_tracked_stages_every_tracked_file(self) -> None:
        if not self._black_available():
            self.skipTest("Black is not available")

        with self._repo_with_unformatted_files() as (
            repo,
            staged_file,
            unstaged_file,
        ):
            hook = BlackFormatterPreCommit(stage_policy=StagePolicy.ALL)
            with self._in_repo(repo):
                result = hook.execute(GitHookContext("pre-commit", []))

            self.assertTrue(result.success)
            staged_after_hook = self._staged_files(repo)
            self._assert_staged_files(
                staged_after_hook, [staged_file.name, unstaged_file.name]
            )

    def _initialize_repo(self, repo: Path) -> None:
        self._git(repo, ["init"])
        self._git(repo, ["config", "user.email", "test@example.com"])
        self._git(repo, ["config", "user.name", "Tester"])

    def _create_initial_commit(
        self, repo: Path, staged_file: Path, unstaged_file: Path
    ) -> None:
        staged_file.write_text("def original():\n    return 1\n")
        unstaged_file.write_text("def another():\n    return 2\n")
        self._git(repo, ["add", "."])
        self._git(repo, ["commit", "-m", "init"])

    def _rewrite_unformatted_files(
        self, staged_file: Path, unstaged_file: Path
    ) -> None:
        staged_file.write_text("first=1\n")
        unstaged_file.write_text("second=2\n")

    def _staged_files(self, repo: Path) -> List[str]:
        diff_result = self._git(repo, ["diff", "--name-only", "--cached"])
        return [line for line in diff_result.stdout.splitlines() if line]

    def _black_available(self) -> bool:
        result = self.executor.python_module("black", ["--version"])
        return result.success and result.exit_code == 0

    def _git(self, repo: Path, args: List[str]) -> CommandResult:
        result = self.executor.run(["git"] + args, cwd=repo)
        self.assertTrue(result.success, f"git {' '.join(args)} failed: {result.stderr}")
        return result

    @contextmanager
    def _repo_with_unformatted_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            staged_file = repo / "staged.py"
            unstaged_file = repo / "unstaged.py"

            self._initialize_repo(repo)
            self._create_initial_commit(repo, staged_file, unstaged_file)
            self._rewrite_unformatted_files(staged_file, unstaged_file)
            self._git(repo, ["add", staged_file.name])
            yield repo, staged_file, unstaged_file

    @contextmanager
    def _in_repo(self, repo: Path):
        original_cwd = PathUtils.get_cwd()
        try:
            PathUtils.set_cwd(repo)
            yield
        finally:
            PathUtils.set_cwd(original_cwd)

    def _assert_staged_files(self, staged_after_hook: List[str], expected: List[str]):
        self.assertCountEqual(expected, staged_after_hook)
