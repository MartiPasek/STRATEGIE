"""add sms_inbox and phone_calls tables

Revision ID: a4b5c6d7e8f9
Revises: f3a2b1c8d7e9
Create Date: 2026-04-21

Inbound SMS + call log od Android telefonu (capcom6 webhook + Tasker push).

sms_inbox:
  telefon po prijeti SMS POSTne na /api/v1/sms/gateway/inbox -> ulozi.
  persona_id = komu to prislo (dnes Marti-AI, budoucnost multi-persona).
  from_phone: E.164.

phone_calls:
  telefon (Tasker profily) pushuje zaznamy o hovorech:
    in      -> prichozi hovor prijat
    out     -> odchozi hovor uskutecnen
    missed  -> prichozi hovor nezvednut
  duration_s je NULL pro missed.
  persona_id = "majitel" telefonu (Marti-AI).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a4b5c6d7e8f9"
down_revision = "f3a2b1c8d7e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── sms_inbox ──────────────────────────────────────────────────────────
    op.create_table(
        "sms_inbox",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("persona_id", sa.BigInteger(), nullable=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=True),
        sa.Column("from_phone", sa.String(length=20), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        # Audit timestamp kdy to pushlo do nasi DB (muze se lisit od received_at
        # pokud telefon byl offline a bufferoval).
        sa.Column("stored_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        # Volitelne raw metadata z gateway (SIM slot, delivery reports, ...)
        sa.Column("meta", sa.Text(), nullable=True),
    )

    # Hot path: tool `list_sms_inbox` filtruje unread_only.
    op.create_index(
        "ix_sms_inbox_persona_received",
        "sms_inbox",
        ["persona_id", "received_at"],
    )
    op.create_index(
        "ix_sms_inbox_persona_read_received",
        "sms_inbox",
        ["persona_id", "read_at", "received_at"],
    )

    # ── phone_calls ────────────────────────────────────────────────────────
    op.create_table(
        "phone_calls",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("persona_id", sa.BigInteger(), nullable=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=True),
        sa.Column("peer_phone", sa.String(length=20), nullable=False),
        sa.Column("direction", sa.String(length=10), nullable=False),   # in | out | missed
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_s", sa.Integer(), nullable=True),           # NULL pro missed
        sa.Column("seen_at", sa.DateTime(timezone=True), nullable=True),  # kdy to user videl
        sa.Column("stored_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("meta", sa.Text(), nullable=True),
    )

    op.create_index(
        "ix_phone_calls_persona_started",
        "phone_calls",
        ["persona_id", "started_at"],
    )
    op.create_index(
        "ix_phone_calls_direction_started",
        "phone_calls",
        ["direction", "started_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_phone_calls_direction_started", table_name="phone_calls")
    op.drop_index("ix_phone_calls_persona_started", table_name="phone_calls")
    op.drop_table("phone_calls")

    op.drop_index("ix_sms_inbox_persona_read_received", table_name="sms_inbox")
    op.drop_index("ix_sms_inbox_persona_received", table_name="sms_inbox")
    op.drop_table("sms_inbox")
