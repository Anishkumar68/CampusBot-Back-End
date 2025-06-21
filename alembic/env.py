import sys
import os

# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models import Base

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("chat_messages", sa.Column("timestamp", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("chat_messages", "timestamp")


target_metadata = Base.metadata
