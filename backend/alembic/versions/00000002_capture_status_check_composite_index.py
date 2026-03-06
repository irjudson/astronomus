"""capture status CHECK constraint and catalog composite index

Revision ID: 00000002
Revises: 00000001_init
Create Date: 2026-03-06

- Adds CHECK constraint on capture_history.status to enforce canonical values.
- Adds composite index on dso_catalog(object_type, magnitude, id) for the
  common filter+sort query pattern used by CatalogService.filter_targets().
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "00000002"
down_revision: Union[str, Sequence[str], None] = "00000001_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Canonical status values (must stay in sync with CaptureStatus enum)
_VALID_STATUSES = ("complete", "needs_more", "needs_more_data")
_CHECK_EXPR = "status IS NULL OR status IN ('complete', 'needs_more', 'needs_more_data')"


def upgrade() -> None:
    # --- capture_history.status CHECK constraint ---
    op.create_check_constraint(
        "ck_capture_history_status",
        "capture_history",
        _CHECK_EXPR,
    )

    # --- composite index for CatalogService.filter_targets() ---
    # Covers: WHERE object_type IN (...) AND magnitude <= ? ORDER BY magnitude, id
    op.create_index(
        "ix_dso_catalog_type_mag_id",
        "dso_catalog",
        ["object_type", "magnitude", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_dso_catalog_type_mag_id", table_name="dso_catalog")
    op.drop_constraint("ck_capture_history_status", "capture_history", type_="check")
