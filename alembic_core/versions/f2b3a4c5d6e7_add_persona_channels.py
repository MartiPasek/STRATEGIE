"""add persona_channels table

Revision ID: f2b3a4c5d6e7
Revises: e1a2b3c4d5f6
Create Date: 2026-04-21

Persona_channels = komunikacni kanal prislusny personu (telefon, email,
v budoucnu Slack/Teams).

Per-tenant: persona muze mit ruzny kanal pro kazdy tenant (Marti-AI za
eurosoft = jedno cislo, Marti-AI za tisax = jine). NULL tenant_id = globalni
fallback ("bezme tenantu").

Kredentialy pro email:
  credentials_encrypted = Fernet(ENCRYPTION_KEY) sifrovane heslo
  server = URL EWS serveru
Kredentialy pro phone:
  credentials_encrypted i server = NULL (SIM ziva v telefonu, my nemame
  zadnou password)

Data migrace (Marti-AI z .env -> persona_channels) se resi zvlast pres
scripts/_migrate_ews_to_persona_channels.py (idempotentni, musi se spustit
rucne s naplnenym .env).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f2b3a4c5d6e7"
down_revision = "e1a2b3c4d5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "persona_channels",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("persona_id", sa.BigInteger(),
                  sa.ForeignKey("personas.id", ondelete="CASCADE"),
                  nullable=False),
        # Tenant_id NULL = globalni kanal (fallback pro vsechny tenanty).
        sa.Column("tenant_id", sa.BigInteger(),
                  sa.ForeignKey("tenants.id", ondelete="SET NULL"),
                  nullable=True),
        # phone | email   (v budoucnu slack | teams | whatsapp ...)
        sa.Column("channel_type", sa.String(length=20), nullable=False),
        # +420... pro phone, adresa@domena pro email
        sa.Column("identifier", sa.String(length=255), nullable=False),
        # Pro email: Fernet-zasifrovane heslo. Pro phone: NULL.
        sa.Column("credentials_encrypted", sa.Text(), nullable=True),
        # Pro email: EWS server URL. Pro phone: NULL.
        sa.Column("server", sa.String(length=255), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False,
                  server_default=sa.text("true")),
        sa.Column("is_enabled", sa.Boolean(), nullable=False,
                  server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # Lookup: najdi vsechny kanaly dane persony daneho typu.
    op.create_index(
        "ix_persona_channels_persona_type",
        "persona_channels",
        ["persona_id", "channel_type"],
    )
    # Reverse lookup: kdo vlastni dane cislo/email (pro incoming webhook
    # resolve podle to_phone nebo delivery addr).
    op.create_index(
        "ix_persona_channels_identifier",
        "persona_channels",
        ["channel_type", "identifier"],
    )


def downgrade() -> None:
    op.drop_index("ix_persona_channels_identifier", table_name="persona_channels")
    op.drop_index("ix_persona_channels_persona_type", table_name="persona_channels")
    op.drop_table("persona_channels")
