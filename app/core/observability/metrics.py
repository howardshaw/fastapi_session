import grpc
from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,

)

from app.settings import Settings


def setup_telemetry_metrics(settings: Settings) -> None:
    compression = {
        "gzip": grpc.Compression.Gzip,
        "deflate": grpc.Compression.Deflate,
        "none": grpc.Compression.NoCompression,
    }[settings.API.COMPRESSION]

    metric_exporter = OTLPMetricExporter(
        endpoint=settings.OTLP.ENDPOINT,
        insecure=settings.OTLP.INSECURE,
        compression=compression,
    )
    metric_readers = [
        PeriodicExportingMetricReader(
            exporter=metric_exporter,
            export_interval_millis=settings.OTLP.EXPORT_INTERVAL_MILLIS,
            export_timeout_millis=settings.OTLP.EXPORT_TIMEOUT_MILLIS,
        )
    ]
    if settings.API.METRICS_CONSOLE:
        metric_readers.append(
            PeriodicExportingMetricReader(
                exporter=ConsoleMetricExporter(),
                export_interval_millis=settings.OTLP.EXPORT_INTERVAL_MILLIS,
                export_timeout_millis=settings.OTLP.EXPORT_TIMEOUT_MILLIS,
            )
        )
    metrics_provider = MeterProvider(metric_readers=metric_readers)
    metrics.set_meter_provider(metrics_provider)
