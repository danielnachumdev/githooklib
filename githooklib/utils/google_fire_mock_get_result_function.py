import functools
import inspect
from pathlib import Path
from typing import Any, Callable

import fire
import fire.value_types
from fire.trace import FireTrace


class FireGetResultMockClass:
    def __init__(self, original_method: Callable[[FireTrace], Any]) -> None:
        self.original_method = original_method
        functools.update_wrapper(self, original_method)

    def __call__(self, self_instance: FireTrace) -> Any:
        try:
            frame = inspect.currentframe()
            caller_frame = frame.f_back.f_back  # type: ignore[union-attr]
            info = inspect.getframeinfo(caller_frame)  # type: ignore[arg-type]
            path_suffix = "/".join(Path(info.filename).parts[-2:])
            if info.function == "_PrintResult" and path_suffix == "fire/core.py":
                result = self.original_method(self_instance)
                if isinstance(result, fire.value_types.VALUE_TYPES):
                    return None
                return result
        except Exception:  # pylint: disable=broad-except
            pass
        return self.original_method(self_instance)


def FireGetResultMockClassDelegator(original_method):
    def wrapper(self_instance: FireTrace) -> Any:
        return FireGetResultMockClass(original_method)(self_instance)

    return wrapper


def FireGetResultMockFunction(
    original_method: Callable[[FireTrace], Any],
) -> Callable[[FireTrace], Any]:
    @functools.wraps(original_method)
    def mock_impl(self: FireTrace):
        try:
            frame = inspect.currentframe()
            caller_frame = frame.f_back  # type: ignore[union-attr]
            info = inspect.getframeinfo(caller_frame)  # type: ignore[arg-type]
            path_suffix = "/".join(Path(info.filename).parts[-2:])
            if info.function == "_PrintResult" and path_suffix == "fire/core.py":
                result = original_method(self)
                if isinstance(result, fire.value_types.VALUE_TYPES):
                    return None
                return result
        except Exception:  # pylint: disable=broad-except
            pass
        return original_method(self)

    return mock_impl


FireGetResultMock = FireGetResultMockFunction

__all__ = ["FireGetResultMock"]
