# Local observability stack

The repository includes a local observability stack for metrics, logs, and traces:

```text
API / worker / scheduler
  ├── Prometheus metrics → Prometheus
  ├── stdout logs → Alloy → Loki
  └── OpenTelemetry traces → Collector → Tempo

Prometheus + Loki + Tempo → Grafana
```

Start it with:

```bash
make services-up
make migrate
make app-up
```

Open Grafana at `http://localhost:3000` using `admin` / `admin`. The `Job Radar Overview` dashboard is provisioned automatically. It includes API scrape health, request rate, 5xx rate, and application logs.

The API exposes Prometheus-compatible metrics at `/metrics`. Docker Compose enables telemetry for the API, worker, scheduler, and Flower and points them to the collector at `http://otel-collector:4318/v1/traces`.

For local development without Compose, keep `OTEL_EXPORTER_OTLP_ENDPOINT` empty to print spans in the terminal. For Compose, use the collector endpoint configured by the service environment. Grafana, Prometheus, Loki, Tempo, and collector data are stored in named Docker volumes.

This stack is local-first. Before production use, add authentication, resource limits, retention policies, external durable storage, TLS, and alert routing.
