"""make user email nullable

Revision ID: b04f12b30146
Revises: 7c1f4a9b2e6d
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b04f12b30146"
down_revision: Union[str, Sequence[str], None] = "7c1f4a9b2e6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(length=200),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(length=200),
        nullable=False,
    )
