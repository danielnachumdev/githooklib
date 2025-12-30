import os
import platform
import re
import subprocess
import unittest
from pathlib import Path
from typing import List
from unittest import skip

from githooklib.gateways import ProjectRootGateway
from tests.base_test_case import BaseTestCase


@skip("Only run manually if you have time")
class TestWslPytest(BaseTestCase):
    def setUp(self):
        if platform.system() != "Windows":
            self.skipTest("WSL tests only run on Windows")

        if os.environ.get("GITHOOKLIB_WSL_TEST_RUNNING"):
            self.skipTest("Already running in WSL test context to prevent recursion")

    def _convert_to_wsl_path(self, windows_path: Path) -> str:
        path_str = str(windows_path.resolve())
        if len(path_str) >= 2 and path_str[1] == ":":
            drive_letter = path_str[0].lower()
            path_without_drive = path_str[2:].replace("\\", "/")
            return f"/mnt/{drive_letter}{path_without_drive}"
        return path_str.replace("\\", "/")

    def _discover_tests(
        self, project_root: Path, wsl_project_path: str, wsl_venv_path: str
    ) -> List[str]:
        wsl_command = (
            f"cd {wsl_project_path} && "
            f"{wsl_venv_path}/bin/python -m pytest --collect-only -q"
        )

        env = os.environ.copy()
        env["GITHOOKLIB_WSL_TEST_RUNNING"] = "1"

        result = subprocess.run(
            ["wsl", "bash", "-c", wsl_command],
            capture_output=True,
            text=True,
            env=env,
            cwd=project_root,
        )

        if result.returncode != 0:
            self.logger.warning(
                "Failed to discover tests: %s\n%s", result.stdout, result.stderr
            )
            return []

        test_names = []
        test_path_pattern = re.compile(r"^tests/.*::.*::.*$")

        for line in result.stdout.splitlines():
            line = line.strip()
            if line and test_path_pattern.match(line):
                test_names.append(line)

        return test_names

    def _run_single_test_in_wsl(
        self,
        test_name: str,
        project_root: Path,
        wsl_project_path: str,
        wsl_venv_path: str,
    ) -> tuple[int, str, str]:
        wsl_command = (
            f"cd {wsl_project_path} && "
            f"{wsl_venv_path}/bin/python -m pytest {test_name}"
        )

        env = os.environ.copy()
        env["GITHOOKLIB_WSL_TEST_RUNNING"] = "1"

        result = subprocess.run(
            ["wsl", "bash", "-c", wsl_command],
            capture_output=True,
            text=True,
            env=env,
            cwd=project_root,
        )

        return result.returncode, result.stdout, result.stderr

    def test_run_all_tests_in_wsl(self):
        if platform.system() != "Windows":
            self.skipTest("WSL tests only run on Windows")

        if os.environ.get("GITHOOKLIB_WSL_TEST_RUNNING"):
            self.skipTest("Already running in WSL test context to prevent recursion")

        project_root = ProjectRootGateway.find_project_root()
        wsl_project_path = self._convert_to_wsl_path(project_root)
        wsl_venv_path = self._convert_to_wsl_path(project_root / "wslvenv")

        if not (project_root / "wslvenv").exists():
            self.skipTest("wslvenv not found, skipping WSL test")

        test_names = self._discover_tests(project_root, wsl_project_path, wsl_venv_path)

        if not test_names:
            self.skipTest("No tests discovered in WSL")

        wsl_test_file = "tests/e2e/test_wsl_pytest.py"
        test_names = [test for test in test_names if wsl_test_file not in test]

        self.logger.debug("Discovered %d tests to run in WSL", len(test_names))

        for test_name in test_names:
            with self.subTest(test_name):
                exit_code, stdout, stderr = self._run_single_test_in_wsl(
                    test_name, project_root, wsl_project_path, wsl_venv_path
                )

                self.logger.debug("Test %s: exit_code=%d", test_name, exit_code)
                if exit_code != 0:
                    self.logger.debug("stdout: %s", stdout)
                    self.logger.debug("stderr: %s", stderr)

                self.assertEqual(
                    0,
                    exit_code,
                    f"Test {test_name} failed in WSL with exit code {exit_code}\n"
                    f"stdout: {stdout}\n"
                    f"stderr: {stderr}",
                )


if __name__ == "__main__":
    unittest.main()
