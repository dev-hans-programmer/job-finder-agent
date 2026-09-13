# Implementation plan

1. Add Prometheus-compatible request metrics while preserving the existing metric helpers.
2. Add structured HTTP request logging with request ID, route, status, and duration.
3. Add Compose services for Prometheus, Grafana, Loki, Tempo, Alloy, and the OpenTelemetry Collector.
4. Add configuration files for scraping, trace export, log shipping, datasource provisioning, and dashboards.
5. Configure Compose application processes to export traces to the collector.
6. Add Makefile targets, README documentation, and a manual end-to-end QA guide.
7. Add tests for metric output and request success/error recording, then run the full quality gate.
