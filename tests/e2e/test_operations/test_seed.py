import unittest

from githooklib.ui_messages import (
    UI_MESSAGE_AVAILABLE_EXAMPLE_HOOKS_HEADER,
    UI_MESSAGE_EXAMPLE_NOT_FOUND_SUFFIX,
    UI_MESSAGE_EXAMPLE_ALREADY_EXISTS_SUFFIX,
    UI_MESSAGE_ERROR_PREFIX,
)

from .base_test_case import OperationsBaseTestCase


class TestSeedE2E(OperationsBaseTestCase):
    def test_isntall_sanity_check(self):
        self.githooklib(["seed"])

    def test_list_examples_no_argument(self):
        with self.new_temp_project() as root:
            result = self.githooklib(["seed"], cwd=root)
            self.assertEqual(0, result.exit_code)
            self.assertIn(UI_MESSAGE_AVAILABLE_EXAMPLE_HOOKS_HEADER, result.stdout)
            self.assertIn("pre_commit_black", result.stdout)

    def test_seed_specific_example(self):
        with self.new_temp_project() as root:
            result = self.githooklib(["seed", "pre_commit_black"], cwd=root)
            self.assertEqual(0, result.exit_code)

            hook_file = self.get_githooks_folder(root) / "pre_commit_black.py"
            self.assertTrue(hook_file.exists(), "Example hook file should be created")
            content = hook_file.read_text()
            self.assertIn("BlackFormatterPreCommit", content)

    def test_example_not_found(self):
        with self.new_temp_project() as root:
            result = self.githooklib(
                ["seed", "non_existent_example"], cwd=root, success=False, exit_code=1
            )
            self.assertEqual(1, result.exit_code)
            self.assertIn(UI_MESSAGE_ERROR_PREFIX.strip(), result.stderr)
            self.assertIn(UI_MESSAGE_EXAMPLE_NOT_FOUND_SUFFIX.strip(), result.stderr)

    def test_example_already_exists(self):
        with self.new_temp_project() as root:
            self.githooklib(["seed", "pre_commit_black"], cwd=root)
            result = self.githooklib(
                ["seed", "pre_commit_black"], cwd=root, success=False, exit_code=1
            )
            self.assertEqual(1, result.exit_code)
            self.assertIn(UI_MESSAGE_ERROR_PREFIX.strip(), result.stderr)
            self.assertIn(
                UI_MESSAGE_EXAMPLE_ALREADY_EXISTS_SUFFIX.strip(), result.stderr
            )

    def test_not_in_git_repository(self):
        with self.new_temp_project() as root:
            non_git_dir = root.parent / "non_git_dir"
            non_git_dir.mkdir()
            try:
                result = self.githooklib(
                    ["seed", "pre_commit_black"],
                    cwd=non_git_dir,
                    success=False,
                    exit_code=1,
                )
                self.assertEqual(1, result.exit_code)
            finally:
                non_git_dir.rmdir()


if __name__ == "__main__":
    unittest.main()
