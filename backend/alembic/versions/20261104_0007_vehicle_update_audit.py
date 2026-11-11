"""Track vehicle update actor and timestamp for UC-CV-08."""
from alembic import op
import sqlalchemy as sa


revision = "20261104_0007"
down_revision = "20261029_0006"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "vehicles",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.add_column("vehicles", sa.Column("updated_by_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_vehicles_updated_by_id_users",
        "vehicles",
        "users",
        ["updated_by_id"],
        ["id"],
    )


def downgrade():
    raise NotImplementedError("No downgrade automático para proteger la trazabilidad de vehículos.")
