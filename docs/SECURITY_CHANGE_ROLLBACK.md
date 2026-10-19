# GreenUpPCB Security Changes: Recovery and Rollback Plan

## Current verified state

- Git branch: development
- Baseline commit before the current uncommitted changes: 6f1842b
- Backend service: greenuppcb-backend.service
- Application database: greenupcb_lis
- Test database: greenupcb_test
- Backend test suite: 29 passed in the latest recorded run
- Frontend production build: passed in the latest recorded run
- Password-reset cleanup timer: greenuppcb-token-cleanup.timer
- Database credentials were rotated and the new connection was verified.
- The cleanup service was run once and reported zero deleted tokens.

Re-run tests and health checks before making a release decision.

## Important credential rule

Never restore
backend/.env.before_db_password_rotation_20261019_164752
as the active environment file. It contains the old database credential,
which was rotated. Keep the file restricted and do not commit it.

If database authentication fails, do not copy old credentials back into
the application. Generate a new database credential through an authorized
PostgreSQL administrator, update backend/.env with restrictive permissions,
verify a connection to greenupcb_lis, and then restart the backend.

Never print credentials to the terminal or store them in Git.

## If automated token cleanup has a problem

Disable the schedule first:

    sudo systemctl disable --now greenuppcb-token-cleanup.timer

Inspect the service logs:

    sudo journalctl -u greenuppcb-token-cleanup.service --no-pager -n 100

Do not run the cleanup script with --execute manually until the failure
is understood and the database target has been verified.

Cleanup deletes expired or sufficiently old used password-reset tokens.
Those deleted token rows are not automatically recoverable. This job must
not delete users, sessions, PCB records, or unrelated database data.

## If the backend fails after a code change

1. Check service state and recent logs.
2. Verify the configured database URL without displaying its value.
3. Verify database connectivity before restarting the service.
4. Prefer a reviewed forward-fix if possible.
5. If code rollback is necessary, review the exact affected files and
   restore a known-good version selectively. Re-run the complete backend
   tests and frontend build before restarting the service.

Do not use git reset --hard or git clean -fd as a general recovery method.
Do not blindly restore database.py from a pre-change backup: those versions
may reintroduce a hard-coded database credential fallback.
Do not stage or commit *.env* files, private keys, or local backup files.

## Before release

- Review all intended source and test changes.
- Confirm git diff --check is clean.
- Confirm the full backend test suite passes against greenupcb_test.
- Confirm the frontend production build passes.
- Confirm backend and cleanup timer status.
- Confirm reset-token URL removal in a real browser.
- Review Git history findings and coordinate any history rewrite with
  repository collaborators before force-pushing.
- Verify Microsoft Graph sender authorization and real email delivery
  with the responsible IT team before enabling production email delivery.
