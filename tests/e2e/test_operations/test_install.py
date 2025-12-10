import unittest

from .base_test_case import OperationsBaseTestCase


class TestInstallE2E(OperationsBaseTestCase):
    def test_isntall_sanity_check(self):
        self.githooklib(["install", "pre-push"])


if __name__ == "__main__":
    unittest.main()
