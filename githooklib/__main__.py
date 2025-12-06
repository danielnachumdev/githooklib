# pylint: disable=invalid-name
import sys
from unittest.mock import patch

import fire
import fire.value_types

from .cli import CLI
from .utils import FireGetResultMock


def main() -> None:
    original_function = fire.trace.FireTrace.GetResult
    mock_function = FireGetResultMock(original_function)
    try:
        with patch("fire.trace.FireTrace.GetResult", mock_function):
            code = fire.Fire(CLI)
    except Exception:  # pylint: disable=broad-except
        sys.exit(1)

    sys.exit(code if isinstance(code, int) else 0)


if __name__ == "__main__":
    main()


__all__ = ["main"]
