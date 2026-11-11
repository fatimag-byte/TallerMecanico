"""Add optional normalized address fields to customers without altering existing records."""
from alembic import op
import sqlalchemy as sa

revision = "20261014_0003"
down_revision = "20261014_0002"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("customers", sa.Column("neighborhood", sa.String(length=150), nullable=True))
    op.add_column("customers", sa.Column("postal_code", sa.String(length=5), nullable=True))

def downgrade():
    raise NotImplementedError("No downgrade automático para proteger datos.")
