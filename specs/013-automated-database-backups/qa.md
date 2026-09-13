# QA Guide

## Prerequisites

```bash
make services-up
make migrate
make app-up
```

The backup process writes to `./backups` on the host. In Compose it runs at the configured interval, defaulting to once per day.

## Manual backup

```bash
make backup
ls -l backups
```

Expected: matching `.dump`, `.sha256`, and `.json` files. The dump is outside the PostgreSQL data volume.

## Verification

```bash
make backup-verify BACKUP=backups/jobradar-YYYYMMDDTHHMMSSZ.dump
```

Expected: a 64-character SHA-256 digest. Modify the dump or checksum sidecar and repeat; verification must fail.

## Restore test

Restore only to a disposable PostgreSQL database:

```bash
make restore BACKUP=backups/jobradar-YYYYMMDDTHHMMSSZ.dump
make migrate
```

Expected: `pg_restore` completes without error and representative application tables/data can be queried.

## Retention and monitoring

Set `BACKUP_RETENTION_DAYS=0` only in a disposable test directory, run `make backup`, and verify expired artifacts are removed. Inspect the process with:

```bash
docker compose logs -f backup
docker compose ps backup
```

Expected: successful backup paths are logged without passwords; the backup container remains running.
