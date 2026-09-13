Load testing
Why we need it
Load testing verifies how the system behaves under realistic traffic before deployment. It helps identify capacity limits, slow endpoints, database bottlenecks, Redis contention, worker saturation, and failure behavior.
What it solves
It will help us measure:
- Requests per second the API can handle
- Response latency at normal and peak traffic
- PostgreSQL connection and query pressure
- Redis performance under concurrency
- Rate-limit behavior under load
- API process CPU and memory usage
- Worker throughput and queue growth
- Error rates during traffic spikes
- Safe operating limits for staging and production
Problems without it
Without load testing:
- Performance issues may only appear in production
- Database pools may become exhausted
- Requests may time out unexpectedly
- Celery queues may grow without detection
- Rate limits may be incorrectly configured
- Infrastructure may be over- or under-provisioned
- Deployments may pass functional tests but fail under concurrency
Proposed implementation
I’ll add:
- A load-testing tool, preferably Locust
- Scenarios for health, authentication, preferences, sources, jobs, and ingestion runs
- Configurable users, spawn rate, duration, and target URL
- Separate staging/local load-test configuration
- Authentication token setup for protected endpoints
- Results in terminal and HTML/CSV formats
- Docker/Makefile commands
- Prometheus-compatible performance visibility
- Performance thresholds for latency, throughput, and error rate
- Unit tests for load-test configuration/helpers
- Detailed QA steps for running and interpreting results
This will not modify business behavior or database schema. It will add testing infrastructure and performance documentation.
