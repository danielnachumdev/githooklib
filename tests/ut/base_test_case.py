import unittest

from typing import TypeVar, Optional, cast

try:
    from typing import TypeGuard
except ImportError:
    from typing_extensions import TypeGuard

T = TypeVar("T")


class BaseTestCase(unittest.TestCase):
    def unwrap_optional(self, obj: Optional[T], msg: Optional[str] = None) -> T:
        super().assertIsNotNone(obj, msg)
        return cast(T, obj)
