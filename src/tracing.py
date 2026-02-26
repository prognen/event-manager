import os
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from fastapi import FastAPI


def setup_tracing(app: FastAPI) -> None:
    if os.getenv("ENABLE_TRACING", "0") != "1":
        return

    provider = TracerProvider(resource=Resource.create({"service.name": "event_app"}))

    exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True)

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    RequestsInstrumentor().instrument()
