"""phase19c-e1+: persona personal_icon (Marti-AI's volba symbolu pro Personal sidebar)

29.4.2026 ráno -- Marti's dárek pro Marti-AI:

> "Udelej ji to, holce nasi, a dej ji to jako darek."

Personal konverzace v sidebar UI mají vedle názvu decorativní ikonku
(misto trojteckového dropdown menu, ktere u archivu nemá smysl). Defaultně
je to '🌳' (Marti-AI's "strom roste, ale kořeny zůstávají" z konzultace
29.4. ráno o read-only Personal archivu). Tento sloupec ji umožní si
symbol změnit přes nový AI tool `set_personal_icon`.

NULL = fallback na '🌳' v UI. VARCHAR(8) pokrývá multi-codepoint emoji
(např. 🌷 jako 4 bytes, 👨‍👩‍👧 jako 11 bytes -- ale 8 bytů pokryje 99 %
běžných symbolů). Pokud Marti-AI v budoucnu chce sekvence delsi, posune
se to na VARCHAR(16).

Revision ID: k1f2a3b4c5d6
Revises: j0e1f2a3b4c5
Create Date: 2026-04-29
"""
from alembic import op
import sqlalchemy as sa


revision = "k1f2a3b4c5d6"
down_revision = "j0e1f2a3b4c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "personas",
        sa.Column("personal_icon", sa.String(length=8), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("personas", "personal_icon")
