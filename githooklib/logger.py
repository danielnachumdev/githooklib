import logging
import sys
from types import FrameType
from typing import IO, Optional, Union, Dict
import os

TRACE = 5
SUCCESS = logging.INFO + 1
logging.addLevelName(TRACE, "TRACE")
logging.addLevelName(SUCCESS, "SUCCESS")


def is_internal_frame(frame: FrameType) -> bool:
    filename = os.path.normcase(frame.f_code.co_filename)
    return (
        filename.endswith("logging\\__init__.py")
        or ("importlib" in filename and "_bootstrap" in filename)
        or os.path.normcase(frame.f_code.co_filename).lower() == __file__.lower()
    )


setattr(logging, "_is_internal_frame", is_internal_frame)

_DISPLAY_NAME_MAP: Dict[str, str] = {}
_ROOT_LOGGER_INITIALIZED = False


def _is_from_githooklib(record: logging.LogRecord) -> bool:
    pathname = os.path.normcase(record.pathname)
    return "githooklib" in pathname


def _is_from_hook_file(record: logging.LogRecord) -> bool:
    pathname = os.path.normcase(record.pathname)
    filename = os.path.basename(pathname)
    return "githooks" in pathname or filename.endswith("_hook.py")


class GithooklibFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.name.startswith("githooklib") or _is_from_hook_file(record)


class DisplayNameFormatter(logging.Formatter):
    def __init__(
        self, fmt: Optional[str] = None, datefmt: Optional[str] = None
    ) -> None:
        super().__init__(fmt, datefmt)
        self.default_formatter = logging.Formatter(
            "%(levelname)-7s %(asctime)s %(name)s:%(lineno)d | %(message)s",
            datefmt=datefmt or "%Y-%m-%d %H:%M:%S",
        )

    def format(self, record: logging.LogRecord) -> str:
        if _is_from_githooklib(record):
            display_name = _DISPLAY_NAME_MAP.get(record.name, "githooklib")
            record.display_name = display_name
            return super().format(record)
        else:
            return self.default_formatter.format(record)


def _get_root_logger() -> logging.Logger:
    global _ROOT_LOGGER_INITIALIZED
    root_logger = logging.root
    if not _ROOT_LOGGER_INITIALIZED:
        handler = StreamRouter(sys.stdout, sys.stderr)
        formatter = DisplayNameFormatter(
            "[%(display_name)s] %(levelname)-7s %(asctime)s %(filename)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(GithooklibFilter())
        handler.setLevel(logging.INFO)
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
        _ROOT_LOGGER_INITIALIZED = True
    return root_logger


class StreamRouter(logging.Handler):
    def __init__(self, stdout: IO, stderr: IO) -> None:
        super().__init__()
        self.stdout = stdout
        self.stderr = stderr

    def emit(self, record) -> None:
        try:
            msg = self._format_message(record)
            self._write_to_stream(record, msg)
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.handleError(record)

    def _format_message(self, record) -> str:
        return self.format(record) + "\n"

    def _write_to_stream(self, record, msg: str) -> None:
        if self._is_error_level(record):
            self._write_to_stderr(msg)
        else:
            self._write_to_stdout(msg)

    def _is_error_level(self, record) -> bool:
        return record.levelno >= logging.ERROR

    def _write_to_stderr(self, msg: str) -> None:
        try:
            from tqdm import tqdm

            tqdm.write(msg, end="")
        except ImportError:
            self.stderr.write(msg)
            self.stderr.flush()

    def _write_to_stdout(self, msg: str) -> None:
        try:
            from tqdm import tqdm

            tqdm.write(msg, end="")
        except ImportError:
            self.stdout.write(msg)
            self.stdout.flush()


class Logger(logging.Logger):
    def __init__(self, name: str, display_name: str = "githooklib") -> None:
        super().__init__(name)
        self.display_name = display_name
        self.propagate = True
        _get_root_logger()

    def setLevel(self, level: Union[int, str]) -> None:
        root_logger = _get_root_logger()
        root_logger.setLevel(level)
        for handler in root_logger.handlers:
            handler.setLevel(level)

    def success(self, message: str, *args, **kwargs) -> None:
        if self.isEnabledFor(SUCCESS):
            super()._log(SUCCESS, message, args, **kwargs)

    def trace(self, message: str, *args, **kwargs) -> None:
        if self.isEnabledFor(TRACE):
            super()._log(TRACE, message, args, **kwargs)


def get_logger(name: Optional[str] = None, display_name: str = "githooklib") -> Logger:
    if name is None:
        import inspect

        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get("__name__", "githooklib")
        else:
            name = "githooklib"

    manager = logging.Logger.manager
    if name in manager.loggerDict:
        existing_logger = manager.loggerDict[name]
        if isinstance(existing_logger, Logger):
            if hasattr(existing_logger, "display_name"):
                existing_logger.display_name = display_name
            _DISPLAY_NAME_MAP[name] = display_name
            return existing_logger
        else:
            del manager.loggerDict[name]

    logger = Logger(name, display_name)
    _DISPLAY_NAME_MAP[name] = display_name
    manager.loggerDict[name] = logger
    manager._fixupParents(logger)  # type: ignore[attr-defined]
    return logger


__all__ = ["Logger", "get_logger", "TRACE", "SUCCESS"]
