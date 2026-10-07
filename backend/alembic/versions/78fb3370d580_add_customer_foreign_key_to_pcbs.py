"""add customer foreign key to pcbs

Revision ID: 78fb3370d580
Revises: b04f12b30146
Create Date: 2026-10-07 13:06:45.886256

"""
from typing import Sequence, Union

from alembic import op


revision: str = "78fb3370d580"
down_revision: Union[str, Sequence[str], None] = "b04f12b30146"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_pcbs_customer_id_customers",
        "pcbs",
        "customers",
        ["customer_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_pcbs_customer_id_customers",
        "pcbs",
        type_="foreignkey",
    )
