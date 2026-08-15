"""create llm_models table

Revision ID: 281c633b97ed
Revises: 641c6dd3c83f
Create Date: 2026-08-14 20:27:35.334508

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '281c633b97ed'
down_revision: Union[str, Sequence[str], None] = '641c6dd3c83f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'llm_models',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('label', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('llm_models')
