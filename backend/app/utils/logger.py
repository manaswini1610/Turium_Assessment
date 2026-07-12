import logging
import sys

SENSITIVE_MARKERS = ("api_key", "apikey", "authorization", "secret", "bearer ")


class RedactSensitiveFilter(logging.Filter):
    """Prevents accidental logging of API keys or other secrets."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage().lower()
        if any(marker in message for marker in SENSITIVE_MARKERS):
            record.msg = "[REDACTED LOG MESSAGE - POSSIBLE SENSITIVE CONTENT]"
            record.args = ()
        return True


def configure_logging(level: int = logging.INFO) -> None:
    """Configures structured, single-line logging for the whole application."""
    formatter = logging.Formatter(
        fmt='{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        '"logger": "%(name)s", "message": "%(message)s"}'
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RedactSensitiveFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    # Quiet down noisy third-party loggers while keeping our own app.* logs verbose.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
