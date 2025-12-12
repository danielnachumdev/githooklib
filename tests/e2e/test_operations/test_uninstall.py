import unittest

from .base_test_case import OperationsBaseTestCase


class TestUninstallE2E(OperationsBaseTestCase):
    def test_uninstall(self):
        available_hooks = set(self.list())
        installed_hooks = set(
            hook.strip("(githooklib)").strip()
            for hook in self.show()
            if "external" not in hook
        )
        checkable_hooks = installed_hooks.intersection(available_hooks)
        hook = checkable_hooks.pop()
        self.githooklib(["uninstall", hook])
        self.githooklib(["install", hook])


if __name__ == "__main__":
    unittest.main()
