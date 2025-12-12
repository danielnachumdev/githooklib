import unittest

from .base_test_case import OperationsBaseTestCase


class TestShowE2E(OperationsBaseTestCase):
    def test_isntall_sanity_check(self):
        self.githooklib(["show"])

    def test_shows_installed_hooks(self):
        with self.new_temp_project() as root:
            self.githooklib(["install", "pre-commit"], cwd=root)
            self.githooklib(["install", "pre-push"], cwd=root)

            show_output = self.show(cwd=root)
            hook_names = [
                hook.split()[0] if hook.split() else "" for hook in show_output
            ]
            self.assertIn("pre-commit", hook_names)
            self.assertIn("pre-push", hook_names)

    def test_distinguishes_githooklib_vs_external(self):
        with self.new_temp_project() as root:
            self.githooklib(["install", "pre-commit"], cwd=root)
            self.create_external_hook(root, "pre-push", "#!/bin/sh\necho 'External'\n")

            show_output = self.show(cwd=root)
            githooklib_found = any(
                "pre-commit" in hook and "githooklib" in hook for hook in show_output
            )
            external_found = any(
                "pre-push" in hook and "external" in hook for hook in show_output
            )

            self.assertTrue(
                githooklib_found,
                f"pre-commit should be marked as githooklib: {show_output}",
            )
            self.assertTrue(
                external_found, f"pre-push should be marked as external: {show_output}"
            )

    def test_no_hooks_installed(self):
        with self.new_temp_project() as root:
            result = self.githooklib(["show"], cwd=root, success=False, exit_code=0)
            self.assertIn("No hooks installed", result.stdout)

    def test_not_in_git_repository(self):
        with self.new_temp_project() as root:
            non_git_dir = root.parent / "non_git_dir"
            non_git_dir.mkdir()
            try:
                result = self.githooklib(
                    ["show"], cwd=non_git_dir, success=False, exit_code=0
                )
                self.assertIn("Not in a git repository", result.stdout)
            finally:
                non_git_dir.rmdir()

    def test_no_hooks_directory(self):
        with self.new_temp_project() as root:
            hooks_dir = self.get_installed_hooks_path(root)
            hooks_dir.rmdir()
            result = self.githooklib(["show"], cwd=root, success=False, exit_code=0)
            self.assertIn("No hooks directory found", result.stdout)


if __name__ == "__main__":
    unittest.main()
