"""Command-line interface for one-shot backup operations."""

import sys
from pathlib import Path

from app.backup.service import backup_once, restore_backup, verify_backup
from app.config import get_settings


def main() -> None:  # pragma: no cover
    settings = get_settings()
    operation = sys.argv[1] if len(sys.argv) > 1 else "backup"
    if operation == "backup":
        print(backup_once(settings).dump_path)
    elif operation == "verify" and len(sys.argv) > 2:
        print(verify_backup(Path(sys.argv[2]), settings.database_url))
    elif operation == "restore" and len(sys.argv) > 2:
        restore_backup(Path(sys.argv[2]), settings.database_url)
    else:
        raise SystemExit("Usage: backup | verify BACKUP | restore BACKUP")


if __name__ == "__main__":  # pragma: no cover
    main()
