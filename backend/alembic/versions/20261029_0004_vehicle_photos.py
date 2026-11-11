"""Persist vehicle photos in MySQL."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "20261029_0004"
down_revision = "20261014_0003"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "vehicle_photos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("vehicle_id", sa.Integer, sa.ForeignKey("vehicles.id"), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=40), nullable=False),
        sa.Column("content", mysql.MEDIUMBLOB, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
    )
    op.create_index("ix_vehicle_photos_vehicle", "vehicle_photos", ["vehicle_id"])

def downgrade():
    raise NotImplementedError("No downgrade automático para proteger datos.")
