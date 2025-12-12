import unittest

from .base_test_case import OperationsBaseTestCase


class TestUninstallE2E(OperationsBaseTestCase):
    def test_successful_uninstallation(self):
        with self.new_temp_project() as root:
            self.githooklib(["install", "pre-commit"], cwd=root)
            self.verify_hook_installed(root, "pre-commit")

            self.githooklib(["uninstall", "pre-commit"], cwd=root)
            self.verify_hook_uninstalled(root, "pre-commit")

            show_output = self.show(cwd=root)
            hook_found = any("pre-commit" in hook for hook in show_output)
            self.assertFalse(
                hook_found,
                f"pre-commit should not appear in show output: {show_output}",
            )

    def test_hook_not_found(self):
        with self.new_temp_project() as root:
            result = self.githooklib(
                ["uninstall", "non-existent-hook"], cwd=root, success=False, exit_code=1
            )
            self.assertEqual(1, result.exit_code)
            self.assertIn("Error", result.stderr)

    def test_hook_not_installed(self):
        with self.new_temp_project() as root:
            result = self.githooklib(
                ["uninstall", "pre-commit"], cwd=root, success=False, exit_code=1
            )
            self.assertEqual(1, result.exit_code)

    def test_not_in_git_repository(self):
        with self.new_temp_project(git=False) as root:
            result = self.githooklib(
                ["uninstall", "pre-commit"],
                cwd=root,
                success=False,
                exit_code=1,
            )
            self.assertEqual(1, result.exit_code)

    def test_external_hook_handling(self):
        with self.new_temp_project() as root:
            self.create_external_hook(
                root, "prepare-commit-msg", "#!/bin/sh\necho 'External hook'\n"
            )
            self.verify_hook_installed(root, "prepare-commit-msg")

            result = self.githooklib(
                ["uninstall", "prepare-commit-msg"],
                cwd=root,
                success=False,
                exit_code=1,
            )
            self.assertEqual(1, result.exit_code)

            hook_path = self.get_installed_hooks_path(root) / "prepare-commit-msg"
            self.assertTrue(hook_path.exists(), "External hook should not be removed")

    def test_uninstall_verification(self):
        with self.new_temp_project() as root:
            self.githooklib(["install", "pre-commit"], cwd=root)
            self.githooklib(["install", "pre-push"], cwd=root)

            self.verify_hook_installed(root, "pre-commit")
            self.verify_hook_installed(root, "pre-push")

            self.githooklib(["uninstall", "pre-commit"], cwd=root)

            self.verify_hook_uninstalled(root, "pre-commit")
            self.verify_hook_installed(root, "pre-push")


if __name__ == "__main__":
    unittest.main()
