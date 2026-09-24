"""add preventivo_km_intervalo to site_config

Revision ID: 003
Revises: 002
Create Date: 2026-09-23
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("site_config")}
    if "preventivo_km_intervalo" not in cols:
        op.add_column(
            "site_config",
            sa.Column(
                "preventivo_km_intervalo",
                sa.Integer(),
                nullable=False,
                server_default="5000",
            ),
        )


def downgrade() -> None:
    op.drop_column("site_config", "preventivo_km_intervalo")
