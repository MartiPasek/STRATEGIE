"""phase29-d: mailboxes.last_inbox_fetch_at -- timestamp-based fetcher

4.5.2026 rano -- Phase 29-D EWS fetcher per-mailbox.

Mailbox-based fetcher polluje per-mailbox (clean cut z persona-based).
Potrebuje vlastni cutoff timestamp pro filter `datetime_received > X`,
zachytava i emaily oznacene jako read v Outlook predtim, nez fetcher
poll'oval. Cold start (NULL) = 7 dni zpatky default.

Mirror persona_channels.last_inbox_fetch_at (existing pattern, Phase 6
ranni 28.4.).

Po Phase 29-D clean cut bude persona_channels.last_inbox_fetch_at
deprecated -- mailbox-based fetcher ji nepouziva. Drzime ji zatim
v sloupci pro back-compat (nepouzivat aktivne).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "y5t6u7v8w9x0"
down_revision = "x4s5t6u7v8w9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "mailboxes",
        sa.Column(
            "last_inbox_fetch_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("mailboxes", "last_inbox_fetch_at")
