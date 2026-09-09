# Spec 007 — Notification Delivery

## Objective

Deliver eligible match results through Telegram and email with idempotency, retries, quiet hours, and provider isolation.

## Scope

Implement notification intents, templates, provider protocol, Telegram and email adapters, delivery persistence, retry classification, quiet hours, and delivery status API/service. WhatsApp remains a feature-flagged adapter boundary only.

## Acceptance criteria

- Only `notify` decisions above threshold create delivery intents.
- Reprocessing a match never sends the same channel/job/profile notification twice.
- Templates contain score, title, company, location/work mode, matched/missing criteria, concerns, and application URL.
- Provider timeout/429/5xx retries; permanent errors stop retrying and are visible.
- Quiet hours suppress or defer delivery according to configuration.
- Unit, provider contract, PostgreSQL/Redis integration, and API tests achieve 100% branch coverage.

## Required tests

Template rendering; idempotency key; quiet-hours boundaries and timezone; Telegram/email success; retryable/permanent failures; duplicate delivery race; persisted status and retry count.
