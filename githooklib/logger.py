import logging
import sys
from typing import IO


class StreamRouter(logging.Handler):
    def __init__(self, stdout: IO, stderr: IO) -> None:
        super().__init__()
        self.stdout = stdout
        self.stderr = stderr

    def emit(self, record):
        try:
            msg = self._format_message(record)
            self._write_to_stream(record, msg)
        except Exception:  # pylint: disable=broad-exception-caught
            self.handleError(record)

    def _format_message(self, record) -> str:
        return self.format(record) + "\n"

    def _write_to_stream(self, record, msg: str):
        if self._is_error_level(record):
            self._write_to_stderr(msg)
        else:
            self._write_to_stdout(msg)

    def _is_error_level(self, record) -> bool:
        return record.levelno >= logging.ERROR

    def _write_to_stderr(self, msg: str):
        self.stderr.write(msg)
        self.stderr.flush()

    def _write_to_stdout(self, msg: str):
        self.stdout.write(msg)
        self.stdout.flush()


class Logger:
    def __init__(self, prefix: str = "[githooklib]", level: int = logging.INFO):
        self.prefix = prefix
        self.logger = logging.getLogger(prefix)
        if not self.logger.handlers:
            self._setup_handlers(level)
        else:
            self.set_level(level)

    def set_level(self, level: int) -> None:
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)

    def _setup_handlers(self, level: int = logging.INFO) -> None:
        handler = self._create_handler(level)
        self._configure_logger(handler, level)

    def _create_handler(self, level: int) -> StreamRouter:
        handler = StreamRouter(sys.stdout, sys.stderr)
        formatter = self._create_formatter()
        handler.setFormatter(formatter)
        handler.setLevel(level)
        return handler

    def _configure_logger(self, handler: StreamRouter, level: int):
        self.logger.addHandler(handler)
        self.logger.setLevel(level)
        self.logger.propagate = False

    def _create_formatter(self) -> logging.Formatter:
        return logging.Formatter(
            f"{self.prefix} [%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def log(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)

    def info(self, message: str):
        self.logger.info(" %s", message)

    def success(self, message: str):
        self.logger.info("[V] %s", message)

    def warning(self, message: str):
        self.logger.warning(message)

    def debug(self, message: str):
        self.logger.debug(message)


__all__ = ["Logger"]
