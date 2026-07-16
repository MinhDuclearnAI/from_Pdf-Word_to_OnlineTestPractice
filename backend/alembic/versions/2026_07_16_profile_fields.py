"""add user profile fields

Revision ID: 2026_07_16_profile_fields
Revises: 2026_7_14_235-0a55b92111a2
Create Date: 2026-07-16 10:28:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2026_07_16_profile_fields'
down_revision = '0a55b92111a2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('date_of_birth', sa.Date(), nullable=True))
    op.add_column('users', sa.Column('school', sa.String(), nullable=True))
    op.add_column('users', sa.Column('workplace', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'workplace')
    op.drop_column('users', 'school')
    op.drop_column('users', 'date_of_birth')
