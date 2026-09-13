from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from opentelemetry.sdk.trace import TracerProvider

from app.observability import telemetry


def enabled_settings(endpoint: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        otel_enabled=True,
        otel_service_name="test-service",
        app_env="test",
        otel_sample_rate=0.5,
        otel_exporter_otlp_endpoint=endpoint,
    )


def test_configure_telemetry_is_disabled() -> None:
    telemetry._configured = False
    assert telemetry.configure_telemetry(SimpleNamespace(otel_enabled=False)) is None


def test_configure_telemetry_uses_otlp_exporter() -> None:
    telemetry._configured = False
    provider = MagicMock()
    with (
        patch.object(telemetry, "TracerProvider", return_value=provider),
        patch.object(telemetry, "OTLPSpanExporter") as exporter,
        patch.object(telemetry, "BatchSpanProcessor") as processor,
        patch.object(telemetry.trace, "set_tracer_provider") as set_provider,
    ):
        result = telemetry.configure_telemetry(enabled_settings("http://collector/v1/traces"))

    assert result is provider
    exporter.assert_called_once_with(endpoint="http://collector/v1/traces")
    processor.assert_called_once_with(exporter.return_value)
    provider.add_span_processor.assert_called_once_with(processor.return_value)
    set_provider.assert_called_once_with(provider)
    telemetry._configured = False


def test_configure_telemetry_uses_console_exporter() -> None:
    telemetry._configured = False
    provider = MagicMock()
    with (
        patch.object(telemetry, "TracerProvider", return_value=provider),
        patch.object(telemetry, "ConsoleSpanExporter") as exporter,
        patch.object(telemetry, "BatchSpanProcessor") as processor,
        patch.object(telemetry.trace, "set_tracer_provider"),
    ):
        result = telemetry.configure_telemetry(enabled_settings())

    assert result is provider
    exporter.assert_called_once_with()
    processor.assert_called_once_with(exporter.return_value)
    telemetry._configured = False


def test_configure_telemetry_returns_existing_provider() -> None:
    telemetry._configured = True
    provider = TracerProvider()
    with patch.object(telemetry.trace, "get_tracer_provider", return_value=provider):
        assert telemetry.configure_telemetry(enabled_settings()) is provider
    telemetry._configured = False


def test_instrumentation_helpers_are_noops_when_disabled() -> None:
    settings = SimpleNamespace(otel_enabled=False)
    with (
        patch.object(telemetry.FastAPIInstrumentor, "instrument_app") as app_instrument,
        patch.object(telemetry.SQLAlchemyInstrumentor, "instrument") as engine_instrument,
    ):
        telemetry.instrument_app(object(), settings)
        telemetry.instrument_engine(object(), settings)
    telemetry.instrument_clients(settings)
    app_instrument.assert_not_called()
    engine_instrument.assert_not_called()


def test_instrument_app_and_engine_when_enabled() -> None:
    settings = enabled_settings()
    app = object()
    sync_engine = object()
    engine = SimpleNamespace(sync_engine=sync_engine)
    with (
        patch.object(telemetry.FastAPIInstrumentor, "instrument_app") as app_instrument,
        patch.object(telemetry, "SQLAlchemyInstrumentor") as instrumentor,
    ):
        telemetry.instrument_app(app, settings)
        telemetry.instrument_engine(engine, settings)

    app_instrument.assert_called_once_with(app)
    instrumentor.return_value.instrument.assert_called_once_with(engine=sync_engine)


def test_instrument_clients_instruments_each_client_once() -> None:
    telemetry._instrumented_redis = False
    telemetry._instrumented_httpx = False
    telemetry._instrumented_celery = False
    with (
        patch.object(telemetry, "RedisInstrumentor") as redis,
        patch.object(telemetry, "HTTPXClientInstrumentor") as httpx,
        patch.object(telemetry, "CeleryInstrumentor") as celery,
    ):
        telemetry.instrument_clients(enabled_settings())
        telemetry.instrument_clients(enabled_settings())

    redis.return_value.instrument.assert_called_once_with()
    httpx.return_value.instrument.assert_called_once_with()
    celery.return_value.instrument.assert_called_once_with()
    telemetry._instrumented_redis = False
    telemetry._instrumented_httpx = False
    telemetry._instrumented_celery = False
