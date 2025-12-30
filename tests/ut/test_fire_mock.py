import io
import os
import re
import sys
from builtins import SystemExit as BuiltinSystemExit
from typing import Callable, List, Optional, Tuple
from unittest.mock import patch

from githooklib.__main__ import main
from githooklib.gateways.project_root_gateway import ProjectRootGateway

from tests.base_test_case import BaseTestCase

HELP_PATTERN = re.compile(
    r"NAME.*?SYNOPSIS.*?COMMANDS.*?(install|list|run|seed|show|uninstall)",
    re.DOTALL | re.IGNORECASE,
)

HELP_LONG_FLAG_PATTERN = re.compile(
    r"INFO:.*?NAME.*?SYNOPSIS",
    re.DOTALL | re.IGNORECASE,
)


class MockSystemExit(Exception):
    def __init__(self, code: int) -> None:
        super().__init__()
        self.code = code


class ModuleCommandRunner:
    def __init__(self) -> None:
        self._original_argv = sys.argv.copy()
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        self._original_exit = sys.exit
        self._exit_code = 0

    def run_module_command(self, args: List[str]) -> Tuple[int, str, str]:
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        self._exit_code = 0

        try:
            self._setup_environment(args, stdout_buffer, stderr_buffer)
            self._execute_main_with_exit_handling()
        finally:
            self._restore_environment()

        return self._exit_code, stdout_buffer.getvalue(), stderr_buffer.getvalue()

    def _setup_environment(
        self, args: List[str], stdout_buffer: io.StringIO, stderr_buffer: io.StringIO
    ) -> None:
        sys.argv = ["githooklib"] + args
        sys.stdout = stdout_buffer
        sys.stderr = stderr_buffer
        sys.exit = self._create_mock_exit()  # type: ignore[assignment]

    def _create_mock_exit(self) -> Callable[..., None]:
        def mock_exit(code: int = 0) -> None:
            self._exit_code = code if isinstance(code, int) else 0
            raise MockSystemExit(code)

        return mock_exit

    def _execute_main_with_exit_handling(self) -> None:
        try:
            try:
                main()
            except BuiltinSystemExit as e:
                self._exit_code = e.code if isinstance(e.code, int) else 0
                raise MockSystemExit(self._exit_code) from e
        except MockSystemExit:
            pass

    def _restore_environment(self) -> None:
        sys.argv = self._original_argv
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
        sys.exit = self._original_exit


class TestFireMock(BaseTestCase):
    _original_cwd: Optional[str] = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._original_cwd = os.getcwd()
        project_root = ProjectRootGateway.find_project_root()
        if project_root:
            os.chdir(project_root)

    @classmethod
    def tearDownClass(cls):
        if cls._original_cwd:
            os.chdir(cls._original_cwd)
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.runner = ModuleCommandRunner()

    def test_help_output(self):
        test_cases = [
            ("no_args", [], HELP_PATTERN, lambda a, b: a),
            ("short_flag", ["-h"], HELP_LONG_FLAG_PATTERN, lambda a, b: b),
            (
                "long_flag",
                ["--help"],
                HELP_LONG_FLAG_PATTERN,
                lambda a, b: b,
            ),
        ]
        for test_name, args, pattern, selector in test_cases:
            with self.subTest(test_name=test_name):
                exit_code, stdout, stderr = self.runner.run_module_command(args)
                output = selector(stdout, stderr)  # type: ignore[no-untyped-call]
                self.assertRegex(output, pattern)
                self.assertEqual(0, exit_code)

    def test_seed_does_not_print_return_value(self):
        with patch("githooklib.cli.CLI.seed", return_value=42):
            exit_code, stdout, stderr = self.runner.run_module_command(["seed"])
            self.assertNotIn("42", stdout)
            self.assertEqual(42, exit_code)

    def test_install_does_not_print_return_value(self):
        with patch("githooklib.cli.CLI.install", return_value=37):
            exit_code, stdout, stderr = self.runner.run_module_command(
                ["install", "pre-commit"]
            )
            self.assertNotIn("37", stdout)
            self.assertEqual(37, exit_code)

    def test_uninstall_does_not_print_return_value(self):
        with patch("githooklib.cli.CLI.uninstall", return_value=99):
            exit_code, stdout, stderr = self.runner.run_module_command(
                ["uninstall", "pre-commit"]
            )
            self.assertNotIn("99", stdout)
            self.assertEqual(99, exit_code)

    def test_run_does_not_print_return_value(self):
        with patch("githooklib.cli.CLI.run", return_value=123):
            exit_code, stdout, stderr = self.runner.run_module_command(
                ["run", "pre-commit"]
            )
            self.assertNotIn("123", stdout)
            self.assertEqual(123, exit_code)

    def test_list_returns_none_no_print_exit_zero(self):
        with patch("githooklib.cli.CLI.list", return_value=None):
            exit_code, stdout, stderr = self.runner.run_module_command(["list"])
            self.assertEqual(0, exit_code)
