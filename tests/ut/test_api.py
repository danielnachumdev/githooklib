import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from githooklib.api import API
from githooklib import GitHook, GitHookContext, HookResult
from githooklib.services.hook_management_service import InstalledHooksContext
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


class TestAPI(BaseTestCase):
    def setUp(self):
        self.api = API()

    def test_discover_all_hooks_returns_hooks_dict(self):
        with patch.object(
            self.api.hook_discovery_service,
            "discover_hooks",
            return_value={"test-hook": MockHook},
        ):
            result = self.api.discover_all_hooks()
            self.assertIsInstance(result, dict)
            self.assertIn("test-hook", result)

    def test_discover_all_hooks_caches_result(self):
        with patch.object(
            self.api.hook_discovery_service,
            "discover_hooks",
            return_value={"test-hook": MockHook},
        ) as mock_discover:
            result1 = self.api.discover_all_hooks()
            result2 = self.api.discover_all_hooks()
            self.assertEqual(result1, result2)
            mock_discover.assert_called_once()

    def test_list_available_hook_names_returns_sorted_list(self):
        with patch.object(
            self.api.hook_management_service,
            "list_hooks",
            return_value=["hook-b", "hook-a", "hook-c"],
        ):
            result = self.api.list_available_hook_names()
            self.assertEqual(result, ["hook-b", "hook-a", "hook-c"])

    def test_list_available_hook_names_caches_result(self):
        with patch.object(
            self.api.hook_management_service,
            "list_hooks",
            return_value=["test-hook"],
        ) as mock_list:
            result1 = self.api.list_available_hook_names()
            result2 = self.api.list_available_hook_names()
            self.assertEqual(result1, result2)
            mock_list.assert_called_once()

    def test_check_hook_exists_returns_true_when_exists(self):
        with patch.object(
            self.api.hook_discovery_service, "hook_exists", return_value=True
        ):
            result = self.api.check_hook_exists("test-hook")
            self.assertTrue(result)

    def test_check_hook_exists_returns_false_when_not_exists(self):
        with patch.object(
            self.api.hook_discovery_service, "hook_exists", return_value=False
        ):
            result = self.api.check_hook_exists("non-existent-hook")
            self.assertFalse(result)

    def test_check_hook_exists_caches_result(self):
        with patch.object(
            self.api.hook_discovery_service, "hook_exists", return_value=True
        ) as mock_exists:
            result1 = self.api.check_hook_exists("test-hook")
            result2 = self.api.check_hook_exists("test-hook")
            self.assertTrue(result1)
            self.assertTrue(result2)
            mock_exists.assert_called_once()

    def test_install_hook_by_name_returns_true_on_success(self):
        with patch.object(
            self.api.hook_management_service, "install_hook", return_value=True
        ):
            result = self.api.install_hook_by_name("test-hook")
            self.assertTrue(result)

    def test_install_hook_by_name_returns_false_on_failure(self):
        with patch.object(
            self.api.hook_management_service, "install_hook", return_value=False
        ):
            result = self.api.install_hook_by_name("test-hook")
            self.assertFalse(result)

    def test_uninstall_hook_by_name_returns_true_on_success(self):
        with patch.object(
            self.api.hook_management_service, "uninstall_hook", return_value=True
        ):
            result = self.api.uninstall_hook_by_name("test-hook")
            self.assertTrue(result)

    def test_uninstall_hook_by_name_returns_false_on_failure(self):
        with patch.object(
            self.api.hook_management_service, "uninstall_hook", return_value=False
        ):
            result = self.api.uninstall_hook_by_name("test-hook")
            self.assertFalse(result)

    def test_run_hook_by_name_returns_exit_code(self):
        with patch.object(self.api.hook_management_service, "run_hook", return_value=0):
            result = self.api.run_hook_by_name("test-hook")
            self.assertEqual(result, 0)

    def test_run_hook_by_name_returns_non_zero_exit_code(self):
        with patch.object(self.api.hook_management_service, "run_hook", return_value=1):
            result = self.api.run_hook_by_name("test-hook")
            self.assertEqual(result, 1)

    def test_get_installed_hooks_with_context_returns_context(self):
        context = InstalledHooksContext({}, None, False)
        with patch.object(
            self.api.hook_management_service,
            "get_installed_hooks_with_context",
            return_value=context,
        ):
            result = self.api.get_installed_hooks_with_context()
            self.assertIsInstance(result, InstalledHooksContext)

    def test_find_git_repository_root_returns_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            git_root = Path(temp_dir)
            with patch.object(
                self.api.git_gateway, "get_git_root_path", return_value=git_root
            ):
                result = self.api.find_git_repository_root()
                self.assertEqual(result, git_root)

    def test_find_git_repository_root_returns_none_when_not_found(self):
        with patch.object(self.api.git_gateway, "get_git_root_path", return_value=None):
            result = self.api.find_git_repository_root()
            self.assertIsNone(result)

    def test_configure_hook_search_paths_sets_paths(self):
        with patch.object(
            self.api.hook_discovery_service, "set_hook_search_paths"
        ) as mock_set:
            self.api.configure_hook_search_paths("path1", "path2", "path3")
            mock_set.assert_called_once_with(["path1", "path2", "path3"])

    def test_get_hook_not_found_error_message_returns_message(self):
        with patch.object(
            self.api.error_message_service,
            "get_hook_not_found_error_message",
            return_value="Error: Hook not found",
        ):
            result = self.api.get_hook_not_found_error_message("test-hook")
            self.assertEqual(result, "Error: Hook not found")

    def test_list_available_example_names_returns_list(self):
        with patch.object(
            self.api.seed_gateway,
            "get_available_examples",
            return_value=["example1", "example2"],
        ):
            result = self.api.list_available_example_names()
            self.assertEqual(result, ["example1", "example2"])

    def test_check_example_exists_returns_true_when_exists(self):
        with patch.object(
            self.api.seed_gateway, "is_example_available", return_value=True
        ):
            result = self.api.check_example_exists("test-example")
            self.assertTrue(result)

    def test_check_example_exists_returns_false_when_not_exists(self):
        with patch.object(
            self.api.seed_gateway, "is_example_available", return_value=False
        ):
            result = self.api.check_example_exists("non-existent-example")
            self.assertFalse(result)

    def test_get_seed_failure_details_returns_details(self):
        from githooklib.definitions import SeedFailureDetails

        with patch.object(
            self.api.seed_service,
            "get_seed_failure_details",
            return_value=SeedFailureDetails(
                example_not_found=False,
                project_root_not_found=False,
                target_hook_already_exists=False,
                target_hook_path=None,
                available_examples=[],
            ),
        ):
            result = self.api.get_seed_failure_details("test-example")
            self.assertIsInstance(result, SeedFailureDetails)

    def test_seed_example_hook_to_project_returns_true_on_success(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            with patch(
                "githooklib.api.ProjectRootGateway.find_project_root",
                return_value=project_root,
            ):
                with patch.object(
                    self.api.seed_service, "seed_hook", return_value=True
                ):
                    result = self.api.seed_example_hook_to_project("test-example")
                    self.assertTrue(result)

    def test_seed_example_hook_to_project_returns_false_when_project_root_not_found(
        self,
    ):
        with patch(
            "githooklib.api.ProjectRootGateway.find_project_root",
            return_value=None,
        ):
            result = self.api.seed_example_hook_to_project("test-example")
            self.assertFalse(result)

    def test_seed_example_hook_to_project_returns_false_on_seed_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            with patch(
                "githooklib.api.ProjectRootGateway.find_project_root",
                return_value=project_root,
            ):
                with patch.object(
                    self.api.seed_service, "seed_hook", return_value=False
                ):
                    result = self.api.seed_example_hook_to_project("test-example")
                    self.assertFalse(result)

    def test_seed_example_hook_to_project_handles_exception(self):
        with patch(
            "githooklib.api.ProjectRootGateway.find_project_root",
            side_effect=Exception("Error finding project root"),
        ):
            result = self.api.seed_example_hook_to_project("test-example")
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
