import logging
import os

from colorlog import ColoredFormatter, StreamHandler

# Imitates uvicorn alignment
LOGS_WITH_SPACES = {
    "DEBUG": "DEBUG:   ",
    "INFO": "INFO:    ",
    "WARNING": "WARNING: ",
    "ERROR": "ERROR:   ",
    "CRITICAL": "CRITICAL:",
}


class AlignedFormatter(ColoredFormatter):
    """Custom formatter to align log levels and colorize output."""

    def format(self, record):
        record.levelprefix = LOGS_WITH_SPACES.get(
            record.levelname, f"{record.levelname}:     "
        )
        record.name = f"\033[35m[{record.name}]\033[0m"  # Magenta
        return super().format(record)


def setup_logger(name: str = "") -> logging.Logger:
    """Set up a logger with colored output and aligned log levels."""

    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    handler = StreamHandler()
    handler.setFormatter(
        AlignedFormatter(
            "%(log_color)s%(levelprefix)s%(reset)s %(asctime)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG": "blue",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
    )

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(handler)
    logger.propagate = False

    _configure_third_party_loggers()

    return logger


def _configure_third_party_loggers() -> None:
    """Configure Azure SDK logging to reduce verbosity."""

    for third_party_logger_name in [
        # Azure
        "azure.core.pipeline.policies.http_logging_policy",
        "azure.core.pipeline.policies.retry",
        "azure.core.pipeline.transport",
        "azure.ai.formrecognizer",
        "azure.core",
        # Alembic
        "alembic",
        "alembic.runtime.migration",
        # HTTP clients / libraries
        "httpx",
        "httpcore",
        "urllib3",
        # OpenAI and LangChain
        "openai",
        "langchain",
        # MongoDB / PyMongo
        "pymongo",
        "pymongo.command",
        "pymongo.connection",
        "pymongo.serverSelection",
        "pymongo.topology",
    ]:
        third_party_logger = logging.getLogger(third_party_logger_name)
        third_party_logger.setLevel(logging.WARNING)
        third_party_logger.handlers.clear()
