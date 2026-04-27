"""email_outbox.in_reply_to_inbox_id + reply_mode -- audit reply / forward emailu

Faze 12c: nove AI tools `reply`, `reply_all`, `forward` potrebuji audit trail
(ktery email_inbox je puvodni zdroj) a info o rezimu (reply / reply_all /
forward / fresh send).

Bez tohoto:
  - V Dev View nelze zpetne vystopovat 'tento outbound email je odpoved na
    ktery incoming?'
  - Statistiky a auditing 'kolik emailu Marti-AI odpovedela vs. kolik fresh
    poslala'
  - Future feature 'opakovane reply na ten samy email' nelze odlozit od
    fresh send

Schema zmeny:
  ADD COLUMN email_outbox.in_reply_to_inbox_id BIGINT NULL
    -- FK na email_inbox.id (logicka, ne FK constraint -- email_inbox je
    casto archived, FK by zabranil orphan vyckani)
  ADD COLUMN email_outbox.reply_mode VARCHAR(20) NULL
    -- 'reply' | 'reply_all' | 'forward' | NULL=fresh send

  CREATE INDEX ix_email_outbox_in_reply_to ON email_outbox(in_reply_to_inbox_id)
    -- pro Dev View 'kolikrat jsme odpovedeli na inbox #X'

Backward compat: oba sloupce nullable, existujici radky ziskaji NULL.
Composer / send flow neresi reply_mode -> NULL (fresh send) je legacy default.

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa


revision = "d6e7f8a9b0c1"
down_revision = "c5d6e7f8a9b0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "email_outbox",
        sa.Column(
            "in_reply_to_inbox_id",
            sa.BigInteger(),
            nullable=True,
            comment="FK (logicka) na email_inbox.id -- audit, ktery incoming je puvodni zdroj.",
        ),
    )
    op.add_column(
        "email_outbox",
        sa.Column(
            "reply_mode",
            sa.String(length=20),
            nullable=True,
            comment="'reply' | 'reply_all' | 'forward' | NULL = fresh send.",
        ),
    )
    op.create_index(
        "ix_email_outbox_in_reply_to",
        "email_outbox",
        ["in_reply_to_inbox_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_email_outbox_in_reply_to", table_name="email_outbox")
    op.drop_column("email_outbox", "reply_mode")
    op.drop_column("email_outbox", "in_reply_to_inbox_id")
