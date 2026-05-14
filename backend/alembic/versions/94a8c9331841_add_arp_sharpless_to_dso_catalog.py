"""add_arp_sharpless_to_dso_catalog

Revision ID: 94a8c9331841
Revises: 1eb59f1772f1
Create Date: 2026-05-14 18:36:45.415462

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94a8c9331841'
down_revision: Union[str, Sequence[str], None] = '1eb59f1772f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("dso_catalog", sa.Column("arp_number", sa.Integer(), nullable=True))
    op.add_column("dso_catalog", sa.Column("sharpless_number", sa.Integer(), nullable=True))
    op.create_index("ix_dso_catalog_arp_number", "dso_catalog", ["arp_number"])
    op.create_index("ix_dso_catalog_sharpless_number", "dso_catalog", ["sharpless_number"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_dso_catalog_sharpless_number", table_name="dso_catalog")
    op.drop_index("ix_dso_catalog_arp_number", table_name="dso_catalog")
    op.drop_column("dso_catalog", "sharpless_number")
    op.drop_column("dso_catalog", "arp_number")
