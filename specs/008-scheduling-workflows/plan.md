# Implementation plan

1. Define workflow command/result types and stage boundaries.
2. Implement scheduler with source locks and timezone-safe intervals.
3. Implement ingestion-to-normalization-to-matching orchestration.
4. Add notification enqueue stage and bounded retries/dead letter.
5. Add manual run endpoint integration and recovery behavior.
6. Add full-stack fixture workflow tests using Docker services.

Start with APScheduler; keep worker functions serializable so Celery/RQ can replace the execution layer later.
