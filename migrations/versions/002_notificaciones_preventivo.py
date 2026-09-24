"""notificaciones y service preventivo

Revision ID: 002
Revises: 001
Create Date: 2026-09-22
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def cols(table):
        return {c["name"] for c in inspector.get_columns(table)}

    if "telegram_chat_id" not in cols("clients"):
        op.add_column("clients", sa.Column("telegram_chat_id", sa.String(50), nullable=True))

    if "proximo_service_km" not in cols("motorcycles"):
        op.add_column("motorcycles", sa.Column("proximo_service_km", sa.Integer(), nullable=True))
    if "proximo_service_fecha" not in cols("motorcycles"):
        op.add_column("motorcycles", sa.Column("proximo_service_fecha", sa.Date(), nullable=True))

    site_cols = cols("site_config")
    if "notif_email_auto" not in site_cols:
        op.add_column("site_config", sa.Column("notif_email_auto", sa.Boolean(), nullable=False, server_default=sa.true()))
    if "notif_telegram_auto" not in site_cols:
        op.add_column("site_config", sa.Column("notif_telegram_auto", sa.Boolean(), nullable=False, server_default=sa.true()))
    if "preventivo_dias_anticipacion" not in site_cols:
        op.add_column("site_config", sa.Column("preventivo_dias_anticipacion", sa.Integer(), nullable=False, server_default="7"))
    if "preventivo_km_anticipacion" not in site_cols:
        op.add_column("site_config", sa.Column("preventivo_km_anticipacion", sa.Integer(), nullable=False, server_default="500"))

    if not inspector.has_table("notifications"):
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("canal", sa.String(20), nullable=False),
            sa.Column("estado", sa.String(20), nullable=False),
            sa.Column("asunto", sa.String(200), nullable=True),
            sa.Column("mensaje", sa.Text(), nullable=True),
            sa.Column("destinatario", sa.String(100), nullable=True),
            sa.Column("error", sa.Text(), nullable=True),
            sa.Column("referencia", sa.String(150), nullable=True),
            sa.Column("service_order_id", sa.Integer(), sa.ForeignKey("service_orders.id", ondelete="SET NULL"), nullable=True),
            sa.Column("motorcycle_id", sa.Integer(), sa.ForeignKey("motorcycles.id", ondelete="SET NULL"), nullable=True),
            sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_notifications_id", "notifications", ["id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_column("site_config", "preventivo_km_anticipacion")
    op.drop_column("site_config", "preventivo_dias_anticipacion")
    op.drop_column("site_config", "notif_telegram_auto")
    op.drop_column("site_config", "notif_email_auto")
    op.drop_column("motorcycles", "proximo_service_fecha")
    op.drop_column("motorcycles", "proximo_service_km")
    op.drop_column("clients", "telegram_chat_id")
