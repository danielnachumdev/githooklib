from .base_test_case import OperationsBaseTestCase


class TestListE2E(OperationsBaseTestCase):
    def test_on_githooklib_folder(self):
        result = self.githooklib(["list"])
        self.assertIn("pre-push", result.stdout)
        self.assertIn("pre-commit", result.stdout)
