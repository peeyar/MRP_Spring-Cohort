"""Phoenix tracing setup for WarmPath."""

import logging

logger = logging.getLogger(__name__)


def setup_tracing(project_name: str = "warmpath") -> None:
    """Register Phoenix as the OTLP trace collector and instrument the OpenAI client.
    Call once at startup before the app is created.
    """
    try:
        from phoenix.otel import register
        from openinference.instrumentation.openai import OpenAIInstrumentor

        tracer_provider = register(
            project_name=project_name,
            endpoint="http://localhost:6006/v1/traces",
        )
        OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)
        logger.info(
            "Phoenix tracing enabled → http://localhost:6006 (project: %s)", project_name
        )
    except Exception as e:
        logger.warning("Phoenix tracing not available: %s", e)


def instrument_app(app) -> None:
    """Attach FastAPI instrumentation so every HTTP request gets a root span."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumentation attached")
    except Exception as e:
        logger.warning("FastAPI instrumentation not available: %s", e)
