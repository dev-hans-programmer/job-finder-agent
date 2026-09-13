Why OpenTelemetry instrumentation?
Currently, the application has:
- Request IDs
- Basic structured logging
- Basic metrics
- Error handling
But it cannot show the complete lifecycle of one operation across processes.
For example:
POST /sources/{id}/run
    ↓
API process
    ↓
Celery task
    ↓
Redis
    ↓
Worker
    ↓
Greenhouse API
    ↓
PostgreSQL
Without distributed tracing, these appear as unrelated log messages.
OpenTelemetry gives every operation a trace ID and span hierarchy so we can see the complete request flow.
What it solves
Request debugging
We could answer:
- How long did the API request take?
- How long did the Celery task wait?
- How long did Greenhouse take to respond?
- How long did PostgreSQL take?
- Which step failed?
Example trace:
POST /sources/{id}/run                 42ms
├── authenticate JWT                    2ms
├── insert ingestion_run                8ms
└── dispatch Celery task               12ms

job_radar.ingestion                    4.8s
├── load source                         5ms
├── Greenhouse HTTP request           2.1s
├── normalize 120 jobs                1.4s
└── PostgreSQL upserts                1.2s
Cross-process visibility
The API, scheduler, worker, and Celery task are separate processes.
OpenTelemetry propagates trace context between services and processes, allowing us to connect:
API trace → Celery task trace → database/provider spans
Provider performance
We can identify:
- Slow Greenhouse requests
- Slow Lever requests
- HTTP 429 responses
- HTTP 5xx failures
- Timeout frequency
- Provider-specific latency
Database performance
Instrumentation can expose:
- Slow SQL queries
- Query duration
- Connection pool behavior
- Transaction timing
- Database errors
Error investigation
Instead of searching logs manually, a trace will show:
Trace ID: abc123
Status: ERROR
Error: Greenhouse returned HTTP 404
Location: GreenhouseAdapter.fetch()
Vendor-neutral observability
OpenTelemetry is an open standard. Traces can later be exported to:
- Tempo
- Jaeger
- Datadog
- New Relic
- Honeycomb
- Elastic
- Any OTLP-compatible backend
This fits well with the later Prometheus/Grafana/Loki/Tempo item.
What happens without it?
Without OpenTelemetry:
- API and worker failures are difficult to correlate.
- A request ID may stop at the API boundary.
- Celery tasks appear disconnected from originating requests.
- Slow database queries are hard to identify.
- Provider latency is not consistently measurable.
- Debugging requires manually combining logs from multiple containers.
- Future dashboards have less useful data.
- Performance regressions may go unnoticed.
What this spec implements
1. OpenTelemetry configuration
Add settings such as:
OTEL_ENABLED=true
OTEL_SERVICE_NAME=job-radar-agent
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces
OTEL_SAMPLE_RATE=1.0
Production would use a lower sampling rate, for example:
OTEL_TRACES_SAMPLE_RATE=0.1
2. FastAPI instrumentation
Automatically instrument:
- HTTP requests
- Response status codes
- Request duration
- Exceptions
- Route names
3. PostgreSQL instrumentation
Instrument SQLAlchemy operations to capture:
- Query duration
- Database system
- Transaction spans
- Connection information
- SQL errors
Sensitive values should not be recorded.
4. Redis instrumentation
Instrument:
- Redis command duration
- Celery broker interactions
- Redis errors
- Queue operations
5. External HTTP instrumentation
Instrument httpx requests to Greenhouse and Lever:
HTTP method
URL host
status code
duration
retry count
exception
Request bodies, credentials, and sensitive query values must be excluded.
6. Manual business spans
Add explicit spans around important operations:
ingestion.start_run
ingestion.fetch_provider_jobs
ingestion.normalize_jobs
ingestion.persist_jobs
matching.evaluate
notification.deliver
These spans provide business context that automatic framework instrumentation cannot infer.
7. Celery task instrumentation
Instrument:
- Task received
- Task started
- Task retried
- Task succeeded
- Task failed
- Task duration
The existing Celery task trace should be linked to the originating API or scheduler trace where possible.
8. Export strategy
The implementation configures:
- Console exporter for local development when no collector is configured.
- OTLP exporter when OTEL_ENABLED=true and an endpoint is provided.
- No telemetry exporter when disabled.
Grafana, Tempo, Loki, and Prometheus dashboards are intentionally deferred to item 6.
9. Privacy and security
Instrumentation must not capture:
- Passwords
- JWTs
- Refresh tokens
- Database passwords
- Provider credentials
- Full job descriptions
- User personal data unnecessarily
Only IDs, operation names, statuses, and timing data should be attached as attributes.
10. Tests
Tests would cover:
- Telemetry disabled behavior
- Telemetry enabled behavior
- FastAPI spans
- Database spans
- Redis spans
- Provider HTTP spans
- Celery task spans
- Trace context propagation
- Exception recording
- Sampling configuration
- Sensitive-data redaction
- Application startup/shutdown
The goal would remain:
100% statement coverage
100% branch coverage
Tradeoffs
Benefits:
- Much faster debugging
- Cross-process visibility
- Standard telemetry format
- Provider and database performance insight
- Ready for Tempo/Grafana later
- Easier production incident analysis
Costs:
- Additional dependencies
- Small runtime overhead
- More configuration
- Telemetry storage costs later
- Risk of accidentally recording sensitive data
- Celery context propagation requires deliberate implementation
