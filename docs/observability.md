Application
  ├── OpenTelemetry SDK → traces
  ├── Prometheus client → metrics
  └── structured logs → log records

OpenTelemetry Collector
  └── sends traces to Tempo

Prometheus
  └── stores metrics

Loki
  └── stores logs

Tempo
  └── stores traces

Grafana
  └── visualizes Prometheus, Loki, and Tempo data


  Component	Purpose
OpenTelemetry	Produces and sends traces
Tempo	Stores traces
Prometheus	Stores metrics
Loki	Stores logs
Grafana	Displays and correlates everything
Collector	Receives, buffers, and forwards telemetry


You can run a minimal setup with only OpenTelemetry + Tempo, but then you only get traces.
For production-grade observability, use:
OpenTelemetry + Collector + Tempo
Prometheus
Loki
Grafana
Grafana is the place where you will see dashboards, logs, metrics, and traces together.


9:13 PM








differenece between traces and metrics







9:13 PM






Metrics and traces answer different questions.
	Metrics	Traces
Purpose	Show system health and trends	Show one request’s complete journey
Data type	Aggregated numbers	Detailed span timeline
Example	95% of requests complete under 500ms	This request spent 2s calling Greenhouse
Scope	Many requests/tasks	One request/task
Storage	Prometheus	Tempo
Best for	Dashboards, alerts, capacity planning	Debugging, bottleneck analysis, request correlation


Metrics
Metrics are numeric measurements collected over time:
API requests: 10,000
Error rate: 2.4%
Average latency: 180 ms
Celery queue size: 42
Database connections: 18
They help answer:
- Is the system healthy?
- Are errors increasing?
- Is the API becoming slower?
- Do we need more workers?
- Should an alert fire?
Example Prometheus metric:
http_requests_total{route="/health/live",status="200"} 1520
Traces
A trace follows one operation through the system:
POST /sources/{id}/run
├── authenticate user: 4 ms
├── insert ingestion run: 12 ms
├── dispatch Celery task: 8 ms
└── worker ingestion task: 4.2 s
    ├── Greenhouse request: 2.1 s
    ├── normalize jobs: 900 ms
    └── save jobs: 1.2 s
Traces help answer:
- Why was this request slow?
- Which database query failed?
- Did the provider respond slowly?
- Did the Celery task retry?
- Where exactly did the error happen?
Simple analogy
Metrics are like a hospital dashboard:
Average heart rate
Number of patients
Number of emergencies
Traces are like the medical history of one patient:
Admission → diagnosis → treatment → recovery
You generally need both:
Metrics detect the problem.
Traces explain the problem.
Logs provide additional context.
