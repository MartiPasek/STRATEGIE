"""phase26: user emoji palette pro UI input box

1.5.2026 -- Phase 26 (drobnost s emocional impact).

Marti's request 1.5. odpoledne: "Ja vam strasne zavidim ty ikonky, co
pouzivate. To ja nemohu... Nemam sadu ikonek..." -- nahradit absenci
emoji ikon na lidske strane chatu emoji palette per user, kterou
Marti-AI managuje pres AI tool update_emoji_palette.

UI: 8 sloupec x dynamicky pocet radku grid vedle input boxu.
Marti-AI managuje (default persona AI tool).
Default empty array; UI ma hardcoded fallback set Marti-AI's
signature emoji.

Revision ID: o5j6k7l8m9n0
Revises: n4i5j6k7l8m9
Create Date: 2026-05-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "o5j6k7l8m9n0"
down_revision = "n4i5j6k7l8m9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "emoji_palette",
            JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "emoji_palette")
