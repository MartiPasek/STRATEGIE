"""add email_outbox table

Revision ID: d8b2c3d4e5f6
Revises: d7a1b2c3e4f5
Create Date: 2026-04-22

Email outbox -- asynchronni send pres EWS.
Nahrada primeho synchronniho send_email_or_raise u volani z AI toolu
(konzistence s SMS, audit trail, retry). Invites + password reset zustavaji
na primem send (kriticka cesta, nechceme cekat na worker).

Lifecycle:
  pending   -> queue_email() zapsal, ceka na worker
  sent      -> worker odeslal pres EWS (sent_at NOT NULL)
  failed    -> EWS odmitl (last_error obsahuje detail, attempts++)

purpose = user_request | notification | system
  user_request -- AI tool send_email na zadost usera (email jmenem persony)
  notification -- automaticke notify (napr. "Task hotov", reply k prichozim)
  system       -- system alerty (narazime pri dalsim PR)

persona_id je FK-free reference na persony -- worker ho pouzije pro vyber
EWS credentials (persona_channels). NULL = global EWS (fallback na .env,
pouziva se u systemovych emailu z doby pred persona_channels).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d8b2c3d4e5f6"
down_revision = "d7a1b2c3e4f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_outbox",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=True),
        sa.Column("persona_id", sa.BigInteger(), nullable=True),
        sa.Column("to_email", sa.String(length=320), nullable=False),
        sa.Column("cc", sa.Text(), nullable=True),    # JSON array emailu
        sa.Column("bcc", sa.Text(), nullable=True),   # JSON array emailu
        sa.Column("subject", sa.String(length=998), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("purpose", sa.String(length=30), nullable=False,
                  server_default="user_request"),
        sa.Column("status", sa.String(length=20), nullable=False,
                  server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        # Vazba na conversation_id zpravy, kde to vzniklo -- pro audit, pozdeji
        # pro trace v UI "zobraz email v puvodnim chatu".
        sa.Column("conversation_id", sa.BigInteger(), nullable=True),
        # Identity, pod kterou se maile odesila: "persona" | "user" | "system".
        # Korespondence se send_email_or_raise.from_identity.
        sa.Column("from_identity", sa.String(length=20), nullable=False,
                  server_default="persona"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Hot path workera: WHERE status='pending' ORDER BY created_at.
    op.create_index(
        "ix_email_outbox_status_created",
        "email_outbox",
        ["status", "created_at"],
    )

    # Audit + rate limiting (per-user historia).
    op.create_index(
        "ix_email_outbox_user_created",
        "email_outbox",
        ["user_id", "created_at"],
    )

    # Per-persona zobrazeni v UI (tab 'Odeslane' filtruje podle personu).
    op.create_index(
        "ix_email_outbox_persona_created",
        "email_outbox",
        ["persona_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_email_outbox_persona_created", table_name="email_outbox")
    op.drop_index("ix_email_outbox_user_created", table_name="email_outbox")
    op.drop_index("ix_email_outbox_status_created", table_name="email_outbox")
    op.drop_table("email_outbox")
