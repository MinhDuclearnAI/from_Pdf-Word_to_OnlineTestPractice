"""Add IELTS component types to ENUM

Revision ID: update_componenttype_enum
Revises: e51aec460817
Create Date: 2026-08-13 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'update_componenttype_enum'
down_revision = 'e51aec460817'
branch_labels = None
depends_on = None

NEW_ENUMS = [
    "true_false_not_given",
    "matching_headings",
    "matching_features",
    "sentence_completion",
    "summary_completion",
    "table_completion",
    "diagram_label_completion",
    "multiple_choice_ielts"
]

def upgrade() -> None:
    # Trong PostgreSQL, lệnh ALTER TYPE ADD VALUE không thể chạy trong một transaction
    # Alembic tự động bọc script trong 1 transaction (BEGIN ... COMMIT).
    # Do đó chúng ta cần commit transaction hiện tại, chạy ALTER TYPE, rồi bắt đầu transaction mới.
    op.execute("COMMIT")
    for new_val in NEW_ENUMS:
        # PostgreSQL 10+ hỗ trợ IF NOT EXISTS
        op.execute(f"ALTER TYPE componenttype ADD VALUE IF NOT EXISTS '{new_val}'")
    op.execute("BEGIN")

def downgrade() -> None:
    # Không thể dễ dàng DROP VALUE trong PostgreSQL ENUM
    pass
