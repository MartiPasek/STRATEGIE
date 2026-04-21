"""add sms_outbox table

Revision ID: f3a2b1c8d7e9
Revises: c9e5d7f1a8b3
Create Date: 2026-04-21

SMS outbox -- write-only z aplikace, poll-read Android gateway.

Lifecycle:
  pending   -> queue_sms() zapsal, ceka na telefon
  sent      -> telefon potvrdil odeslani (POST /gateway/outbox/{id}/sent)
  failed    -> telefon reportoval chybu, nebo rate-limit v app

purpose = user_request | notification | system
  - user_request -- AI tool `send_sms` na zadost usera
  - notification -- automaticka (offline notif. apod.)
  - system       -- alerting / audit / bezpecnost

to_phone: E.164 format (+420777180511), normalizovano v sms_service.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f3a2b1c8d7e9"
down_revision = "c9e5d7f1a8b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sms_outbox",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=True),
        sa.Column("to_phone", sa.String(length=20), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("purpose", sa.String(length=30), nullable=False, server_default="user_request"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Hot path: GET /gateway/outbox -- filtruje WHERE status='pending'.
    op.create_index(
        "ix_sms_outbox_status_created",
        "sms_outbox",
        ["status", "created_at"],
    )

    # Audit + rate limiting: count SMS per user per time window.
    op.create_index(
        "ix_sms_outbox_user_created",
        "sms_outbox",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_sms_outbox_user_created", table_name="sms_outbox")
    op.drop_index("ix_sms_outbox_status_created", table_name="sms_outbox")
    op.drop_table("sms_outbox")
