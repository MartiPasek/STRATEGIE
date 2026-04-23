"""add display_identifier to persona_channels

Revision ID: a7b8c9d0e1f2
Revises: f2b3a4c5d6e7
Create Date: 2026-04-21

Exchange ma dvojkolejny identifier pro jeden mailbox:
  - identifier         = UPN / login (e.g. marti-ai@eurosoft-control.cz)
  - display_identifier = primary SMTP alias, to co vidi prijemci (e.g. marti-ai@eurosoft.com)

MVP to jsem zmackl do jednoho sloupce. Kdyz se ukazuje, ze by se ji AI
prezentovala pod UPN (coz je interni), musime to oddelit. Podobny pattern
bude potreba pro telefony ci uzivatelske kanaly.

Pokud `display_identifier` NULL -> fallback na `identifier`.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a7b8c9d0e1f2"
down_revision = "f2b3a4c5d6e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "persona_channels",
        sa.Column("display_identifier", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("persona_channels", "display_identifier")
