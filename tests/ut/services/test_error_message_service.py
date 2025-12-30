import tempfile
import unittest
from pathlib import Path
from typing import List
from unittest.mock import patch, MagicMock

from githooklib.services.error_message_service import ErrorMessageService
from githooklib.gateways.project_root_gateway import ProjectRootGateway
from tests.base_test_case import BaseTestCase


class TestErrorMessageService(BaseTestCase):
    def setUp(self):
        self.service = ErrorMessageService()

    def test_get_hook_not_found_error_message_includes_hook_name(self):
        with patch.object(
            self.service.hook_discovery_service,
            "project_root",
            ProjectRootGateway.find_project_root(),
        ):
            result = self.service.get_hook_not_found_error_message("test-hook")
            self.assertIn("test-hook", result)

    def test_get_hook_not_found_error_message_includes_search_info(self):
        with patch.object(
            self.service.hook_discovery_service,
            "project_root",
            ProjectRootGateway.find_project_root(),
        ):
            result = self.service.get_hook_not_found_error_message("test-hook")
            self.assertIn("Could not find hooks", result)

    def test_resolve_search_path_returns_absolute_path_when_absolute(self):
        import os

        if os.name == "nt":
            absolute_path = Path("C:/absolute/path")
        else:
            absolute_path = Path("/absolute/path")
        cwd = Path.cwd()
        result = ErrorMessageService._resolve_search_path(str(absolute_path), cwd)
        self.assertEqual(result, absolute_path)

    def test_resolve_search_path_returns_relative_path_when_relative(self):
        cwd = Path("/current/working/dir")
        relative_path = "relative/path"
        result = ErrorMessageService._resolve_search_path(relative_path, cwd)
        self.assertEqual(result, cwd / relative_path)

    def test_add_search_dir_info_adds_info_for_existing_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            search_dir = Path(temp_dir)
            test_file = search_dir / "test.py"
            test_file.write_text("test")
            error_lines: List[str] = []
            ErrorMessageService._add_search_dir_info(error_lines, search_dir)
            self.assertEqual(len(error_lines), 1)
            self.assertIn(str(search_dir), error_lines[0])
            self.assertIn("1 .py files", error_lines[0])

    def test_add_search_dir_info_adds_info_for_empty_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            search_dir = Path(temp_dir)
            error_lines: List[str] = []
            ErrorMessageService._add_search_dir_info(error_lines, search_dir)
            self.assertEqual(len(error_lines), 1)
            self.assertIn(str(search_dir), error_lines[0])
            self.assertIn("no .py files found", error_lines[0])

    def test_add_search_dir_info_adds_info_for_nonexistent_directory(self):
        nonexistent_dir = Path("/nonexistent/directory")
        error_lines: List[str] = []
        ErrorMessageService._add_search_dir_info(error_lines, nonexistent_dir)
        self.assertEqual(len(error_lines), 1)
        self.assertIn(str(nonexistent_dir), error_lines[0])
        self.assertIn("directory does not exist", error_lines[0])

    def test_add_search_dir_info_ignores_init_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            search_dir = Path(temp_dir)
            init_file = search_dir / "__init__.py"
            init_file.write_text("")
            error_lines: List[str] = []
            ErrorMessageService._add_search_dir_info(error_lines, search_dir)
            self.assertEqual(len(error_lines), 1)
            self.assertIn("no .py files found", error_lines[0])

    def test_add_project_root_search_info_with_hooks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            hook_file = project_root / "test_hook.py"
            hook_file.write_text("test")
            self.service.hook_discovery_service.project_root = project_root
            error_lines: List[str] = []
            self.service._add_project_root_search_info(error_lines)
            self.assertEqual(len(error_lines), 1)
            self.assertIn(str(project_root), error_lines[0])
            self.assertIn("1 *_hook.py files", error_lines[0])

    def test_add_project_root_search_info_without_hooks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            self.service.hook_discovery_service.project_root = project_root
            error_lines: List[str] = []
            self.service._add_project_root_search_info(error_lines)
            self.assertEqual(len(error_lines), 1)
            self.assertIn(str(project_root), error_lines[0])
            self.assertIn("no *_hook.py files found", error_lines[0])

    def test_add_project_root_search_info_no_project_root(self):
        self.service.hook_discovery_service.project_root = None  # type: ignore[assignment]
        error_lines: List[str] = []
        self.service._add_project_root_search_info(error_lines)
        self.assertEqual(len(error_lines), 0)

    def test_add_hook_search_paths_info_with_relative_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = Path(temp_dir)
            githooks_dir = cwd / "githooks"
            githooks_dir.mkdir()
            test_file = githooks_dir / "test.py"
            test_file.write_text("test")
            self.service.hook_discovery_service.hook_search_paths = ["githooks"]
            with patch("pathlib.Path.cwd", return_value=cwd):
                error_lines: List[str] = []
                self.service._add_hook_search_paths_info(error_lines)
                self.assertGreater(len(error_lines), 0)
                self.assertIn("githooks", str(error_lines))

    def test_add_hook_search_paths_info_with_absolute_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            abs_path = Path(temp_dir) / "custom_hooks"
            abs_path.mkdir()
            test_file = abs_path / "test.py"
            test_file.write_text("test")
            self.service.hook_discovery_service.hook_search_paths = [str(abs_path)]
            error_lines: List[str] = []
            self.service._add_hook_search_paths_info(error_lines)
            self.assertGreater(len(error_lines), 0)
            error_text = " ".join(error_lines)
            self.assertIn("custom_hooks", error_text)

    def test_add_hook_search_paths_info_with_multiple_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = Path(temp_dir)
            path1 = cwd / "path1"
            path1.mkdir()
            path2 = cwd / "path2"
            path2.mkdir()
            self.service.hook_discovery_service.hook_search_paths = [
                "path1",
                "path2",
            ]
            with patch("pathlib.Path.cwd", return_value=cwd):
                error_lines: List[str] = []
                self.service._add_hook_search_paths_info(error_lines)
                self.assertGreaterEqual(len(error_lines), 2)


if __name__ == "__main__":
    unittest.main()
