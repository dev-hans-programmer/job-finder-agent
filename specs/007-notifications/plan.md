# Implementation plan

1. Define notification message and provider contracts.
2. Add delivery table and migration.
3. Implement template renderer and channel formatting.
4. Implement Telegram and email providers with provider-specific error classification.
5. Implement notification service using transactional intent creation and Redis delivery locks.
6. Add retry worker boundary and delivery status queries.
7. Add provider fixtures, integration tests, and coverage gate.
