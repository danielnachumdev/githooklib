import unittest
from .base_test_case import OperationsBaseTestCase


class TestRunE2E(OperationsBaseTestCase):

    def test_install_sanity_check(self):
        self.githooklib(["run", "pre-push"])

    def test_no_debug_or_trace(self):
        with self.new_temp_project() as root:
            stdout = self.githooklib(["run", "pre-commit"], cwd=root).stdout
            self.assertIn(self.get_default_print("pre-commit"), stdout)


if __name__ == "__main__":
    unittest.main()
