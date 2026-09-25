"""add audit logs table

Revision ID: 7c1f4a9b2e6d
Revises: 942dc7dd5ab5
Create Date: 2026-09-25
"""

from alembic import op
import sqlalchemy as sa


revision = "7c1f4a9b2e6d"
down_revision = "942dc7dd5ab5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_audit_logs_id", "audit_logs", ["id"], unique=False)
    op.create_index(
        "ix_audit_logs_user_id",
        "audit_logs",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_event_type",
        "audit_logs",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_created_at",
        "audit_logs",
        ["created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_event_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_id", table_name="audit_logs")
    op.drop_table("audit_logs")
