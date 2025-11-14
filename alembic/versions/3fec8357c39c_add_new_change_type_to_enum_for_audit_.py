"""add new change type to enum for audit logs

Revision ID: 3fec8357c39c
Revises: 5ddbdfeccfe4
Create Date: 2025-11-14 02:09:28.227687

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3fec8357c39c'
down_revision: Union[str, Sequence[str], None] = '5ddbdfeccfe4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new value to ChangeType enum
    op.execute("ALTER TYPE changetype ADD VALUE IF NOT EXISTS 'BULK_UPDATE'")


def downgrade() -> None:
    """Downgrade schema."""
    # Note: PostgreSQL does not support removing enum values directly.
    # You would need to recreate the enum type without the value,
    # which requires dropping and recreating the column.
    # For simplicity, we leave this as a no-op.
    pass
