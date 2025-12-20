import subprocess
import unittest
from unittest.mock import MagicMock

from githooklib.utils.command_result_factory import CommandResultFactory
from githooklib.constants import EXIT_FAILURE
from tests.base_test_case import BaseTestCase


class TestCommandResultFactory(BaseTestCase):
    def test_create_success_result_with_zero_exit_code(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        result = CommandResultFactory.create_success_result(mock_result, ["test"], True)
        self.assertTrue(result.success)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout, "output")
        self.assertEqual(result.command, ["test"])

    def test_create_success_result_with_non_zero_exit_code(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "error output"
        mock_result.stderr = "error"
        result = CommandResultFactory.create_success_result(mock_result, ["test"], True)
        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, 1)

    def test_create_success_result_without_capture_output(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        result = CommandResultFactory.create_success_result(
            mock_result, ["test"], False
        )
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_create_error_result(self):
        error = subprocess.CalledProcessError(1, "test", "output", "error")
        result = CommandResultFactory.create_error_result(error, ["test"], True)
        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.stdout, "output")
        self.assertEqual(result.stderr, "error")
        self.assertEqual(result.command, ["test"])

    def test_create_error_result_without_capture_output(self):
        error = subprocess.CalledProcessError(1, "test", "output", "error")
        result = CommandResultFactory.create_error_result(error, ["test"], False)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_create_not_found_result(self):
        result = CommandResultFactory.create_not_found_result(["nonexistent"])
        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, 127)
        self.assertIn("Command not found", result.stderr)
        self.assertEqual(result.command, ["nonexistent"])

    def test_create_generic_error_result(self):
        error = Exception("Generic error message")
        result = CommandResultFactory.create_generic_error_result(error, ["test"])
        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, EXIT_FAILURE)
        self.assertIn("Error executing command", result.stderr)
        self.assertIn("Generic error message", result.stderr)
        self.assertEqual(result.command, ["test"])


if __name__ == "__main__":
    unittest.main()
