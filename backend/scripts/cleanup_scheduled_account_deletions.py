import argparse
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.database import DATABASE_URL, SessionLocal, engine
from app.services.account_deletion import (
    cleanup_scheduled_account_deletions,
    count_due_accounts,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report or execute scheduled GreenUpPCB account deletions."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Delete accounts whose 30-day grace period has elapsed.",
    )
    parser.add_argument(
        "--confirm-database",
        help="Required with --execute; must match the connected database name.",
    )
    args = parser.parse_args()

    if args.execute and not args.confirm_database:
        parser.error("--confirm-database is required with --execute")

    configured_name = make_url(DATABASE_URL).database

    try:
        with engine.connect() as connection:
            actual_name = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()
    except Exception:
        print("ERROR: Could not verify connected database.", file=sys.stderr)
        return 2

    if actual_name != configured_name:
        print("ERROR: Connected database does not match DATABASE_URL.", file=sys.stderr)
        return 2

    if args.execute and args.confirm_database != actual_name:
        print("ERROR: Database confirmation does not match.", file=sys.stderr)
        return 2

    with SessionLocal() as db:
        due_count = count_due_accounts(db)

        if not args.execute:
            print(f"DRY RUN - database: {actual_name}")
            print(f"Accounts past the 30-day grace period: {due_count}")
            print("No records were deleted.")
            return 0

        deleted, protected = cleanup_scheduled_account_deletions(db)
        print(f"Database: {actual_name}")
        print(f"Accounts deleted: {deleted}")
        print(f"Accounts protected by last-admin rule: {protected}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
