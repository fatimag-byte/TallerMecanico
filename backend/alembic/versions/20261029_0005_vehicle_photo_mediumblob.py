"""Allow vehicle photos up to 15 MB."""
from alembic import op
from sqlalchemy.dialects import mysql

revision = "20261029_0005"
down_revision = "20261029_0004"
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column("vehicle_photos", "content", existing_type=mysql.BLOB, type_=mysql.MEDIUMBLOB, existing_nullable=False)

def downgrade():
    raise NotImplementedError("No downgrade automático para proteger datos.")
