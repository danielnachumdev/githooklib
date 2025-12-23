import unittest

from typing import TypeVar, Optional, cast

from githooklib import get_logger, Logger

try:
    from typing import TypeGuard
except ImportError:
    from typing_extensions import TypeGuard

T = TypeVar("T")


class BaseTestCase(unittest.TestCase):
    logger: Logger

    @classmethod
    def setUpClass(cls) -> None:
        cls.logger = get_logger(__name__, prefix=cls.__name__)
        cls.logger.setLevel(0)

    def unwrap_optional(self, obj: Optional[T], msg: Optional[str] = None) -> T:
        super().assertIsNotNone(obj, msg)
        return cast(T, obj)
