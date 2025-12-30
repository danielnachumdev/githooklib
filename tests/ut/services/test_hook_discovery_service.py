import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from githooklib import GitHook, GitHookContext, HookResult
from githooklib.services.hook_discovery_service import HookDiscoveryService
from githooklib.gateways.project_root_gateway import ProjectRootGateway
from tests.base_test_case import BaseTestCase


class MockHook1(GitHook):
    @classmethod
    def get_hook_name(cls) -> str:
        return "test-hook-1"

    @classmethod
    def get_file_patterns(cls):
        return None

    def execute(self, context: GitHookContext) -> HookResult:
        return HookResult(success=True)


class MockHook2(GitHook):
    @classmethod
    def get_hook_name(cls) -> str:
        return "test-hook-2"

    @classmethod
    def get_file_patterns(cls):
        return None

    def execute(self, context: GitHookContext) -> HookResult:
        return HookResult(success=True)


class TestHookDiscoveryService(BaseTestCase):
    def setUp(self):
        self.service = HookDiscoveryService()
        self.original_registered_hooks = GitHook._registered_hooks.copy()

    def tearDown(self):
        GitHook._registered_hooks[:] = self.original_registered_hooks
        if hasattr(self.service, "_hooks"):
            self.service._hooks = None

    def test_discover_hooks_returns_cached_hooks(self):
        self.service._hooks = {"test-hook": MockHook1}
        result = self.service.discover_hooks()
        self.assertEqual(result, {"test-hook": MockHook1})

    def test_discover_hooks_no_project_root_returns_empty(self):
        with patch.object(ProjectRootGateway, "find_project_root", return_value=None):
            service = HookDiscoveryService()
            service.project_root = None  # type: ignore[assignment]
            result = service.discover_hooks()
            self.assertEqual(result, {})

    def test_discover_hooks_finds_registered_hooks(self):
        self.service._hooks = None
        with patch.object(
            self.service, "_validate_no_duplicate_hooks"
        ) as mock_validate:
            with patch.object(self.service, "_import_all_hook_modules") as mock_import:
                with patch.object(
                    HookDiscoveryService,
                    "_collect_hook_classes_by_name",
                    return_value={"test-hook-1": [MockHook1]},
                ):
                    result = self.service.discover_hooks()
                    self.assertIsInstance(result, dict)
                    self.assertGreater(len(result), 0)

    def test_hook_exists_returns_true_when_hook_exists(self):
        self.service._hooks = {"test-hook-1": MockHook1}
        result = self.service.hook_exists("test-hook-1")
        self.assertTrue(result)

    def test_hook_exists_returns_false_when_hook_not_exists(self):
        self.service._hooks = {"test-hook-1": MockHook1}
        result = self.service.hook_exists("non-existent-hook")
        self.assertFalse(result)

    def test_set_hook_search_paths_updates_paths_and_invalidates_cache(self):
        original_hooks = {"test": MockHook1}  # type: ignore[assignment]
        self.service._hooks = original_hooks  # type: ignore[assignment]
        self.service.set_hook_search_paths(["custom/path"])
        self.assertEqual(self.service.hook_search_paths, ["custom/path"])
        self.assertIsNone(self.service._hooks)

    def test_set_hook_search_paths_with_multiple_paths(self):
        self.service.set_hook_search_paths(["path1", "path2", "path3"])
        self.assertEqual(self.service.hook_search_paths, ["path1", "path2", "path3"])

    def test_find_hook_modules_finds_files_in_project_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            hook_file = project_root / "test_hook.py"
            hook_file.write_text("class TestHook(GitHook): pass")
            self.service.project_root = project_root
            modules = self.service._find_hook_modules()
            self.assertIn(hook_file, modules)

    def test_find_hook_modules_finds_files_in_search_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = Path(temp_dir)
            githooks_dir = cwd / "githooks"
            githooks_dir.mkdir()
            hook_file = githooks_dir / "test_hook.py"
            hook_file.write_text("class TestHook(GitHook): pass")
            with patch("pathlib.Path.cwd", return_value=cwd):
                self.service.hook_search_paths = ["githooks"]
                modules = self.service._find_hook_modules()
                self.assertIn(hook_file, modules)

    def test_find_hook_modules_ignores_init_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = Path(temp_dir)
            githooks_dir = cwd / "githooks"
            githooks_dir.mkdir()
            init_file = githooks_dir / "__init__.py"
            init_file.write_text("")
            hook_file = githooks_dir / "test_hook.py"
            hook_file.write_text("class TestHook(GitHook): pass")
            with patch("pathlib.Path.cwd", return_value=cwd):
                self.service.hook_search_paths = ["githooks"]
                modules = self.service._find_hook_modules()
                self.assertNotIn(init_file, modules)
                self.assertIn(hook_file, modules)

    def test_find_hook_modules_handles_absolute_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            abs_path = Path(temp_dir) / "custom_hooks"
            abs_path.mkdir()
            hook_file = abs_path / "test_hook.py"
            hook_file.write_text("class TestHook(GitHook): pass")
            self.service.hook_search_paths = [str(abs_path)]
            modules = self.service._find_hook_modules()
            self.assertIn(hook_file, modules)

    def test_find_hook_modules_handles_nonexistent_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = Path(temp_dir)
            nonexistent_dir = cwd / "nonexistent"
            with patch("pathlib.Path.cwd", return_value=cwd):
                self.service.hook_search_paths = ["nonexistent"]
                modules = self.service._find_hook_modules()
                self.assertEqual(len(modules), 0)

    def test_invalidate_cache_clears_hooks(self):
        self.service._hooks = {"test": MockHook1}
        self.service._invalidate_cache()
        self.assertIsNone(self.service._hooks)

    def test_collect_hook_classes_by_name_groups_hooks(self):
        result = HookDiscoveryService._collect_hook_classes_by_name()
        self.assertIsInstance(result, dict)
        for hook_name, classes in result.items():
            self.assertIsInstance(hook_name, str)
            self.assertIsInstance(classes, list)
            self.assertGreater(len(classes), 0)
            for hook_class in classes:
                self.assertTrue(issubclass(hook_class, GitHook))

    def test_collect_hook_classes_by_name_handles_instantiation_errors(self):
        class FailingHookClass(GitHook):
            @classmethod
            def get_hook_name(cls) -> str:
                return "failing-hook"

            @classmethod
            def get_file_patterns(cls):
                return None

            def execute(self, context: GitHookContext) -> HookResult:
                return HookResult(success=True)

            def __init__(self):
                raise Exception("Instantiation error")

        original_registered = GitHook._registered_hooks.copy()
        try:
            if FailingHookClass not in GitHook._registered_hooks:
                GitHook._registered_hooks.append(FailingHookClass)
            result = HookDiscoveryService._collect_hook_classes_by_name()
            self.assertIsInstance(result, dict)
            self.assertNotIn("failing-hook", result)
        finally:
            GitHook._registered_hooks[:] = original_registered

    def test_validate_no_duplicate_hooks_passes_with_no_duplicates(self):
        hook_classes_by_name = {  # type: ignore[assignment]
            "hook1": [MockHook1],
            "hook2": [MockHook2],
        }
        try:
            self.service._validate_no_duplicate_hooks(hook_classes_by_name)  # type: ignore[arg-type]
        except ValueError:
            self.fail("_validate_no_duplicate_hooks raised ValueError unexpectedly")

    def test_validate_no_duplicate_hooks_raises_error_with_duplicates(self):
        hook_classes_by_name = {"duplicate-hook": [MockHook1, MockHook2]}
        with self.assertRaises(ValueError) as context:
            self.service._validate_no_duplicate_hooks(hook_classes_by_name)
        self.assertIn("Duplicate hook implementations found", str(context.exception))
        self.assertIn("duplicate-hook", str(context.exception))

    def test_raise_duplicate_hook_error_includes_module_info(self):
        duplicates = {"test-hook": [MockHook1, MockHook2]}  # type: ignore[assignment]
        with patch.object(
            self.service.module_import_gateway,
            "find_module_file",
            return_value="test_module.py",
        ):
            with self.assertRaises(ValueError) as context:
                self.service._raise_duplicate_hook_error(
                    duplicates
                )  # type: ignore[arg-type]
            error_message = str(context.exception)
            self.assertIn("test-hook", error_message)
            self.assertIn("MockHook1", error_message)
            self.assertIn("MockHook2", error_message)

    def test_raise_duplicate_hook_error_handles_missing_module_file(self):
        duplicates = {"test-hook": [MockHook1]}  # type: ignore[assignment]
        with patch.object(
            self.service.module_import_gateway,
            "find_module_file",
            return_value=None,
        ):
            with self.assertRaises(ValueError) as context:
                self.service._raise_duplicate_hook_error(duplicates)  # type: ignore[arg-type]
            error_message = str(context.exception)
            self.assertIn("test-hook", error_message)
            self.assertIn("MockHook1", error_message)

    def test_import_all_hook_modules_calls_import_gateway(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            hook_file = project_root / "test_hook.py"
            hook_file.write_text("class TestHook(GitHook): pass")
            self.service.project_root = project_root
            with patch.object(
                self.service.module_import_gateway, "import_module"
            ) as mock_import:
                self.service._import_all_hook_modules()
                mock_import.assert_called()

    def test_discover_hooks_caches_result(self):
        self.service._hooks = None
        with patch.object(self.service, "_validate_no_duplicate_hooks"):
            with patch.object(self.service, "_import_all_hook_modules"):
                with patch.object(
                    HookDiscoveryService,
                    "_collect_hook_classes_by_name",
                    return_value={"test-hook-1": [MockHook1]},
                ):
                    result1 = self.service.discover_hooks()
                    result2 = self.service.discover_hooks()
                    self.assertEqual(result1, result2)
                    self.assertIsNotNone(self.service._hooks)


if __name__ == "__main__":
    unittest.main()
