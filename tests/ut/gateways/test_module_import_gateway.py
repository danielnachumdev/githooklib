import sys
import tempfile
import unittest
from builtins import __import__
from pathlib import Path
from unittest.mock import patch, MagicMock

from githooklib.gateways.module_import_gateway import ModuleImportGateway
from tests.base_test_case import BaseTestCase


class TestModuleImportGateway(BaseTestCase):
    def setUp(self):
        self.gateway = ModuleImportGateway()
        self.original_sys_path = sys.path.copy()

    def tearDown(self):
        sys.path[:] = self.original_sys_path

    def test_convert_module_name_to_file_path(self):
        result = ModuleImportGateway.convert_module_name_to_file_path("test.module")
        self.assertEqual(result, Path("test/module.py"))

    def test_convert_module_name_to_file_path_single_module(self):
        result = ModuleImportGateway.convert_module_name_to_file_path("test")
        self.assertEqual(result, Path("test.py"))

    def test_convert_module_name_to_file_path_nested_module(self):
        result = ModuleImportGateway.convert_module_name_to_file_path("a.b.c.d")
        self.assertEqual(result, Path("a/b/c/d.py"))

    def test_find_module_file_with_project_root_returns_relative_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            module_file = project_root / "test_module.py"
            module_file.write_text("test")
            with patch("importlib.util.find_spec") as mock_find_spec:
                mock_spec = MagicMock()
                mock_spec.origin = str(module_file)
                mock_find_spec.return_value = mock_spec
                result = ModuleImportGateway.find_module_file(
                    "test_module", project_root
                )
                self.assertEqual(result, "test_module.py")

    def test_find_module_file_without_project_root_returns_absolute_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            module_file = Path(temp_dir) / "test_module.py"
            module_file.write_text("test")
            with patch("importlib.util.find_spec") as mock_find_spec:
                mock_spec = MagicMock()
                mock_spec.origin = str(module_file)
                mock_find_spec.return_value = mock_spec
                result = ModuleImportGateway.find_module_file("test_module", None)
                self.assertEqual(result, str(module_file))

    def test_find_module_file_not_relative_to_project_root_returns_absolute_path(
        self,
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "project"
            project_root.mkdir()
            module_file = Path(temp_dir) / "test_module.py"
            module_file.write_text("test")
            with patch("importlib.util.find_spec") as mock_find_spec:
                mock_spec = MagicMock()
                mock_spec.origin = str(module_file)
                mock_find_spec.return_value = mock_spec
                result = ModuleImportGateway.find_module_file(
                    "test_module", project_root
                )
                self.assertEqual(result, str(module_file))

    def test_find_module_file_returns_none_when_spec_not_found(self):
        with patch("importlib.util.find_spec", return_value=None):
            result = ModuleImportGateway.find_module_file("nonexistent", None)
            self.assertIsNone(result)

    def test_find_module_file_returns_none_when_spec_origin_missing(self):
        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_spec = MagicMock()
            mock_spec.origin = None
            mock_find_spec.return_value = mock_spec
            result = ModuleImportGateway.find_module_file("test", None)
            self.assertIsNone(result)

    def test_find_module_file_handles_import_error(self):
        with patch("importlib.util.find_spec", side_effect=ImportError()):
            result = ModuleImportGateway.find_module_file("test", None)
            self.assertIsNone(result)

    def test_add_to_sys_path_if_needed_adds_when_not_present(self):
        test_dir = Path("/test/directory")
        self.gateway._add_to_sys_path_if_needed(test_dir)
        self.assertIn(str(test_dir), sys.path)
        self.assertEqual(sys.path[0], str(test_dir))

    def test_add_to_sys_path_if_needed_does_not_add_when_present(self):
        test_dir = Path("/test/directory")
        sys.path.insert(0, str(test_dir))
        initial_length = len(sys.path)
        self.gateway._add_to_sys_path_if_needed(test_dir)
        self.assertEqual(len(sys.path), initial_length)
        self.assertEqual(sys.path.count(str(test_dir)), 1)

    def test_import_relative_module(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            module_dir = base_dir / "test" / "module"
            module_dir.mkdir(parents=True)
            module_file = module_dir / "__init__.py"
            module_file.write_text("")
            relative_path = Path("test/module/__init__.py")
            original_import = __import__
            call_count = 0
            mock_module = MagicMock()

            def side_effect(name, *args, **kwargs):
                nonlocal call_count
                if name == "test.module.__init__":
                    call_count += 1
                    return mock_module
                return original_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=side_effect):
                self.gateway._import_relative_module(relative_path, base_dir)
                self.assertEqual(1, call_count)

    def test_import_absolute_module(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            module_file = Path(temp_dir) / "test_module.py"
            module_file.write_text("")
            original_import = __import__
            call_count = 0
            mock_module = MagicMock()

            def side_effect(name, *args, **kwargs):
                nonlocal call_count
                if name == "test_module":
                    call_count += 1
                    return mock_module
                return original_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=side_effect):
                self.gateway._import_absolute_module(module_file)
                self.assertEqual(1, call_count)


if __name__ == "__main__":
    unittest.main()
