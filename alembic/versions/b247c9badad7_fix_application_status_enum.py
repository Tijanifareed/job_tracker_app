"""fix application status enum

Revision ID: b247c9badad7
Revises: 716093b52340
Create Date: 2025-08-25 21:57:36.385241
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b247c9badad7'
down_revision: Union[str, Sequence[str], None] = '716093b52340'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum type
    application_status_enum = sa.Enum(
        'applied', 'interview', 'offer', 'rejected',
        name='applicationstatus'
    )
    application_status_enum.create(op.get_bind())

    # Add the column using that enum
    op.add_column(
        'applications',
        sa.Column('status', application_status_enum, nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the column first
    op.drop_column('applications', 'status')

    # Then drop the enum type
    sa.Enum(name='applicationstatus').drop(op.get_bind())
