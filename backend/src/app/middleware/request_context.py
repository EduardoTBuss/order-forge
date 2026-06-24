from contextvars import ContextVar

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

request_context: ContextVar[Request] = ContextVar("request_context")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request_context.set(request)
        try:
            response = await call_next(request)
        finally:
            request_context.reset(token)
        return response


def add_request_context_middleware(app: FastAPI) -> None:
    app.add_middleware(RequestContextMiddleware)
