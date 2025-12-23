import logging
import inspect
import sys
from typing import IO, Optional
import os

TRACE = 5
SUCCESS = logging.INFO + 1
logging.addLevelName(TRACE, "TRACE")
logging.addLevelName(SUCCESS, "SUCCESS")

_configured_log_level: Optional[int] = None


class LogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        pathname = os.path.normcase(record.pathname)
        return (
            "githooklib" in pathname
            or record.name.startswith("githooklib")
            or "githooks" in pathname
        )


class StreamHandler(logging.Handler):
    def __init__(self, stdout: IO, stderr: IO) -> None:
        super().__init__()
        self.stdout = stdout
        self.stderr = stderr

    def emit(self, record) -> None:
        try:
            msg = self.format(record) + "\n"
            if record.levelno >= logging.ERROR:
                self._write(stderr=True, msg=msg)
            else:
                self._write(stderr=False, msg=msg)
        except Exception:  # pylint: disable=broad-exception-caught
            self.handleError(record)

    def _write(self, stderr: bool, msg: str) -> None:
        stream = self.stderr if stderr else self.stdout
        try:
            from tqdm import tqdm

            tqdm.write(msg, end="")
        except ImportError:
            stream.write(msg)
            stream.flush()


class Logger(logging.Logger):
    def success(self, message: str, *args, **kwargs) -> None:
        if self.isEnabledFor(SUCCESS):
            self._log(SUCCESS, message, args, **kwargs)

    def trace(self, message: str, *args, **kwargs) -> None:
        if self.isEnabledFor(TRACE):
            self._log(TRACE, message, args, **kwargs)


def get_logger(name: Optional[str] = None, prefix: Optional[str] = None) -> Logger:
    if name is None:

        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get("__name__", "githooklib")
        else:
            name = "githooklib"

    if prefix is None:
        prefix = "githooklib"

    manager = logging.Logger.manager
    if name in manager.loggerDict:
        existing = manager.loggerDict[name]
        if isinstance(existing, Logger):
            return existing

    logger = Logger(name)
    handler = StreamHandler(sys.stdout, sys.stderr)
    formatter = logging.Formatter(
        f"[{prefix}] %(levelname)-7s %(asctime)s %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    handler.addFilter(LogFilter())
    handler.setLevel(TRACE)
    logger.addHandler(handler)

    initial_level = (
        _configured_log_level if _configured_log_level is not None else logging.INFO
    )
    logger.setLevel(initial_level)
    handler.setLevel(initial_level)

    manager.loggerDict[name] = logger

    return logger


def setup_logging() -> None:
    global _configured_log_level

    if "--trace" in sys.argv:
        level = TRACE
        sys.argv.remove("--trace")
        if "--debug" in sys.argv:
            sys.argv.remove("--debug")
    elif "--debug" in sys.argv:
        level = logging.DEBUG
        sys.argv.remove("--debug")
    else:
        level = logging.INFO

    _configured_log_level = level

    manager = logging.Logger.manager
    for logger_name, logger_instance in manager.loggerDict.items():
        if isinstance(logger_instance, Logger):
            logger_instance.setLevel(level)
            for handler in logger_instance.handlers:
                handler.setLevel(level)


__all__ = ["Logger", "get_logger", "TRACE", "SUCCESS", "StreamHandler", "setup_logging"]
