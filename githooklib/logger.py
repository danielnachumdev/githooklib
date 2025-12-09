import logging
import sys
from pathlib import Path
from typing import IO, Optional


class StreamRouter(logging.Handler):
    def __init__(self, stdout: IO, stderr: IO) -> None:
        super().__init__()
        self.stdout = stdout
        self.stderr = stderr

    def emit(self, record) -> None:
        try:
            msg = self._format_message(record)
            self._write_to_stream(record, msg)
        except Exception:  # pylint: disable=broad-exception-caught
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
        self.stderr.write(msg)
        self.stderr.flush()

    def _write_to_stdout(self, msg: str) -> None:
        self.stdout.write(msg)
        self.stdout.flush()


class Logger(logging.Logger):
    def __init__(self, prefix: str, level: int = logging.INFO) -> None:
        unique_name = f"{prefix}_{id(self)}"
        super().__init__(unique_name)
        self.prefix = prefix
        self.setLevel(level)
        self.propagate = False
        self._setup_handlers(level)

    def set_level(self, level: int) -> None:
        self.setLevel(level)
        for handler in self.handlers:
            handler.setLevel(level)

    def _setup_handlers(self, level: int = logging.INFO) -> None:
        handler = self._create_handler(level)
        self.addHandler(handler)

    def _create_handler(self, level: int) -> StreamRouter:
        handler = StreamRouter(sys.stdout, sys.stderr)
        formatter = self._create_formatter()
        handler.setFormatter(formatter)
        handler.setLevel(level)
        return handler

    def _create_formatter(self) -> logging.Formatter:
        return logging.Formatter(
            f"[{self.prefix} - %(levelname)-5s - %(asctime)s- %(filename)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def success(self, message: str) -> None:
        super().info(f"[V] %s", message)


def get_logger(
    file_path: str, level: int = logging.INFO, prefix: str = "githooklib"
) -> Logger:
    if prefix is None:
        filename = Path(file_path).stem
        prefix = f"[{filename}]"
    return Logger(prefix=prefix, level=level)


__all__ = ["Logger", "get_logger"]
