import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from githooklib import GitHook, GitHookContext, HookResult
from githooklib.gateways import GitGateway, ProjectRootGateway
from githooklib.constants import EXIT_SUCCESS, EXIT_FAILURE
from tests.base_test_case import BaseTestCase


class MockHook(GitHook):
    @classmethod
    def get_hook_name(cls) -> str:
        return "test-hook"

    @classmethod
    def get_file_patterns(cls):
        return None

    def execute(self, context: GitHookContext) -> HookResult:
        return HookResult(success=True)


class TestGitHookExtended(BaseTestCase):
    def setUp(self):
        self.hook = MockHook()

    def test_get_registered_hooks_returns_list(self):
        result = GitHook.get_registered_hooks()
        self.assertIsInstance(result, list)

    def test_get_module_and_class_returns_tuple(self):
        result = MockHook._get_module_and_class()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIn("MockHook", result[1])

    def test_get_log_level_returns_info(self):
        import logging

        result = MockHook.get_log_level()
        self.assertEqual(result, logging.INFO)

    def test_install_success_when_prerequisites_met(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            git_root = Path(temp_dir)
            hooks_dir = git_root / "hooks"
            hooks_dir.mkdir(parents=True)
            with patch.object(GitGateway, "get_git_root_path", return_value=git_root):
                with patch(
                    "githooklib.git_hook.ProjectRootGateway.find_project_root",
                    return_value=git_root,
                ):
                    with patch.object(
                        self.hook, "_write_hook_delegation_script", return_value=True
                    ):
                        result = self.hook.install()
                        self.assertTrue(result)

    def test_install_fails_when_not_git_repository(self):
        with patch.object(GitGateway, "get_git_root_path", return_value=None):
            result = self.hook.install()
            self.assertFalse(result)

    def test_install_fails_when_hooks_directory_not_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            git_root = Path(temp_dir)
            with patch.object(GitGateway, "get_git_root_path", return_value=git_root):
                result = self.hook.install()
                self.assertFalse(result)

    def test_install_fails_when_project_root_not_found(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            git_root = Path(temp_dir)
            hooks_dir = git_root / "hooks"
            hooks_dir.mkdir(parents=True)
            with patch.object(GitGateway, "get_git_root_path", return_value=git_root):
                with patch(
                    "githooklib.git_hook.ProjectRootGateway.find_project_root",
                    return_value=None,
                ):
                    result = self.hook.install()
                    self.assertFalse(result)

    def test_uninstall_success_when_hook_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            git_root = Path(temp_dir)
            hooks_dir = git_root / "hooks"
            hooks_dir.mkdir(parents=True)
            hook_file = hooks_dir / "test-hook"
            hook_file.write_text("test content")
            with patch.object(GitGateway, "get_git_root_path", return_value=git_root):
                result = self.hook.uninstall()
                self.assertTrue(result)
                self.assertFalse(hook_file.exists())

    def test_uninstall_fails_when_not_git_repository(self):
        with patch.object(GitGateway, "get_git_root_path", return_value=None):
            result = self.hook.uninstall()
            self.assertFalse(result)

    def test_uninstall_fails_when_hook_not_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            git_root = Path(temp_dir)
            hooks_dir = git_root / "hooks"
            hooks_dir.mkdir(parents=True)
            with patch.object(GitGateway, "get_git_root_path", return_value=git_root):
                result = self.hook.uninstall()
                self.assertFalse(result)

    def test_uninstall_handles_exception(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            git_root = Path(temp_dir)
            hooks_dir = git_root / "hooks"
            hooks_dir.mkdir(parents=True)
            hook_file = hooks_dir / "test-hook"
            hook_file.write_text("test content")
            with patch.object(GitGateway, "get_git_root_path", return_value=git_root):
                with patch("pathlib.Path.unlink", side_effect=Exception("Error")):
                    result = self.hook.uninstall()
                    self.assertFalse(result)

    def test_generate_delegator_script_includes_hook_name(self):
        with patch(
            "githooklib.git_hook.ProjectRootGateway.find_project_root",
            return_value=Path("/test"),
        ):
            script = self.hook._generate_delegator_script()
            self.assertIn("test-hook", script)

    def test_write_script_file_writes_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test_script"
            self.hook._write_script_file(temp_path, "test content")
            self.assertEqual(temp_path.read_text(), "test content")

    def test_make_script_executable_sets_permissions(self):
        import os
        import stat

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test_script"
            temp_path.write_text("test")
            self.hook._make_script_executable(temp_path)
            file_stat = temp_path.stat()
            if os.name != "nt":
                self.assertTrue(file_stat.st_mode & stat.S_IEXEC)
            else:
                self.assertTrue(temp_path.exists())

    def test_write_hook_delegation_script_success(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = Path(temp_dir) / "test-hook"
            result = self.hook._write_hook_delegation_script(
                script_path, "test script content"
            )
            self.assertTrue(result)
            self.assertTrue(script_path.exists())

    def test_write_hook_delegation_script_handles_exception(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = Path(temp_dir) / "test-hook"
            with patch.object(
                self.hook, "_write_script_file", side_effect=Exception("Error")
            ):
                result = self.hook._write_hook_delegation_script(
                    script_path, "test script content"
                )
                self.assertFalse(result)

    def test_run_handles_exception(self):
        with patch.object(GitHookContext, "from_argv", side_effect=Exception("Error")):
            with patch.object(self.hook, "_handle_error") as mock_handle:
                result = self.hook.run()
                self.assertEqual(result, EXIT_FAILURE)
                mock_handle.assert_called_once()

    def test_handle_error_logs_error(self):
        with patch.object(self.hook.logger, "error") as mock_error:
            error = Exception("Test error")
            self.hook._handle_error(error)
            self.assertTrue(mock_error.called)

    def test_validate_installation_prerequisites_returns_hooks_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            git_root = Path(temp_dir)
            hooks_dir = git_root / "hooks"
            hooks_dir.mkdir(parents=True)
            with patch.object(GitGateway, "get_git_root_path", return_value=git_root):
                result = self.hook._validate_installation_prerequisites()
                self.assertEqual(result, hooks_dir)

    def test_validate_installation_prerequisites_returns_none_when_no_git_root(self):
        with patch.object(GitGateway, "get_git_root_path", return_value=None):
            result = self.hook._validate_installation_prerequisites()
            self.assertIsNone(result)

    def test_validate_installation_prerequisites_returns_none_when_no_hooks_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            git_root = Path(temp_dir)
            with patch.object(GitGateway, "get_git_root_path", return_value=git_root):
                result = self.hook._validate_installation_prerequisites()
                self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
