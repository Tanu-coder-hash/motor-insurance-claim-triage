
import logging
import structlog

from libs.common.correlation import get_correlation_id


def add_correlation_id(logger, method_name, event_dict):
    """Add the current correlation ID to every log entry."""
    event_dict["correlation_id"] = get_correlation_id()
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structured JSON logging for all project services."""

    logging.basicConfig(
        format="%(message)s",
        level=log_level.upper(),
        handlers=[logging.StreamHandler()],
        force=True,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            add_correlation_id,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "motor_insurance"):
    """Return a structured logger."""
    return structlog.get_logger(name)
