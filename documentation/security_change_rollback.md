# Security Change Recovery Checklist

This document provides general guidance for recovering from security-related
changes. Environment-specific operational details must remain outside this
public repository.

## Before Releasing Changes

- Review all intended source and test changes.
- Keep environment files, credentials, tokens, private keys, and local
  backups out of version control.
- Run the backend tests and frontend production build.
- Verify application health and the password-reset flow in an authorized
  test environment.
- Verify that password-hash migration tests accept existing bcrypt hashes
  and validate newly generated Argon2id hashes before release.
- Verify SMTP configuration using an authorized test mailbox and inspect
  service logs/provider status to confirm delivery. Password-reset email
  sending runs as an in-process FastAPI background task, not a durable queue;
  pending work may be interrupted if the process restarts before execution.

## If the Backend Fails After a Change

1. Check service status and authorized logs. Do not publish sensitive log
   output.
2. Verify database connectivity without printing connection strings.
3. Prefer a reviewed fix. If rollback is necessary, restore only the
   affected files to a known-good revision.
4. Run the applicable tests and frontend build before releasing the change.

Do not use destructive Git commands as a general recovery method. Never
restore old environment files or backups containing credentials. Do not
commit environment files, secrets, private keys, or local backups.

## Scheduled Cleanup Tasks

If a scheduled cleanup task fails, follow the approved operational procedure
to disable it. Review the logs, confirm the correct environment and database
target, and understand the cause before rerunning the task.

Verify the cleanup scope before execution. Do not run cleanup manually
against a production environment without authorization.
