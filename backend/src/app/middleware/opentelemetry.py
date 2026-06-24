import re

from fastapi import FastAPI, Request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.middleware.base import BaseHTTPMiddleware


def strip_aca_revision(hostname: str) -> str:
    if not hostname:
        return hostname
    first, sep, rest = hostname.partition(".")
    first_clean = re.sub(r"--\d+$", "", first)
    return f"{first_clean}{sep}{rest}" if sep else first_clean


def setup_telemetry(app: FastAPI, service_name: str) -> None:
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    otlp_exporter = OTLPSpanExporter()
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)

    HTTPXClientInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    # ---- Logging: attach trace/span IDs to your logs ----
    # This adds attributes (otelTraceID, otelSpanID, service.name) to log records,
    # and (optionally) sets a useful log format.
    LoggingInstrumentor().instrument(set_logging_format=True)


class OpenTelemetryHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        span = trace.get_current_span()
        if span and span.is_recording():
            for key, value in request.headers.items():
                attr_key = f"http.request.header.{key.lower()}"
                span.set_attribute(attr_key, value)
        response = await call_next(request)
        span = trace.get_current_span()
        if span and span.is_recording():
            for key, value in response.headers.items():
                attr_key = f"http.response.header.{key.lower()}"
                span.set_attribute(attr_key, value)
        return response


def add_opentelemetry_middleware(app: FastAPI, hostname: str) -> None:
    setup_telemetry(app, strip_aca_revision(hostname))
    app.add_middleware(OpenTelemetryHeadersMiddleware)


def instrument_sqlalchemy_engine(engine) -> None:
    """
    Instrument a SQLAlchemy Engine (sync or async engine).
    Call this right after you create the engine, before using it.
    """
    target = engine.sync_engine if isinstance(engine, AsyncEngine) else engine

    if getattr(target, "info", {}).get("otel_sqlalchemy_instrumented"):
        return

    try:
        SQLAlchemyInstrumentor().uninstrument()
    except Exception:
        pass

    SQLAlchemyInstrumentor().instrument(
        engine=target,
        # record_sql_statement=True,          # uncomment if you want full SQL text (watch PII!)
        # capture_parameters=True,            # capture bound parameters (watch PII!)
        enable_commenter=False,
        commenter_options=None,
    )
