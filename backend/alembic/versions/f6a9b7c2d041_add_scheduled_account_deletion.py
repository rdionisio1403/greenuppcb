"""Add scheduled account deletion timestamp."""

from alembic import op
import sqlalchemy as sa

revision = "f6a9b7c2d041"
down_revision = "91c4e7a2b6f1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("deletion_requested_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_users_deletion_requested_at",
        "users",
        ["deletion_requested_at"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_users_deletion_requested_at", table_name="users")
    op.drop_column("users", "deletion_requested_at")
