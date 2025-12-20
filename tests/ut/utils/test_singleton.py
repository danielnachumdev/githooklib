import unittest

from githooklib.utils.singleton import singleton
from tests.base_test_case import BaseTestCase


@singleton
class MockSingletonClass:
    def __init__(self):
        self.value = 0

    def increment(self):
        self.value += 1


class TestSingleton(BaseTestCase):
    def test_singleton_returns_same_instance(self):
        instance1 = MockSingletonClass()
        instance2 = MockSingletonClass()
        self.assertIs(instance1, instance2)

    def test_singleton_initialization_only_once(self):
        instance1 = MockSingletonClass()
        instance1.increment()
        instance1.increment()
        instance2 = MockSingletonClass()
        self.assertEqual(instance2.value, 2)
        self.assertIs(instance1, instance2)

    def test_singleton_with_arguments(self):
        @singleton
        class TestClassWithArgs:
            def __init__(self, value):
                self.value = value

        instance1 = TestClassWithArgs(10)
        instance2 = TestClassWithArgs(20)
        self.assertIs(instance1, instance2)
        self.assertEqual(instance1.value, 10)
        self.assertEqual(instance2.value, 10)


if __name__ == "__main__":
    unittest.main()
