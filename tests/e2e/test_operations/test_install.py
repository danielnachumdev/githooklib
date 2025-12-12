import unittest

from .base_test_case import OperationsBaseTestCase


class TestInstallE2E(OperationsBaseTestCase):
    def test_isntall_sanity_check(self):
        self.githooklib(["install", "pre-push"])

    def test_successful_installation(self):
        with self.new_temp_project() as root:
            self.githooklib(["install", "pre-commit"], cwd=root)
            self.verify_hook_installed(root, "pre-commit")
            hook_path = self.get_installed_hooks_path(root) / "pre-commit"
            content = hook_path.read_text()
            self.assertIn("githooklib", content)
            self.assertIn("run", content)

    def test_hook_not_found(self):
        with self.new_temp_project() as root:
            result = self.githooklib(
                ["install", "non-existent-hook"], cwd=root, success=False, exit_code=1
            )
            self.assertEqual(1, result.exit_code)
            self.assertIn("Error", result.stderr)

    def test_not_in_git_repository(self):
        with self.new_temp_project(git=False) as root:
            result = self.githooklib(
                ["install", "pre-commit"],
                cwd=root,
                success=False,
                exit_code=1,
            )
            self.assertEqual(1, result.exit_code)

    def test_hooks_directory_missing(self):
        with self.new_temp_project() as root:
            hooks_dir = self.get_installed_hooks_path(root)
            import shutil

            shutil.rmtree(hooks_dir)
            result = self.githooklib(
                ["install", "pre-commit"], cwd=root, success=False, exit_code=1
            )
            self.assertEqual(1, result.exit_code)

    def test_already_installed_hook(self):
        with self.new_temp_project() as root:
            self.githooklib(["install", "pre-commit"], cwd=root)
            self.verify_hook_installed(root, "pre-commit")
            first_content = (
                self.get_installed_hooks_path(root) / "pre-commit"
            ).read_text()

            self.githooklib(["install", "pre-commit"], cwd=root)
            self.verify_hook_installed(root, "pre-commit")
            second_content = (
                self.get_installed_hooks_path(root) / "pre-commit"
            ).read_text()
            self.assertEqual(first_content, second_content)

            result = self.githooklib(["run", "pre-commit"], cwd=root)
            self.assertEqual(0, result.exit_code)

    def test_installation_verification(self):
        with self.new_temp_project() as root:
            self.githooklib(["install", "pre-commit"], cwd=root)
            show_output = self.show(cwd=root)
            hook_found = any(
                "pre-commit" in hook and "githooklib" in hook for hook in show_output
            )
            self.assertTrue(
                hook_found, f"pre-commit should appear in show output: {show_output}"
            )


if __name__ == "__main__":
    unittest.main()
