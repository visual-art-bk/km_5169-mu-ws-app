import logging


class Logger:

    def __init__(
        self,
        name: str,
        log_file: str,
        level: int = logging.INFO,
        max_bytes: int = 5 * 1024 * 1024,
        backup_count: int = 5,
    ):
        from logging.handlers import RotatingFileHandler
        import sys

        self.logger = logging.getLogger(name)

        if not self.logger.handlers:  # 핸들러가 없는 경우에만 설정
            self.logger.setLevel(level)
            self.logger.propagate = False

            # Formatter for logs
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

            # Stream Handler (for terminal output)
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setLevel(level)
            stream_handler.setFormatter(formatter)

            if hasattr(stream_handler.stream, "reconfigure"):
                stream_handler.stream.reconfigure(encoding="utf-8")
            self.logger.addHandler(stream_handler)

            # Rotating File Handler (for file output with rotation)
            log_file = self._get_unique_log_file(log_file)
            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def _get_unique_log_file(self, log_file: str) -> str:
        import os

        """Checks if a log file exists and adds a sequential number if it does."""
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        base, ext = os.path.splitext(log_file)
        counter = 1

        while os.path.exists(log_file):
            log_file = f"{base}_{counter}{ext}"
            counter += 1

        return log_file

    def log_exception(self, message: str, exc: Exception):
        import traceback

        """Logs an exception with traceback."""
        self.logger.error(f"{message}\n{traceback.format_exc()}")

    def get_logger(self):
        """Returns the configured logger instance."""
        return self.logger
