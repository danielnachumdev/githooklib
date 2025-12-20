import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from githooklib.command import CommandExecutor
from githooklib.definitions import CommandResult
from tests.base_test_case import BaseTestCase


class TestCommandExecutor(BaseTestCase):
    def setUp(self):
        self.executor = CommandExecutor()

    def test_run_with_list_command(self):
        import sys

        result = self.executor.run([sys.executable, "-c", "print('test')"])
        self.assertIsInstance(result, CommandResult)
        self.assertTrue(result.success)

    def test_run_with_string_command(self):
        result = self.executor.run("echo test", shell=True)
        self.assertIsInstance(result, CommandResult)

    def test_run_with_cwd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.executor.run(["pwd"], cwd=temp_dir)
            self.assertIsInstance(result, CommandResult)

    def test_python_method(self):
        result = self.executor.python(["-c", "print('test')"])
        self.assertIsInstance(result, CommandResult)
        self.assertTrue(result.success)

    def test_python_module_method(self):
        result = self.executor.python_module("sys", ["--version"])
        self.assertIsInstance(result, CommandResult)

    def test_normalize_command_with_string(self):
        result = self.executor._normalize_command("test command", shell=False)
        self.assertEqual(result, ["test", "command"])

    def test_normalize_command_with_string_shell(self):
        result = self.executor._normalize_command("test command", shell=True)
        self.assertEqual(result, ["test command"])

    def test_normalize_command_with_list(self):
        result = self.executor._normalize_command(["test", "command"], shell=False)
        self.assertEqual(result, ["test", "command"])

    def test_normalize_cwd_with_none(self):
        result = self.executor._normalize_cwd(None)
        self.assertIsNone(result)

    def test_normalize_cwd_with_string(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.executor._normalize_cwd(temp_dir)
            self.assertIsInstance(result, Path)
            self.assertEqual(result, Path(temp_dir))

    def test_normalize_cwd_with_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir)
            result = self.executor._normalize_cwd(path)
            self.assertIsInstance(result, Path)
            self.assertEqual(result, path)

    def test_execute_command_handles_called_process_error(self):
        with patch.object(
            self.executor,
            "_run_subprocess",
            side_effect=subprocess.CalledProcessError(1, "cmd"),
        ):
            result = self.executor._execute_command(
                ["test"], None, True, False, True, False
            )
            self.assertIsInstance(result, CommandResult)
            self.assertFalse(result.success)

    def test_execute_command_handles_file_not_found_error(self):
        with patch.object(
            self.executor, "_run_subprocess", side_effect=FileNotFoundError()
        ):
            result = self.executor._execute_command(
                ["nonexistent"], None, True, False, True, False
            )
            self.assertIsInstance(result, CommandResult)
            self.assertFalse(result.success)
            self.assertEqual(result.exit_code, 127)

    def test_execute_command_handles_generic_error(self):
        with patch.object(
            self.executor, "_run_subprocess", side_effect=Exception("Generic error")
        ):
            result = self.executor._execute_command(
                ["test"], None, True, False, True, False
            )
            self.assertIsInstance(result, CommandResult)
            self.assertFalse(result.success)

    def test_run_subprocess_creates_success_result(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            result = self.executor._run_subprocess(
                ["test"], None, True, False, True, False
            )
            self.assertIsInstance(result, CommandResult)
            self.assertTrue(result.success)
            self.assertEqual(result.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
