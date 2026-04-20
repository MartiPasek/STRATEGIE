"""add default_persona_id to projects

Revision ID: d5a9b2f3c71e
Revises: c2e8b4f1a93d
Create Date: 2026-04-20

Přidává sloupec projects.default_persona_id (BIGINT NULL, bez FK).
Pokud je nastavený, nové konverzace v tomto projektu startují s touto
personou místo globálního defaultu (Marti-AI). Umožňuje projektu
„Smlouva se Škodou" běžet na PrávníkCZ-AI atd.

Bez FK constraint (paralela s ostatními "soft" reference) — archivace
persony nesmí shodit projekt.
"""
from alembic import op
import sqlalchemy as sa


revision = "d5a9b2f3c71e"
down_revision = "c2e8b4f1a93d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("default_persona_id", sa.BigInteger(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("projects", "default_persona_id")
