import unittest

from .base_test_case import OperationsBaseTestCase


class TestRunE2E(OperationsBaseTestCase):

    def test_install_sanity_check(self):
        with self.new_temp_project() as root:
            self.githooklib(["run", "pre-push"], cwd=root)

    def test_no_debug_or_trace(self):
        with self.new_temp_project() as root:
            stdout = self.githooklib(["run", "pre-commit"], cwd=root).stdout
            self.assertIn(self.get_default_print("pre-commit"), stdout)

    def test_hook_execution_success(self):
        with self.new_temp_project() as root:
            result = self.githooklib(["run", "pre-commit"], cwd=root)
            self.assertEqual(0, result.exit_code)
            self.assertIn(self.get_default_print("pre-commit"), result.stdout)

    def test_hook_execution_failure(self):
        failing_hook = self.create_failing_hook("pre-commit", "Test failure message")
        with self.new_temp_project(hook_setup={"pre-commit": failing_hook}) as root:
            result = self.githooklib(
                ["run", "pre-commit"], cwd=root, success=False, exit_code=1
            )
            self.assertEqual(1, result.exit_code)
            self.assertIn("Test failure message", result.stdout)

    def test_hook_not_found(self):
        with self.new_temp_project() as root:
            result = self.githooklib(
                ["run", "non-existent-hook"], cwd=root, success=False, exit_code=1
            )
            self.assertEqual(1, result.exit_code)
            self.assertIn("Error", result.stderr)

    def test_hook_with_exceptions(self):
        exception_hook = self.create_exception_hook("pre-commit", "Test exception")
        with self.new_temp_project(hook_setup={"pre-commit": exception_hook}) as root:
            result = self.githooklib(
                ["run", "pre-commit"], cwd=root, success=False, exit_code=1
            )
            self.assertEqual(1, result.exit_code)

    def test_multiple_hooks_execution(self):
        with self.new_temp_project() as root:
            result1 = self.githooklib(["run", "pre-commit"], cwd=root)
            self.assertEqual(0, result1.exit_code)
            self.assertIn(self.get_default_print("pre-commit"), result1.stdout)

            result2 = self.githooklib(["run", "pre-push"], cwd=root)
            self.assertEqual(0, result2.exit_code)
            self.assertIn(self.get_default_print("pre-push"), result2.stdout)

    def test_debug_flag(self):
        with self.new_temp_project() as root:
            result = self.githooklib(["run", "pre-commit", "--debug"], cwd=root)
            self.assertEqual(0, result.exit_code)
            self.assertIn(self.get_default_print("pre-commit"), result.stdout)

    def test_trace_flag(self):
        with self.new_temp_project() as root:
            result = self.githooklib(["run", "pre-commit", "--trace"], cwd=root)
            self.assertEqual(0, result.exit_code)
            self.assertIn(self.get_default_print("pre-commit"), result.stdout)


if __name__ == "__main__":
    unittest.main()
