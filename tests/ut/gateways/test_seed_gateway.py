import unittest
from pathlib import Path
from unittest.mock import patch

from githooklib.gateways.seed_gateway import SeedGateway
from tests.base_test_case import BaseTestCase


class TestSeedGateway(BaseTestCase):
    def setUp(self):
        self.gateway = SeedGateway()

    def test_get_available_examples_returns_list(self):
        result = self.gateway.get_available_examples()
        self.assertIsInstance(result, list)

    def test_get_available_examples_caches_result(self):
        result1 = self.gateway.get_available_examples()
        result2 = self.gateway.get_available_examples()
        self.assertEqual(result1, result2)

    def test_is_example_available_returns_true_when_exists(self):
        examples = self.gateway.get_available_examples()
        if examples:
            result = self.gateway.is_example_available(examples[0])
            self.assertTrue(result)

    def test_is_example_available_returns_false_when_not_exists(self):
        result = self.gateway.is_example_available("non-existent-example-xyz123")
        self.assertFalse(result)

    def test_is_example_available_caches_result(self):
        examples = self.gateway.get_available_examples()
        if examples:
            with patch.object(self.gateway, "_get_examples_folder_path") as mock_path:
                result1 = self.gateway.is_example_available(examples[0])
                result2 = self.gateway.is_example_available(examples[0])
                self.assertEqual(result1, result2)

    def test_get_example_path_returns_path(self):
        examples = self.gateway.get_available_examples()
        if examples:
            result = self.gateway.get_example_path(examples[0])
            self.assertIsInstance(result, Path)
            self.assertTrue(result.name.endswith(".py"))

    def test_get_example_path_caches_result(self):
        examples = self.gateway.get_available_examples()
        if examples:
            result1 = self.gateway.get_example_path(examples[0])
            result2 = self.gateway.get_example_path(examples[0])
            self.assertEqual(result1, result2)

    def test_get_githooklib_path_returns_path(self):
        result = self.gateway._get_githooklib_path()
        self.assertIsInstance(result, Path)

    def test_get_examples_folder_path_returns_path(self):
        result = self.gateway._get_examples_folder_path()
        self.assertIsInstance(result, Path)
        self.assertEqual(result.name, "examples")


if __name__ == "__main__":
    unittest.main()
