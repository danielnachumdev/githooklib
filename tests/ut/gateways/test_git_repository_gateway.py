import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import List
from unittest.mock import patch

from githooklib.constants import EXIT_FAILURE
from githooklib.definitions import CommandResult
from githooklib.gateways import GitGateway
from tests.base_test_case import BaseTestCase


class TestGitRepositoryGateway(BaseTestCase):
    def setUp(self):
        self.gateway = GitGateway()

    def test_find_git_root_via_command_subprocess_fails_returns_none(self):
        from githooklib.definitions import CommandResult
        from githooklib.constants import EXIT_FAILURE

        with self.subTest("file_not_found_error"):
            failed_result = CommandResult(
                success=False,
                exit_code=EXIT_FAILURE,
                stdout="",
                stderr="",
                command=["git", "rev-parse", "--show-toplevel"],
            )
            with patch.object(
                self.gateway.command_executor, "run", return_value=failed_result
            ):
                result = self.gateway._find_git_root_via_command()
                self.assertIsNone(result)

        with self.subTest("command_fails"):
            failed_result = CommandResult(
                success=False,
                exit_code=EXIT_FAILURE,
                stdout="",
                stderr="",
                command=["git", "rev-parse", "--show-toplevel"],
            )
            with patch.object(
                self.gateway.command_executor, "run", return_value=failed_result
            ):
                result = self.gateway._find_git_root_via_command()
                self.assertIsNone(result)

    def test_find_git_root_via_command_ends_with_githooklib(self):
        result = self.gateway._find_git_root_via_command()
        result = self.unwrap_optional(result)
        self.assertEqual("githooklib/.git", "/".join(result.parts[-2:]))
        self.assertTrue(result.exists())

    def test_find_git_root_via_command_no_git_directory_returns_none(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                result = self.gateway._find_git_root_via_command()
                self.assertIsNone(result)
            finally:
                os.chdir(original_cwd)

    def test_find_git_root_via_filesystem_ends_with_githooklib(self):
        result = self.gateway._find_git_root_via_filesystem()
        result = self.unwrap_optional(result)
        self.assertEqual(result.name, "githooklib")
        self.assertTrue((result / ".git").exists())

    def test_find_git_root_via_filesystem_found_in_parent(self):
        git_root = self.gateway.get_git_root_path()
        git_root = self.unwrap_optional(git_root)
        original_cwd = os.getcwd()
        try:
            subdir = git_root / "tests" / "ut" / "gateways"
            subdir.mkdir(parents=True, exist_ok=True)
            os.chdir(subdir)
            result = self.gateway._find_git_root_via_filesystem()
            self.assertIsNotNone(result)
        finally:
            os.chdir(original_cwd)

    def test_find_git_root_ends_with_githooklib(self):
        result = self.gateway.get_git_root_path()
        result = self.unwrap_optional(result)
        self.assertEqual("githooklib/.git", "/".join(result.parts[-2:]))
        self.assertTrue(result.exists())

    def test_find_git_root_no_repo_returns_none(self):
        self.gateway.get_git_root_path.cache_clear()
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                with patch.object(
                    self.gateway, "_find_git_root_via_command", return_value=None
                ):
                    with patch.object(
                        self.gateway, "_find_git_root_via_filesystem", return_value=None
                    ):
                        result = self.gateway.get_git_root_path()
                        self.assertIsNone(result)
            finally:
                os.chdir(original_cwd)
                self.gateway.get_git_root_path.cache_clear()

    def test_is_hook_from_githooklib_true_for_correct(self):
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".sh"
        ) as temp_file:
            temp_path = Path(temp_file.name)
            delegation_script = """#!/usr/bin/env python3

import subprocess
import sys


def main() -> None:
    result = subprocess.run(
        ["python", "-m", "githooklib", "run", "pre-commit"],
        cwd="/path/to/project",
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
"""
            temp_file.write(delegation_script)
        try:
            result = GitGateway._is_hook_from_githooklib(temp_path)
            self.assertTrue(result)
        finally:
            temp_path.unlink()

    def test_is_hook_from_githooklib_false_for_incorrect(self):
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".sh"
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write("#!/bin/bash\necho 'test'")
        try:
            result = GitGateway._is_hook_from_githooklib(temp_path)
            self.assertFalse(result)
        finally:
            temp_path.unlink()

    def test_is_hook_from_githooklib_false_on_file_read_error(self):
        non_existent_path = Path("/non/existent/path/hook")
        result = GitGateway._is_hook_from_githooklib(non_existent_path)
        self.assertFalse(result)

    def test_get_installed_hooks_returns_none_when_none_installed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            hooks_dir = Path(temp_dir)
            result = self.gateway.get_installed_hooks(hooks_dir)
            self.assertEqual(result, {})

    def test_get_installed_hooks_ignores_sample_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            hooks_dir = Path(temp_dir)
            sample_hook = hooks_dir / "pre-commit.sample"
            sample_hook.write_text("sample content")
            try:
                result = self.gateway.get_installed_hooks(hooks_dir)
                self.assertNotIn("pre-commit.sample", result)
                self.assertEqual(result, {})
            finally:
                if sample_hook.exists():
                    sample_hook.unlink()

    def test_get_installed_hooks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            hooks_dir = Path(temp_dir)
            githooklib_hook = hooks_dir / "pre-commit"
            delegation_script = """#!/usr/bin/env python3

import subprocess
import sys


def main() -> None:
    result = subprocess.run(
        ["python", "-m", "githooklib", "run", "pre-commit"],
        cwd="/path/to/project",
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
"""
            githooklib_hook.write_text(delegation_script)
            regular_hook = hooks_dir / "pre-push"
            regular_hook.write_text("#!/bin/bash\necho 'test'")
            sample_hook = hooks_dir / "pre-commit.sample"
            sample_hook.write_text("sample content")
            try:
                result = self.gateway.get_installed_hooks(hooks_dir)
                self.assertIn("pre-commit", result)
                self.assertTrue(result["pre-commit"])
                self.assertIn("pre-push", result)
                self.assertFalse(result["pre-push"])
                self.assertNotIn("pre-commit.sample", result)
            finally:
                for hook_file in [githooklib_hook, regular_hook, sample_hook]:
                    if hook_file.exists():
                        hook_file.unlink()

    def test_get_cached_index_files_returns_staged_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            original_cwd = os.getcwd()
            try:
                os.chdir(repo)
                self._initialize_repo(repo)
                test_file = repo / "test.py"
                test_file.write_text("print('test')")
                self._git(repo, ["add", "test.py"])
                files = self.gateway.get_cached_index_files()
                self.assertIn("test.py", files)
            finally:
                os.chdir(original_cwd)

    def test_get_cached_index_files_no_staged_files_returns_empty(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            original_cwd = os.getcwd()
            try:
                os.chdir(repo)
                self._initialize_repo(repo)
                files = self.gateway.get_cached_index_files()
                self.assertEqual(files, [])
            finally:
                os.chdir(original_cwd)

    def test_get_diff_files_between_refs_returns_changed_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            original_cwd = os.getcwd()
            try:
                os.chdir(repo)
                self._initialize_repo(repo)
                test_file = repo / "test.py"
                test_file.write_text("print('test')")
                self._git(repo, ["add", "test.py"])
                self._git(repo, ["commit", "-m", "initial"])
                test_file.write_text("print('updated')")
                self._git(repo, ["add", "test.py"])
                self._git(repo, ["commit", "-m", "update"])
                files = self.gateway.get_diff_files_between_refs("HEAD~1", "HEAD")
                self.assertIn("test.py", files)
            finally:
                os.chdir(original_cwd)

    def test_get_all_modified_files_returns_changed_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            original_cwd = os.getcwd()
            try:
                os.chdir(repo)
                self._initialize_repo(repo)
                test_file = repo / "test.py"
                test_file.write_text("print('test')")
                files = self.gateway.get_all_modified_files()
                self.assertIn("test.py", files)
            finally:
                os.chdir(original_cwd)

    def _initialize_repo(self, repo: Path) -> None:
        self._git(repo, ["init"])
        self._git(repo, ["config", "user.email", "test@example.com"])
        self._git(repo, ["config", "user.name", "Tester"])

    def _git(self, repo: Path, args: List[str]) -> None:
        result = subprocess.run(
            ["git"] + args, cwd=repo, capture_output=True, text=True, check=True
        )


if __name__ == "__main__":
    unittest.main()
