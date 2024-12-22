import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from temporalio.client import Client
from temporalio.contrib.opentelemetry import TracingInterceptor
from temporalio.runtime import OpenTelemetryConfig, Runtime, TelemetryConfig
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


def init_runtime_with_telemetry(otlp_endpoint: str) -> Runtime:
    # Setup global tracer for workflow traces
    provider = TracerProvider(resource=Resource.create({SERVICE_NAME: "workflow-service"}))
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # Setup SDK metrics to OTel endpoint
    return Runtime(
        telemetry=TelemetryConfig(
            metrics=OpenTelemetryConfig(url=otlp_endpoint)
        )
    )


class TemporalClientFactory:
    """Factory for creating Temporal Client instances"""

    @staticmethod
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def create(url: str, otlp_endpoint: str) -> Client:
        """
        Create and configure a Temporal Client instance
        
        Returns:
            Client: Configured Temporal Client instance
        """
        logger.info(f"Connecting to temporal: {url}")
        if otlp_endpoint:
            runtime = init_runtime_with_telemetry(otlp_endpoint)

            client = await Client.connect(
                url,
                # Use OpenTelemetry interceptor
                interceptors=[TracingInterceptor()],
                runtime=runtime,
            )
        else:
            client = await Client.connect(url)

        logger.info("Successfully connected to Temporal")
        return client
