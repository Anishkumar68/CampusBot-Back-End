"""add timestamp to chatmessage"""

from alembic import op
import sqlalchemy as sa

# These MUST be defined
"""create account table

Revision ID: 1975ea83b712
Revises:
Create Date: 2011-11-08 11:40:27.089406

"""

# revision identifiers, used by Alembic.
revision = "1975ea83b712"
down_revision = None
branch_labels = None


def upgrade():
    op.add_column("chat_messages", sa.Column("timestamp", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("chat_messages", "timestamp")
