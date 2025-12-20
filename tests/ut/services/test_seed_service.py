import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from githooklib.services.seed_service import HookSeedingService
from githooklib.gateways.seed_gateway import SeedGateway
from tests.base_test_case import BaseTestCase


class TestHookSeedingService(BaseTestCase):
    def setUp(self):
        self.service = HookSeedingService()

    def test_get_target_hook_path_returns_correct_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            result = self.service.get_target_hook_path("test-example", project_root)
            expected = project_root / "githooks" / "test-example.py"
            self.assertEqual(result, expected)

    def test_does_target_hook_exist_returns_true_when_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            target_dir = project_root / "githooks"
            target_dir.mkdir()
            target_file = target_dir / "test-example.py"
            target_file.write_text("test content")
            result = self.service.does_target_hook_exist("test-example", project_root)
            self.assertTrue(result)

    def test_does_target_hook_exist_returns_false_when_not_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            result = self.service.does_target_hook_exist("test-example", project_root)
            self.assertFalse(result)

    def test_seed_hook_success_when_example_available_and_target_not_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            source_file = Path(temp_dir) / "source.py"
            source_file.write_text("source content")
            with patch.object(
                self.service.examples_gateway,
                "is_example_available",
                return_value=True,
            ):
                with patch.object(
                    self.service.examples_gateway,
                    "get_example_path",
                    return_value=source_file,
                ):
                    with patch.object(
                        self.service,
                        "does_target_hook_exist",
                        return_value=False,
                    ):
                        result = self.service.seed_hook("test-example", project_root)
                        self.assertTrue(result)
                        target_file = project_root / "githooks" / "test-example.py"
                        self.assertTrue(target_file.exists())
                        self.assertEqual(target_file.read_text(), "source content")

    def test_seed_hook_fails_when_example_not_available(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            with patch.object(
                self.service.examples_gateway,
                "is_example_available",
                return_value=False,
            ):
                result = self.service.seed_hook("non-existent-example", project_root)
                self.assertFalse(result)

    def test_seed_hook_fails_when_target_already_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            with patch.object(
                self.service.examples_gateway,
                "is_example_available",
                return_value=True,
            ):
                with patch.object(
                    self.service,
                    "does_target_hook_exist",
                    return_value=True,
                ):
                    result = self.service.seed_hook("test-example", project_root)
                    self.assertFalse(result)

    def test_seed_hook_creates_githooks_directory_if_not_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            source_file = Path(temp_dir) / "source.py"
            source_file.write_text("source content")
            with patch.object(
                self.service.examples_gateway,
                "is_example_available",
                return_value=True,
            ):
                with patch.object(
                    self.service.examples_gateway,
                    "get_example_path",
                    return_value=source_file,
                ):
                    with patch.object(
                        self.service,
                        "does_target_hook_exist",
                        return_value=False,
                    ):
                        self.service.seed_hook("test-example", project_root)
                        target_dir = project_root / "githooks"
                        self.assertTrue(target_dir.exists())
                        self.assertTrue(target_dir.is_dir())

    def test_get_seed_failure_details_example_not_found(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            with patch.object(
                self.service.examples_gateway,
                "is_example_available",
                return_value=False,
            ):
                with patch.object(
                    self.service.examples_gateway,
                    "get_available_examples",
                    return_value=["example1", "example2"],
                ):
                    result = self.service.get_seed_failure_details(
                        "non-existent", project_root
                    )
                    self.assertTrue(result.example_not_found)
                    self.assertFalse(result.project_root_not_found)
                    self.assertFalse(result.target_hook_already_exists)
                    self.assertEqual(
                        result.available_examples, ["example1", "example2"]
                    )

    def test_get_seed_failure_details_project_root_not_found(self):
        with patch.object(
            self.service.examples_gateway,
            "is_example_available",
            return_value=True,
        ):
            result = self.service.get_seed_failure_details("test-example", None)
            self.assertFalse(result.example_not_found)
            self.assertTrue(result.project_root_not_found)
            self.assertFalse(result.target_hook_already_exists)
            self.assertIsNone(result.target_hook_path)

    def test_get_seed_failure_details_target_hook_already_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            with patch.object(
                self.service.examples_gateway,
                "is_example_available",
                return_value=True,
            ):
                with patch.object(
                    self.service,
                    "does_target_hook_exist",
                    return_value=True,
                ):
                    result = self.service.get_seed_failure_details(
                        "test-example", project_root
                    )
                    self.assertFalse(result.example_not_found)
                    self.assertFalse(result.project_root_not_found)
                    self.assertTrue(result.target_hook_already_exists)
                    expected_path = project_root / "githooks" / "test-example.py"
                    self.assertEqual(result.target_hook_path, expected_path)

    def test_get_seed_failure_details_all_conditions_false(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            with patch.object(
                self.service.examples_gateway,
                "is_example_available",
                return_value=True,
            ):
                with patch.object(
                    self.service,
                    "does_target_hook_exist",
                    return_value=False,
                ):
                    result = self.service.get_seed_failure_details(
                        "test-example", project_root
                    )
                    self.assertFalse(result.example_not_found)
                    self.assertFalse(result.project_root_not_found)
                    self.assertFalse(result.target_hook_already_exists)
                    expected_path = project_root / "githooks" / "test-example.py"
                    self.assertEqual(result.target_hook_path, expected_path)


if __name__ == "__main__":
    unittest.main()
