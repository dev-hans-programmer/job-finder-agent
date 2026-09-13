from collections import Counter

from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from prometheus_client import Counter as PrometheusCounter

_metrics: Counter[str] = Counter()
_http_requests = PrometheusCounter(
    "jobradar_http_requests_total",
    "Total HTTP requests handled by the API",
    ("method", "route", "status"),
)
_http_errors = PrometheusCounter(
    "jobradar_http_errors_total",
    "Total HTTP 5xx responses returned by the API",
    ("method", "route", "status"),
)


def increment(name: str, value: int = 1) -> None:
    _metrics[name] += value


def snapshot() -> dict[str, int]:
    return dict(_metrics)


def prometheus() -> str:
    custom = "\n".join(f"jobradar_{key} {value}" for key, value in sorted(_metrics.items()))
    return custom + ("\n" if custom else "") + generate_latest().decode()


def prometheus_content_type() -> str:
    return CONTENT_TYPE_LATEST


def record_http_request(method: str, route: str, status: int) -> None:
    labels = (method, route, str(status))
    _http_requests.labels(*labels).inc()
    if status >= 500:
        _http_errors.labels(*labels).inc()
