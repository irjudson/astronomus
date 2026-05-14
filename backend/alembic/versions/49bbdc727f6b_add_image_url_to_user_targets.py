"""add_image_url_to_user_targets

Revision ID: 49bbdc727f6b
Revises: 94a8c9331841
Create Date: 2026-05-14 18:44:26.420046

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '49bbdc727f6b'
down_revision: Union[str, Sequence[str], None] = '94a8c9331841'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_targets', sa.Column('image_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('user_targets', 'image_url')
