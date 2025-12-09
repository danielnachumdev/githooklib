import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from githooklib.gateways.git_repository_gateway import GitRepositoryGateway
from tests.base_test_case import BaseTestCase


class TestGitRepositoryGateway(BaseTestCase):
    def setUp(self):
        self.gateway = GitRepositoryGateway()

    def test_find_git_root_via_command_subprocess_fails_returns_none(self):
        with self.subTest("file_not_found_error"):
            with patch("subprocess.run", side_effect=FileNotFoundError()):
                result = GitRepositoryGateway._find_git_root_via_command()
                self.assertIsNone(result)

        with self.subTest("called_process_error"):
            with patch(
                "subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")
            ):
                result = GitRepositoryGateway._find_git_root_via_command()
                self.assertIsNone(result)

    def test_find_git_root_via_command_ends_with_githooklib(self):
        result = GitRepositoryGateway._find_git_root_via_command()
        result = self.unwrap_optional(result)
        self.assertEqual("githooklib/.git", "/".join(result.parts[-2:]))
        self.assertTrue(result.exists())

    def test_find_git_root_via_command_no_git_directory_returns_none(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                result = GitRepositoryGateway._find_git_root_via_command()
                self.assertIsNone(result)
            finally:
                os.chdir(original_cwd)

    def test_find_git_root_via_filesystem_ends_with_githooklib(self):
        result = GitRepositoryGateway._find_git_root_via_filesystem()
        result = self.unwrap_optional(result)
        self.assertEqual(result.name, "githooklib")
        self.assertTrue((result / ".git").exists())

    def test_find_git_root_via_filesystem_found_in_parent(self):
        git_root = GitRepositoryGateway.find_git_root()
        git_root = self.unwrap_optional(git_root)
        original_cwd = os.getcwd()
        try:
            subdir = git_root / "tests" / "ut" / "gateways"
            subdir.mkdir(parents=True, exist_ok=True)
            os.chdir(subdir)
            result = GitRepositoryGateway._find_git_root_via_filesystem()
            self.assertIsNotNone(result)
        finally:
            os.chdir(original_cwd)

    def test_find_git_root_ends_with_githooklib(self):
        result = GitRepositoryGateway.find_git_root()
        result = self.unwrap_optional(result)
        self.assertEqual("githooklib/.git", "/".join(result.parts[-2:]))
        self.assertTrue(result.exists())

    def test_find_git_root_no_repo_returns_none(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                result = GitRepositoryGateway.find_git_root()
                self.assertIsNone(result)
            finally:
                os.chdir(original_cwd)

    def test_is_hook_from_githooklib_true_for_correct(self):
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".sh"
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write("githooklib find_project_root")
        try:
            result = GitRepositoryGateway._is_hook_from_githooklib(temp_path)
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
            result = GitRepositoryGateway._is_hook_from_githooklib(temp_path)
            self.assertFalse(result)
        finally:
            temp_path.unlink()

    def test_is_hook_from_githooklib_false_on_file_read_error(self):
        non_existent_path = Path("/non/existent/path/hook")
        result = GitRepositoryGateway._is_hook_from_githooklib(non_existent_path)
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
            githooklib_hook.write_text("githooklib find_project_root")
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


if __name__ == "__main__":
    unittest.main()
