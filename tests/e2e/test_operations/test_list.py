import unittest

from .base_test_case import OperationsBaseTestCase


class TestListE2E(OperationsBaseTestCase):
    def test_on_githooklib_folder(self):
        result = self.githooklib(["list"])
        self.assertIn("pre-push", result.stdout)
        self.assertIn("pre-commit", result.stdout)

    def test_lists_all_available_hooks(self):
        with self.new_temp_project() as root:
            hooks = self.list(cwd=root)
            self.assertIn("pre-commit", hooks)
            self.assertIn("pre-push", hooks)
            self.assertEqual(2, len(hooks))

    def test_no_hooks_found(self):
        with self.new_temp_project(hook_setup={}) as root:
            result = self.githooklib(["list"], cwd=root, success=True, exit_code=0)
            self.assertIn("No hooks found", result.stdout)

    def test_not_in_git_repository(self):
        with self.new_temp_project() as root:
            non_git_dir = root.parent / "non_git_dir"
            non_git_dir.mkdir()
            try:
                result = self.githooklib(
                    ["list"], cwd=non_git_dir, success=False, exit_code=1
                )
                self.assertEqual(1, result.exit_code)
            finally:
                non_git_dir.rmdir()

    def test_hook_discovery(self):
        custom_hook = self.create_basic_hook("commit-msg")
        with self.new_temp_project(
            hook_setup={
                "pre-commit": self.create_basic_hook("pre-commit"),
                "commit-msg": custom_hook,
            }
        ) as root:
            hooks = self.list(cwd=root)
            self.assertIn("pre-commit", hooks)
            self.assertIn("commit-msg", hooks)


if __name__ == "__main__":
    unittest.main()
