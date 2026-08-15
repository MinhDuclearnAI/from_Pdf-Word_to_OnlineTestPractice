"""Add image_url to questions

Revision ID: add_image_url_to_questions
Revises: update_componenttype_enum
Create Date: 2026-08-14 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_image_url_to_questions'
down_revision = 'update_componenttype_enum'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Thêm cột image_url vào bảng questions
    op.add_column('questions', sa.Column('image_url', sa.String(), nullable=True))


def downgrade() -> None:
    # Xóa cột image_url khỏi bảng questions
    op.drop_column('questions', 'image_url')
