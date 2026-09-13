"""Celery worker process entrypoint."""

import subprocess


def main() -> None:  # pragma: no cover
    subprocess.run(
        ["celery", "-A", "app.workers.celery_app", "worker", "--loglevel=INFO"], check=True
    )


if __name__ == "__main__":  # pragma: no cover
    main()
