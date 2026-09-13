# QA — Observability stack

## 1. Start the stack

From the repository root:

```bash
make services-up
make migrate
make app-up
```

Expected: API, worker, scheduler, Flower, Prometheus, Grafana, Loki, Tempo, Alloy, and the OpenTelemetry Collector start.

## 2. Verify health endpoints

```bash
curl http://localhost:8000/health/live
curl http://localhost:9090/-/ready
curl http://localhost:3100/ready
curl http://localhost:3200/ready
```

Expected: each endpoint responds successfully. The API uses port `8000` inside Compose; a locally run API uses port `8005`.

## 3. Verify Prometheus metrics

```bash
curl http://localhost:8000/metrics
```

Expected: the response has Prometheus exposition text containing metrics such as:

```text
jobradar_http_requests_total
jobradar_http_errors_total
```

Open `http://localhost:9090/targets` and confirm `job-radar-api` is `UP`.

## 4. Verify Grafana

1. Open `http://localhost:3000`.
2. Sign in with `admin` / `admin`.
3. Open Dashboards → Job Radar → Job Radar Overview.
4. Confirm the API scrape health and request panels are present.

Expected: Prometheus, Loki, and Tempo are already configured as datasources; no manual datasource creation is needed.

## 5. Generate and inspect telemetry

```bash
curl -i http://localhost:8000/health/live
curl -i http://localhost:8000/health/ready
docker compose logs api --tail=20
```

In Grafana:

- Use the dashboard for request rate and 5xx metrics.
- Use Explore → Loki and query `{job="job-radar"}`.
- Use Explore → Tempo and search service `job-radar-api`.

Expected: the request appears in logs and produces a trace in Tempo. Logs include route, status, duration, and request ID. Traces include the HTTP server span and any database/provider child spans.

## 6. Verify worker tracing

Configure a real source and run it using the normal source/run API flow. Then inspect:

- Flower at `http://localhost:5555` for task execution.
- Grafana → Explore → Tempo for the ingestion trace.
- Grafana → Explore → Loki for worker logs.

Expected: the worker task, provider request, and database operations are observable and use the worker service name.

## 7. Failure-path verification

Stop the API container:

```bash
docker compose stop api
```

Check Prometheus targets and Grafana.

Expected: the API target becomes `DOWN`, the dashboard reflects the loss, and existing stored telemetry remains queryable. Restart with `docker compose start api`.

## Sign-off

- [ ] All services start successfully.
- [ ] Prometheus target is `UP`.
- [ ] Grafana dashboard is provisioned.
- [ ] Logs are searchable in Loki.
- [ ] Traces are searchable in Tempo.
- [ ] Worker task telemetry is visible.
- [ ] API failure state is reflected in Prometheus/Grafana.
