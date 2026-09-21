"""add server side sessions table

Revision ID: 355a9e95fe86
Revises: 073b526343c7
Create Date: 2026-09-21 13:43:33.621949

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "355a9e95fe86"
down_revision: Union[str, Sequence[str], None] = "073b526343c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create server-side sessions table."""
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "last_activity",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )

    op.create_index(
        "ix_sessions_id",
        "sessions",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_sessions_session_id",
        "sessions",
        ["session_id"],
        unique=True,
    )
    op.create_index(
        "ix_sessions_user_id",
        "sessions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_sessions_user_id_expires_at",
        "sessions",
        ["user_id", "expires_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop server-side sessions table."""
    op.drop_index(
        "ix_sessions_user_id_expires_at",
        table_name="sessions",
    )
    op.drop_index(
        "ix_sessions_user_id",
        table_name="sessions",
    )
    op.drop_index(
        "ix_sessions_session_id",
        table_name="sessions",
    )
    op.drop_index(
        "ix_sessions_id",
        table_name="sessions",
    )
    op.drop_table("sessions")
