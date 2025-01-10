import logging

from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

from app.settings import Settings


def setup_telemetry_logging(settings: Settings) -> None:
    otlp_exporter = OTLPLogExporter(
        endpoint=settings.OTLP.ENDPOINT,
        insecure=settings.OTLP.INSECURE,
    )

    logger_provider = LoggerProvider()
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_exporter))

    logging_handler = LoggingHandler(
        logger_provider=logger_provider,
        level=settings.LOG.LEVEL,
    )
    logging.getLogger().addHandler(logging_handler)

    # 添加到全局 logging 配置
    logging.basicConfig(level=settings.LOG.LEVEL, handlers=[logging_handler])

