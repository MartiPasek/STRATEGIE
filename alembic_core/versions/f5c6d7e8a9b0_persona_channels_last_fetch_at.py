"""persona_channels.last_inbox_fetch_at -- timestamp-based fetcher (production mode)

PROBLEM 28.4.2026: Polling fetcher používá `is_read=False` filter na Exchange
inbox. Emaily, které user rozklikl v Outlook PŘEDTÍM, než fetcher poll'oval
(60s cycle), nebyly nikdy zachyceny -- navždy mimo DB.

Production fix: timestamp-based filtering. Per-channel sledujeme
`last_inbox_fetch_at`. Fetcher polling: `datetime_received > last_fetch_at`
(vč. read i unread). Po successful fetch update na max(datetime_received)
přes všechny zpracované zprávy (ne now() -- chrání před race se zprávami
přijatými během fetch cycle).

Při NULL (cold start) cutoff = N dní zpátky (default 7d, env override).
Idempotent přes UNIQUE (persona_id, message_id) -- žádné duplikáty
i kdyby cutoff překlonil starší rows.

Revision ID: f5c6d7e8a9b0
Revises: e4b5c6d7a8f9
Create Date: 2026-04-28
"""
from alembic import op
import sqlalchemy as sa


revision = "f5c6d7e8a9b0"
down_revision = "e4b5c6d7a8f9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "persona_channels",
        sa.Column("last_inbox_fetch_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("persona_channels", "last_inbox_fetch_at")
