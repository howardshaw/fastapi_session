import grpc
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes
from prometheus_client import Counter, Histogram

from app.logger.logger import get_logger
from app.settings import Settings

logger = get_logger(__name__)

# 指标定义
TASK_LATENCY = Histogram(
    'task_latency_seconds',
    'Task latency in seconds',
    ['service_name', 'task_name']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'path', 'status']
)

OPERATION_COUNT = Counter(
    'operation_total',
    'Number of operations',
    ['service_name', 'operation_type', 'status']
)


def setup_telemetry_tracing(settings: Settings) -> None:
    """设置 OpenTelemetry"""
    try:
        # 设置 TracerProvider
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: settings.API_SERVICE_NAME,
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: settings.ENVIRONMENT,
        })

        tracer_provider = TracerProvider(resource=resource)

        # 配置 OTLP 导出器
        compression = {
            "gzip": grpc.Compression.Gzip,
            "deflate": grpc.Compression.Deflate,
            "none": grpc.Compression.NoCompression,
        }[settings.COMPRESSION]
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.OTLP_ENDPOINT,
            insecure=settings.OTLP_INSECURE,
            compression=compression,
        )

        tracer_provider.add_span_processor(
            BatchSpanProcessor(
                span_exporter=otlp_exporter,
                max_queue_size=settings.MAX_QUEUE_SIZE,
                max_export_batch_size=settings.MAX_EXPORT_BATCH_SIZE,
                schedule_delay_millis=settings.SCHEDULE_DELAY_MILLIS,
                export_timeout_millis=settings.EXPORT_TIMEOUT_MILLIS,
            )
        )
        trace.set_tracer_provider(tracer_provider)
        SystemMetricsInstrumentor().instrument()
        logger.info(f"Telemetry setup completed for service: {settings.API_SERVICE_NAME}")

    except Exception as e:
        logger.error(f"Failed to setup telemetry: {e}")
        raise


def init_fastapi_instrumentation(app: FastAPI):
    """初始化 FastAPI 插装"""
    try:

        # 配置 FastAPI 插装
        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="metrics",
        )

        logger.info("FastAPI instrumentation initialized")
    except Exception as e:
        logger.error(f"Failed to initialize FastAPI instrumentation: {e}")
        raise


def init_celery_instrumentation(service_name: str):
    """初始化 Celery 插装"""
    try:
        # 首先设置 tracer provider
        setup_telemetry_tracing(service_name)

        # 然后进行 Celery 插装
        CeleryInstrumentor().instrument()
        logger.info("Celery instrumentation initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Celery instrumentation: {e}")
        raise


def instrument_sqlalchemny() -> None:
    try:
        # third party
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument(enable_commenter=True, commenter_options={})
        logger.info("Added OTEL SQLAlchemyInstrumentor")
    except Exception as e:
        logger.error(f"Failed to load SQLAlchemyInstrumentor. {e}")


def instrument_threads() -> None:
    try:
        # third party
        from opentelemetry.instrumentation.threading import ThreadingInstrumentor

        ThreadingInstrumentor().instrument()
        logger.info("Added OTEL ThreadingInstrumentor")
    except Exception as e:
        logger.error(f"Failed to load ThreadingInstrumentor. {e}")


def shutdown_telemetry() -> None:
    # https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/protocol/exporter.md#retry
    # https://github.com/open-telemetry/opentelemetry-python/issues/3309
    # If the exporters have not been able to connect to the collector
    # then it will be stuck in a loop during shutdown for at least 30 seconds
    # before it finally gets killed.
    metrics.get_meter_provider().shutdown(timeout_millis=1000)  # type: ignore
    trace.get_tracer_provider().shutdown()  # type: ignore
