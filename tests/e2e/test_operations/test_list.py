import unittest

from githooklib.ui_messages import UI_MESSAGE_NO_HOOKS_FOUND

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
            self.assertIn(UI_MESSAGE_NO_HOOKS_FOUND, result.stdout)

    def test_not_in_git_repository(self):
        with self.new_temp_project(git=False) as root:
            result = self.githooklib(["list"], cwd=root, success=False, exit_code=1)
            self.assertEqual(1, result.exit_code)

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
