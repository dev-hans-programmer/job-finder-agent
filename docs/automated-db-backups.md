Why automated database backups?
Currently, backups are manual:
docker compose exec postgres pg_dump ...
That is risky because backups may be:
- Forgotten
- Incomplete
- Stored on the same disk as PostgreSQL
- Impossible to restore
- Too old when an incident occurs
- Missing during accidental deletion or migration failure
A backup is useful only if it is automated, retained, monitored, and regularly restored successfully.
What it solves
Automated backups protect against:
- Accidental data deletion
- Bad migrations
- Application bugs modifying data
- PostgreSQL corruption
- Disk failure
- Lost Docker volumes
- Failed deployments
- User or job data recovery requirements
- Disaster recovery scenarios
The backup flow will be:
Scheduler
   ↓
pg_dump PostgreSQL
   ↓
Compressed backup
   ↓
Checksum
   ↓
Backup storage
   ↓
Retention cleanup
What happens without it?
Without automated backups:
- A deleted database may be permanently lost.
- A broken migration may require manual reconstruction.
- Recovery depends on someone remembering to run pg_dump.
- You may discover that backups were failing only after needing them.
- Backups may exist but be unreadable or incomplete.
- There is no reliable recovery point objective.
What I will implement
1. Automated PostgreSQL backup command
Add a production-safe backup utility that:
- Runs pg_dump
- Uses the custom PostgreSQL format
- Compresses the backup
- Generates a checksum
- Writes metadata
- Uses timestamped filenames
- Does not expose passwords in process arguments or logs
Example:
backups/jobradar-2026-09-13T020000Z.dump
backups/jobradar-2026-09-13T020000Z.sha256
backups/jobradar-2026-09-13T020000Z.json
2. Configurable retention
Add settings such as:
BACKUP_DIR=./backups
BACKUP_RETENTION_DAYS=7
BACKUP_INTERVAL_SECONDS=86400
The backup process will delete only expired backup files from the configured backup directory.
3. Dedicated backup process
Add a separate process:
app/processes/backup.py
It will:
- Run on a configurable interval
- Create backups
- Perform cleanup
- Log success/failure
- Shut down gracefully
This process will be independent from:
- API
- Worker
- Scheduler
- Celery
4. Docker Compose backup service
Add a service such as:
backup
It will mount a dedicated backup volume:
./backups:/backups
This is suitable for local development and testing.
For production, the backup directory should point to durable external storage such as:
- S3
- S3-compatible object storage
- Cloud provider backup storage
- Managed PostgreSQL backups
A local Docker volume alone is not sufficient for disaster recovery if the machine is lost.
5. Restore command
Add a documented restore flow:
make restore BACKUP=backups/jobradar-....dump
The restore process will:
1. Stop or isolate application processes.
2. Restore into a disposable database.
3. Apply validation queries.
4. Confirm expected tables and row counts.
5. Report success or failure.
6. Backup verification
Each backup will be validated by:
- Checking the command exit code
- Checking that the file exists
- Checking that the file is not empty
- Verifying the SHA-256 checksum
- Running pg_restore --list
- Testing restoration in a disposable PostgreSQL database
7. Makefile commands
Add commands such as:
make backup
make backup-list
make backup-verify
make restore BACKUP=...
make backup-process
8. Tests
Tests will cover:
- Backup filename generation
- Retention cleanup
- Invalid backup directories
- Failed pg_dump
- Empty or invalid backup files
- Checksum generation
- Checksum mismatch
- Restore validation
- Backup process shutdown
- Configuration validation
Integration testing will use a disposable PostgreSQL database.
Important production note
A backup written to the same server as PostgreSQL does not protect against server loss.
The implementation will provide local backups first, but the production recommendation will be:
PostgreSQL
   ↓
Encrypted backup
   ↓
External object storage
   ↓
Retention policy
   ↓
Regular restore verification


# verify
Backups are stored locally at:
./backups/
Example:
backups/jobradar-20260913T020000Z.dump
backups/jobradar-20260913T020000Z.sha256
backups/jobradar-20260913T020000Z.json
The backup is not stored inside PostgreSQL’s data volume.
Run everything
make services-up
make migrate
make app-up
The backup container immediately creates one backup, then runs again according to:
BACKUP_INTERVAL_SECONDS=86400
Check backup logs:
docker compose logs -f backup
Check generated files:
ls -lh backups
Create a manual backup
make backup
This runs through the backup container, so pg_dump does not need to be installed on your Mac.
Verify a backup
LATEST_BACKUP=$(ls -t backups/*.dump | head -1)

make backup-verify BACKUP="$LATEST_BACKUP"
Expected: a 64-character SHA-256 digest.
Restore a backup
Restore only into a disposable or explicitly approved database:
make restore BACKUP="$LATEST_BACKUP"
Configuration
BACKUP_DIR=./backups
BACKUP_RETENTION_DAYS=7
BACKUP_INTERVAL_SECONDS=86400
Production backups should eventually be copied to external storage such as S3. The current implementation stores them on the host-mounted ./backups directory.
