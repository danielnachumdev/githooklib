import os
import platform
import subprocess
import unittest
from pathlib import Path

from tests.base_test_case import BaseTestCase


class TestWslPytest(BaseTestCase):
    def setUp(self):
        if platform.system() != "Windows":
            self.skipTest("WSL tests only run on Windows")

    def _convert_to_wsl_path(self, windows_path: Path) -> str:
        path_str = str(windows_path.resolve())
        if len(path_str) >= 2 and path_str[1] == ":":
            drive_letter = path_str[0].lower()
            path_without_drive = path_str[2:].replace("\\", "/")
            return f"/mnt/{drive_letter}{path_without_drive}"
        return path_str.replace("\\", "/")

    def test_run_pytest_in_wsl(self):
        if platform.system() != "Windows":
            self.skipTest("WSL tests only run on Windows")

        if os.environ.get("GITHOOKLIB_WSL_TEST_RUNNING"):
            self.skipTest("Already running in WSL test context to prevent recursion")

        project_root = Path(__file__).parent.parent.parent
        wsl_project_path = self._convert_to_wsl_path(project_root)
        wsl_venv_path = self._convert_to_wsl_path(project_root / "wslvenv")

        if not (project_root / "wslvenv").exists():
            self.skipTest("wslvenv not found, skipping WSL test")

        wsl_command = (
            f"cd {wsl_project_path} && " f"{wsl_venv_path}/bin/python -m pytest -n auto"
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

        self.logger.debug("WSL pytest stdout: %s", result.stdout)
        self.logger.debug("WSL pytest stderr: %s", result.stderr)
        self.logger.debug("WSL pytest exit code: %d", result.returncode)

        self.assertEqual(
            0,
            result.returncode,
            f"WSL pytest failed with exit code {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
