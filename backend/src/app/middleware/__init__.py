import logging

from fastapi import FastAPI

from src.app.middleware.cors import add_cors_middleware
from src.app.middleware.opentelemetry import add_opentelemetry_middleware
from src.app.middleware.request_context import add_request_context_middleware
from src.settings import CONTAINER_APP_HOSTNAME

logger = logging.getLogger(__name__)


def add_middlewares(app: FastAPI) -> None:
    """
    Add middlewares to the FastAPI app.
    """
    add_cors_middleware(app)
    logger.info("CORS middleware added")
    add_request_context_middleware(app)
    logger.info("Request context middleware added")
    if CONTAINER_APP_HOSTNAME:
        try:
            add_opentelemetry_middleware(app, CONTAINER_APP_HOSTNAME)
            logger.info("OpenTelemetry middleware added")
        except Exception as e:
            logger.error(f"Failed to add OpenTelemetry middleware: {e}")
