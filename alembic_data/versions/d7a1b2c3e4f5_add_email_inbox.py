"""add email_inbox table

Revision ID: d7a1b2c3e4f5
Revises: b5c6d7e8f0a1
Create Date: 2026-04-22

Email inbox -- prichozi emaily fetchnute z Exchange/EWS pres ews_fetcher.
Paralelni struktura k sms_inbox, ale email je pull-model:
  worker (scripts/email_fetcher.py) polluje INBOX kazdych 60s,
  stahuje unread, oznaci jako read v EWS, ulozi do teto tabulky.

persona_id = komu to prislo (vlastnik persona_channel s matching email).
message_id = RFC822 Message-ID z Exchange, pro dedup. UNIQUE zajistuje ze
  opakovany fetch stejne zpravy (napr. po restartu) neudelaji duplikat.

Workflow pole:
  read_at       -- kdy si user zpravu poprve zobrazil v UI
  processed_at  -- kdy se s emailem skoncilo (NULL = v prichozich,
                   NOT NULL = zpracovane). Plni se bud manualne pres UI
                   akci "Oznacit jako zpracovane", nebo kaskadou z posledniho
                   dokonceneho tasku (stejne jako sms_inbox).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d7a1b2c3e4f5"
down_revision = "b5c6d7e8f0a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_inbox",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("persona_id", sa.BigInteger(), nullable=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=True),
        sa.Column("from_email", sa.String(length=320), nullable=False),
        sa.Column("from_name", sa.String(length=255), nullable=True),
        sa.Column("to_email", sa.String(length=320), nullable=False),
        sa.Column("subject", sa.String(length=998), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        # RFC822 Message-ID pro dedup. Exchange ho vzdy ma; pokud by nahodou
        # chybel, fetcher dopocita hash(from+subject+received_at) a prefixne "synthetic:".
        sa.Column("message_id", sa.String(length=998), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stored_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        # JSON metadata z EWS (folder, cc, bcc, has_attachments, importance, ...).
        sa.Column("meta", sa.Text(), nullable=True),
    )

    # Dedup: stejna zprava v ramci persony (dvojity fetch) nesmi projit podruhe.
    # Unique per persona_id (ne globalne), protoze tentyz email muze pristat
    # do inboxu vice person (napr. CC na obe firemni adresy).
    op.create_index(
        "ix_email_inbox_persona_message_unique",
        "email_inbox",
        ["persona_id", "message_id"],
        unique=True,
    )

    # Hot path: UI list a unread count.
    op.create_index(
        "ix_email_inbox_persona_received",
        "email_inbox",
        ["persona_id", "received_at"],
    )
    op.create_index(
        "ix_email_inbox_persona_read_received",
        "email_inbox",
        ["persona_id", "read_at", "received_at"],
    )
    # Pro filter "Prichozi vs Zpracovane" v UI.
    op.create_index(
        "ix_email_inbox_persona_processed_received",
        "email_inbox",
        ["persona_id", "processed_at", "received_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_email_inbox_persona_processed_received", table_name="email_inbox")
    op.drop_index("ix_email_inbox_persona_read_received", table_name="email_inbox")
    op.drop_index("ix_email_inbox_persona_received", table_name="email_inbox")
    op.drop_index("ix_email_inbox_persona_message_unique", table_name="email_inbox")
    op.drop_table("email_inbox")
