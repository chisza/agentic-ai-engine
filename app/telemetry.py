"""OpenTelemetry setup for Cloud Trace, Cloud Monitoring, and Cloud Logging.

GCP observability overview
--------------------------
Cloud Trace      – distributed traces for every agent invocation, LLM call,
                   and tool execution (ADK instruments these automatically).
Cloud Monitoring – metrics exported via OpenTelemetry (token usage, latency,
                   request counts recorded by the ADK MeterProvider).
Cloud Logging    – structured logs via structlog (already wired in config.py)
                   plus gen_ai OTel log events forwarded by the ADK logger.
Cloud Audit Logs – automatically enabled in GCP for all Admin Activity and
                   configurable Data Access events; no code required here.

This module calls ADK's ``maybe_set_otel_providers()`` which:
  1. Registers the supplied span processors / metric readers / log processors.
  2. Skips silently if a provider was already set externally.
  3. Also picks up standard OTEL_EXPORTER_OTLP_* env vars automatically.
"""

from __future__ import annotations

import structlog

from app import config

logger = structlog.get_logger(__name__)

_SERVICE_NAME = "agentic-ai-engine"


def setup_telemetry() -> None:
    """Configure OpenTelemetry with GCP exporters.

    A no-op when ``TELEMETRY_ENABLED`` is False (the default locally).
    Logs a warning and continues if any exporter fails to initialise —
    the application still starts, just without telemetry.
    """
    if not config.TELEMETRY_ENABLED:
        logger.info(
            "OpenTelemetry disabled locally "
            "(set TELEMETRY_ENABLED=true to enable)"
        )
        return

    try:
        _configure_gcp_telemetry()
        logger.info(
            "OpenTelemetry configured",
            exporters=["CloudTrace", "CloudMonitoring"],
            service=_SERVICE_NAME,
        )
    except Exception as exc:
        logger.warning(
            "OpenTelemetry setup failed — running without telemetry",
            error=str(exc),
        )


def _configure_gcp_telemetry() -> None:
    from google.adk.telemetry.setup import OTelHooks, maybe_set_otel_providers
    from opentelemetry.exporter.cloud_monitoring import CloudMonitoringMetricsExporter
    from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
    from opentelemetry.resourcedetector.gcp_resource_detector import (
        GoogleCloudResourceDetector,
    )
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    # Build the OTel resource — GCP detector adds project_id, zone, etc.
    # Falls back to a plain service-name resource if the metadata server
    # is unreachable (e.g. during local testing with the flag enabled).
    try:
        gcp_resource = GoogleCloudResourceDetector(raise_on_error=False).detect()
    except Exception:
        gcp_resource = Resource.get_empty()

    resource = gcp_resource.merge(Resource({SERVICE_NAME: _SERVICE_NAME}))

    hooks = OTelHooks(
        # Cloud Trace: every ADK agent/LLM/tool span
        span_processors=[
            BatchSpanProcessor(
                CloudTraceSpanExporter(project_id=config.GOOGLE_CLOUD_PROJECT)
            )
        ],
        # Cloud Monitoring: ADK token/latency metrics, 60 s export interval
        metric_readers=[
            PeriodicExportingMetricReader(
                CloudMonitoringMetricsExporter(
                    project_id=config.GOOGLE_CLOUD_PROJECT
                ),
                export_interval_millis=60_000,
            )
        ],
        # Cloud Logging for gen_ai OTel events is handled by structlog +
        # the GCP Cloud Logging sink — no separate log processor needed.
    )

    maybe_set_otel_providers([hooks], otel_resource=resource)
