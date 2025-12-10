import unittest
from .base_test_case import OperationsBaseTestCase


class TestRunE2E(OperationsBaseTestCase):

    def test_install_sanity_check(self):
        self.githooklib(["run", "pre-push"], stdin="git push")


if __name__ == "__main__":
    unittest.main()
