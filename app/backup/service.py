"""Safe, testable PostgreSQL backup operations."""

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from sqlalchemy.engine import make_url


@dataclass(frozen=True)
class BackupResult:
    dump_path: Path
    checksum_path: Path
    metadata_path: Path


def _database_options(database_url: str) -> tuple[list[str], dict[str, str]]:
    url = make_url(database_url)
    options = ["--host", url.host or "localhost", "--username", url.username or ""]
    if url.port is not None:
        options.extend(["--port", str(url.port)])
    environment = os.environ.copy()
    if url.password is not None:
        environment["PGPASSWORD"] = url.password
    return options, environment


def _run(command_runner: Callable, command: list[str], environment: dict[str, str]) -> None:
    command_runner(command, check=True, env=environment, capture_output=True)


def backup_once(
    settings, now: datetime | None = None, command_runner=subprocess.run
) -> BackupResult:
    timestamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    backup_dir = Path(settings.backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    stem = f"jobradar-{timestamp.strftime('%Y%m%dT%H%M%SZ')}"
    dump_path = backup_dir / f"{stem}.dump"
    temporary_path = backup_dir / f"{stem}.dump.tmp"
    checksum_path = backup_dir / f"{stem}.sha256"
    metadata_path = backup_dir / f"{stem}.json"
    options, environment = _database_options(settings.database_url)
    url = make_url(settings.database_url)
    _run(
        command_runner,
        ["pg_dump", "--format=custom", "--file", str(temporary_path), *options, url.database or ""],
        environment,
    )
    _run(command_runner, ["pg_restore", "--list", str(temporary_path)], environment)
    temporary_path.replace(dump_path)
    digest = hashlib.sha256(dump_path.read_bytes()).hexdigest()
    checksum_path.write_text(f"{digest}  {dump_path.name}\n")
    metadata_path.write_text(
        json.dumps(
            {
                "created_at": timestamp.isoformat(),
                "database": url.database,
                "format": "custom",
                "sha256": digest,
                "size_bytes": dump_path.stat().st_size,
            },
            indent=2,
        )
        + "\n"
    )
    cleanup_backups(backup_dir, settings.backup_retention_days, timestamp)
    return BackupResult(dump_path, checksum_path, metadata_path)


def cleanup_backups(backup_dir: Path, retention_days: int, now: datetime | None = None) -> int:
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=retention_days)
    removed = 0
    for dump_path in backup_dir.glob("*.dump"):
        modified = datetime.fromtimestamp(dump_path.stat().st_mtime, timezone.utc)
        if modified < cutoff:
            for path in (
                dump_path,
                dump_path.with_suffix(".sha256"),
                dump_path.with_suffix(".json"),
            ):
                path.unlink(missing_ok=True)
            removed += 1
    return removed


def verify_backup(dump_path: Path, database_url: str, command_runner=subprocess.run) -> str:
    if not dump_path.is_file() or dump_path.stat().st_size == 0:
        raise ValueError("backup dump is missing or empty")
    options, environment = _database_options(database_url)
    _run(command_runner, ["pg_restore", "--list", str(dump_path)], environment)
    digest = hashlib.sha256(dump_path.read_bytes()).hexdigest()
    checksum_path = dump_path.with_suffix(".sha256")
    if checksum_path.exists():
        expected = checksum_path.read_text().split()[0]
        if expected != digest:
            raise ValueError("backup checksum mismatch")
    return digest


def restore_backup(dump_path: Path, database_url: str, command_runner=subprocess.run) -> None:
    if not dump_path.is_file() or dump_path.stat().st_size == 0:
        raise ValueError("backup dump is missing or empty")
    options, environment = _database_options(database_url)
    url = make_url(database_url)
    _run(
        command_runner,
        [
            "pg_restore",
            "--exit-on-error",
            "--no-owner",
            *options,
            "--dbname",
            url.database or "",
            str(dump_path),
        ],
        environment,
    )
