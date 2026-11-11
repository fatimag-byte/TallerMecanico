"""Allow workshop photo data URLs without truncation."""
from alembic import op
from sqlalchemy.dialects import mysql

revision = "20261029_0006"
down_revision = "20261029_0005"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "workshops",
        "photo_url",
        existing_type=mysql.VARCHAR(length=255),
        type_=mysql.LONGTEXT(),
        existing_nullable=True,
    )


def downgrade():
    raise NotImplementedError("No downgrade automático para proteger fotografías existentes.")
