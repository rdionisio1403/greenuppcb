"""add customer owner user foreign key

Revision ID: 91c4e7a2b6f1
Revises: 78fb3370d580
Create Date: 2026-10-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "91c4e7a2b6f1"
down_revision: Union[str, Sequence[str], None] = "78fb3370d580"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
    )

    op.create_index(
        "ix_customers_created_by_user_id",
        "customers",
        ["created_by_user_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_customers_created_by_user_id_users",
        "customers",
        "users",
        ["created_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_customers_created_by_user_id_users",
        "customers",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_customers_created_by_user_id",
        table_name="customers",
    )

    op.drop_column("customers", "created_by_user_id")
