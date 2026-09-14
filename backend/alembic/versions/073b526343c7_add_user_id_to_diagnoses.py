"""add user id to diagnoses

Revision ID: 073b526343c7
Revises: 76d49811dc22
Create Date: 2026-09-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "073b526343c7"
down_revision: Union[str, Sequence[str], None] = "76d49811dc22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "diagnoses",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )

    op.create_foreign_key(
        "diagnoses_user_id_fkey",
        "diagnoses",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_index(
        "ix_diagnoses_user_id",
        "diagnoses",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_diagnoses_user_id", table_name="diagnoses")
    op.drop_constraint(
        "diagnoses_user_id_fkey",
        "diagnoses",
        type_="foreignkey",
    )
    op.drop_column("diagnoses", "user_id")
