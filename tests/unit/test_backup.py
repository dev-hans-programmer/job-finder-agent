import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import app.backup.cli
import app.processes.backup
from app.backup.service import backup_once, cleanup_backups, restore_backup, verify_backup


def settings(path: Path):
    return SimpleNamespace(
        backup_dir=str(path),
        backup_retention_days=7,
        database_url="postgresql+asyncpg://jobradar:secret@localhost:5432/jobradar",
    )


def runner_factory():
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        if command[0] == "pg_dump":
            Path(command[command.index("--file") + 1]).write_bytes(b"backup-data")

    return runner, calls


def test_backup_creates_dump_checksum_and_metadata(tmp_path):
    runner, calls = runner_factory()
    result = backup_once(settings(tmp_path), datetime(2026, 1, 1, tzinfo=timezone.utc), runner)
    assert result.dump_path.read_bytes() == b"backup-data"
    assert result.checksum_path.exists() and result.metadata_path.exists()
    assert len(calls) == 2
    assert calls[0][1]["env"]["PGPASSWORD"] == "secret"
    assert "secret" not in " ".join(calls[0][0])


def test_verify_restore_and_cleanup(tmp_path):
    dump = tmp_path / "jobradar-old.dump"
    dump.write_bytes(b"backup-data")
    runner = MagicMock()
    digest = verify_backup(dump, "postgresql://jobradar@localhost/jobradar", runner)
    assert len(digest) == 64
    dump.with_suffix(".sha256").write_text(f"{digest}  {dump.name}\n")
    assert verify_backup(dump, "postgresql://jobradar@localhost/jobradar", runner) == digest
    dump.with_suffix(".sha256").write_text("bad  old.dump\n")
    with pytest.raises(ValueError, match="checksum"):
        verify_backup(dump, "postgresql://jobradar@localhost/jobradar", runner)
    restore_backup(dump, "postgresql://jobradar@localhost/jobradar", runner)
    assert runner.call_count == 4

    old = tmp_path / "expired.dump"
    old.write_bytes(b"old")
    old.with_suffix(".sha256").write_text("checksum")
    old.with_suffix(".json").write_text("metadata")
    old_time = (datetime.now(timezone.utc) - timedelta(days=10)).timestamp()
    os.utime(old, (old_time, old_time))
    current = tmp_path / "current.dump"
    current.write_bytes(b"current")
    assert cleanup_backups(tmp_path, 7) == 1
    assert not old.exists() and current.exists()


def test_backup_rejects_missing_or_empty_dumps(tmp_path):
    missing = tmp_path / "missing.dump"
    with pytest.raises(ValueError):
        verify_backup(missing, "postgresql://localhost/jobradar", MagicMock())
    empty = tmp_path / "empty.dump"
    empty.touch()
    with pytest.raises(ValueError):
        restore_backup(empty, "postgresql://localhost/jobradar", MagicMock())


def test_backup_process_module_exposes_entrypoint():
    assert callable(app.processes.backup.main)
    assert callable(app.backup.cli.main)
