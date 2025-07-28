"""added session_id

Revision ID: 9f8d934b6501
Revises:
Create Date: 2025-07-26 14:36:15.415477
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f8d934b6501"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Add session_id as nullable first
    op.add_column(
        "chat_messages", sa.Column("session_id", sa.String(length=36), nullable=True)
    )

    # 2. Backfill existing rows with a known session_id (MUST exist in chat_sessions)
    # ❗ Replace with a real session ID if needed
    op.execute("UPDATE chat_messages SET session_id = 'dummy-session-id'")

    # 3. Make it NOT NULL
    op.alter_column("chat_messages", "session_id", nullable=False)

    # 4. Safely drop old FK only if it exists — or skip this if uncertain
    # Remove this line unless you are 100% sure the old constraint exists:
    # op.drop_constraint(op.f("chat_messages_chat_id_fkey"), "chat_messages", type_="foreignkey")

    # 5. Create new foreign key for session_id
    op.create_foreign_key(
        "fk_chat_messages_session_id",  # Give it a clear name
        "chat_messages",
        "chat_sessions",
        ["session_id"],
        ["session_id"],
        ondelete="CASCADE",
    )

    # 6. Drop old columns safely
    # Use try/except or ensure they're present before dropping
    op.drop_column("chat_messages", "active_pdf_type")
    op.drop_column("chat_messages", "chat_id")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "chat_messages",
        sa.Column("chat_id", sa.String(length=36), nullable=False),
    )
    op.add_column(
        "chat_messages",
        sa.Column("active_pdf_type", sa.String(length=50), nullable=False),
    )
    op.drop_constraint(
        "fk_chat_messages_session_id", "chat_messages", type_="foreignkey"
    )
    op.drop_column("chat_messages", "session_id")
