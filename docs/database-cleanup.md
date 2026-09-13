# Local database cleanup

The default local database can be cleared with:

```bash
make db-clean CONFIRM=YES
```

The command targets only the default Docker Compose `postgres` service and database `jobradar`. It truncates application tables with `CASCADE` while preserving the schema and `alembic_version` migration history.

The confirmation flag is required to prevent accidental deletion:

```bash
make db-clean
```

will refuse to run. Never use this command against staging or production.
