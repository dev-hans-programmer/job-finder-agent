# Plan

1. Add Celery and Flower dependencies.
2. Configure a JSON-only Celery application using Redis broker/result backend.
3. Add thin task adapters that call the existing ingestion service.
4. Replace API and scheduler dispatch with Celery task dispatch.
5. Configure worker acknowledgement, retries, backoff, and task tracking.
6. Add Flower and Makefile monitoring commands.
7. Remove the obsolete custom Redis list queue.
8. Add task, dispatch, retry, and monitoring configuration tests.
