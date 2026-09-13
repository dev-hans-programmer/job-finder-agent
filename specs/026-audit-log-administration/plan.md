# Plan: Audit log administration

1. Add repository query primitives for composable filters, pagination, counts,
   and retention deletion.
2. Add an audit service boundary so routes do not access repositories directly.
3. Add an admin dependency using the existing configurable role guard.
4. Add versioned search and export routes using the standard response envelope.
5. Add a CLI-style retention operation that optionally writes JSONL archives.
6. Add unit and API tests for filters, pagination, authorization wiring, both
   export formats, empty exports, and archive/delete behavior.
7. Verify formatting, lint, branch coverage, migrations, and manual QA.

No migration is expected because this feature consumes the existing audit
event schema.
