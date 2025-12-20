import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from githooklib import GitHook, GitHookContext, HookResult
from githooklib.services.hook_management_service import (
    HookManagementService,
    InstalledHooksContext,
)
from githooklib.gateways.git_gateway import GitGateway
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


class TestHookManagementService(BaseTestCase):
    def setUp(self):
        self.service = HookManagementService()

    def test_list_hooks_returns_sorted_hook_names(self):
        with patch.object(
            self.service.hook_discovery_service,
            "discover_hooks",
            return_value={"hook-b": MockHook, "hook-a": MockHook, "hook-c": MockHook},
        ):
            result = self.service.list_hooks()
            self.assertEqual(result, ["hook-a", "hook-b", "hook-c"])

    def test_list_hooks_returns_empty_list_when_no_hooks(self):
        with patch.object(
            self.service.hook_discovery_service, "discover_hooks", return_value={}
        ):
            result = self.service.list_hooks()
            self.assertEqual(result, [])

    def test_install_hook_success_when_hook_exists(self):
        with patch.object(
            self.service.hook_discovery_service,
            "discover_hooks",
            return_value={"test-hook": MockHook},
        ):
            with patch.object(MockHook, "install", return_value=True) as mock_install:
                result = self.service.install_hook("test-hook")
                self.assertTrue(result)
                mock_install.assert_called_once()

    def test_install_hook_fails_when_hook_not_found(self):
        with patch.object(
            self.service.hook_discovery_service, "discover_hooks", return_value={}
        ):
            result = self.service.install_hook("non-existent-hook")
            self.assertFalse(result)

    def test_install_hook_fails_when_install_returns_false(self):
        with patch.object(
            self.service.hook_discovery_service,
            "discover_hooks",
            return_value={"test-hook": MockHook},
        ):
            with patch.object(MockHook, "install", return_value=False):
                result = self.service.install_hook("test-hook")
                self.assertFalse(result)

    def test_uninstall_hook_success_when_hook_exists(self):
        with patch.object(
            self.service.hook_discovery_service,
            "discover_hooks",
            return_value={"test-hook": MockHook},
        ):
            with patch.object(
                MockHook, "uninstall", return_value=True
            ) as mock_uninstall:
                result = self.service.uninstall_hook("test-hook")
                self.assertTrue(result)
                mock_uninstall.assert_called_once()

    def test_uninstall_hook_fails_when_hook_not_found(self):
        with patch.object(
            self.service.hook_discovery_service, "discover_hooks", return_value={}
        ):
            result = self.service.uninstall_hook("non-existent-hook")
            self.assertFalse(result)

    def test_uninstall_hook_fails_when_uninstall_returns_false(self):
        with patch.object(
            self.service.hook_discovery_service,
            "discover_hooks",
            return_value={"test-hook": MockHook},
        ):
            with patch.object(MockHook, "uninstall", return_value=False):
                result = self.service.uninstall_hook("test-hook")
                self.assertFalse(result)

    def test_run_hook_returns_exit_code_when_hook_exists(self):
        with patch.object(
            self.service.hook_discovery_service,
            "discover_hooks",
            return_value={"test-hook": MockHook},
        ):
            with patch.object(MockHook, "run", return_value=0) as mock_run:
                result = self.service.run_hook("test-hook")
                self.assertEqual(result, 0)
                mock_run.assert_called_once()

    def test_run_hook_returns_failure_when_hook_not_found(self):
        from githooklib.constants import EXIT_FAILURE

        with patch.object(
            self.service.hook_discovery_service, "discover_hooks", return_value={}
        ):
            result = self.service.run_hook("non-existent-hook")
            self.assertEqual(result, EXIT_FAILURE)

    def test_run_hook_returns_non_zero_exit_code(self):
        with patch.object(
            self.service.hook_discovery_service,
            "discover_hooks",
            return_value={"test-hook": MockHook},
        ):
            with patch.object(MockHook, "run", return_value=1):
                result = self.service.run_hook("test-hook")
                self.assertEqual(result, 1)

    def test_get_installed_hooks_with_context_no_git_root(self):
        with patch.object(
            self.service.git_gateway, "get_git_root_path", return_value=None
        ):
            result = self.service.get_installed_hooks_with_context()
            self.assertIsInstance(result, InstalledHooksContext)
            self.assertEqual(result.installed_hooks, {})
            self.assertIsNone(result.git_root)
            self.assertFalse(result.hooks_dir_exists)

    def test_get_installed_hooks_with_context_no_hooks_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            git_root = Path(temp_dir)
            with patch.object(
                self.service.git_gateway, "get_git_root_path", return_value=git_root
            ):
                result = self.service.get_installed_hooks_with_context()
                self.assertIsInstance(result, InstalledHooksContext)
                self.assertEqual(result.installed_hooks, {})
                self.assertEqual(result.git_root, git_root)
                self.assertFalse(result.hooks_dir_exists)

    def test_get_installed_hooks_with_context_with_hooks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            git_root = Path(temp_dir)
            hooks_dir = git_root / "hooks"
            hooks_dir.mkdir(parents=True)
            hook_file = hooks_dir / "pre-commit"
            hook_file.write_text("#!/bin/bash\necho test")

            with patch.object(
                self.service.git_gateway, "get_git_root_path", return_value=git_root
            ):
                with patch.object(
                    self.service.git_gateway,
                    "get_installed_hooks",
                    return_value={"pre-commit": True},
                ):
                    result = self.service.get_installed_hooks_with_context()
                    self.assertIsInstance(result, InstalledHooksContext)
                    self.assertEqual(result.installed_hooks, {"pre-commit": True})
                    self.assertEqual(result.git_root, git_root)
                    self.assertTrue(result.hooks_dir_exists)

    def test_get_installed_hooks_with_context_calls_git_gateway(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            git_root = Path(temp_dir)
            hooks_dir = git_root / "hooks"
            hooks_dir.mkdir(parents=True)

            with patch.object(
                self.service.git_gateway, "get_git_root_path", return_value=git_root
            ) as mock_git_root:
                with patch.object(
                    self.service.git_gateway,
                    "get_installed_hooks",
                    return_value={},
                ) as mock_get_hooks:
                    self.service.get_installed_hooks_with_context()
                    mock_git_root.assert_called_once()
                    mock_get_hooks.assert_called_once_with(hooks_dir)


if __name__ == "__main__":
    unittest.main()
