# Plan

1. Define a Redis queue boundary for ingestion identifiers.
2. Move API ingestion dispatch from FastAPI `BackgroundTasks` to queue publishing.
3. Add worker and scheduler process entrypoints with resource lifecycle management.
4. Add scheduler polling for due enabled sources.
5. Add Docker Compose services and Makefile commands.
6. Add unit tests for queue, worker, scheduler, shutdown, and API enqueue behavior.
7. Verify lint, coverage, and Compose configuration.
