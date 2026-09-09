# QA — Notification Delivery

## Prerequisites

Complete Spec 005. Configure Telegram sandbox credentials and a test email mailbox, or use the provider mocks documented for local testing.

## Test data

Use a match with score 97, title `Senior Backend Engineer`, company `XYZ`, Mumbai/hybrid, 8+ years, salary `45–55 LPA`, matched Python/PostgreSQL/AWS/FinTech, missing FastAPI, and a valid application URL.

## Test 1: Telegram notification

Create/enqueue a notification for the match. Expected: one delivered message containing score, title, company, location, work mode, salary, matched criteria, missing criteria, and application link.

## Test 2: Email notification

Send through the email adapter. Expected: readable subject/body, the same required content, valid link, and a persisted provider message/delivery ID where available.

## Test 3: Idempotency

Trigger the same match/channel three times. Expected: one provider delivery and one successful delivery row; later attempts are suppressed or return the existing delivery.

## Test 4: Retry and permanent failure

Force a timeout/429 and then recovery. Expected: bounded retries and eventual success. Force invalid credentials. Expected: permanent failure is recorded without an endless retry loop.

## Test 5: Quiet hours

Configure quiet hours around the current test time. Expected: delivery is deferred or suppressed according to configuration, with the reason visible in delivery state.

## Completion expectation

Notifications are useful, complete, duplicate-free, observable, and isolated from provider failures.
