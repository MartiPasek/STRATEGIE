"""add description to personas

Revision ID: c2e8b4f1a93d
Revises: 7f3a2c9b1e84
Create Date: 2026-04-20

Pridava sloupec personas.description (krátký jednořádkový popis role —
např. "Specialista na české právo", "Psychologický průvodce"). Použito
v UI seznamech (list_personas tool, persona dropdown), aby user nemusel
číst plný system_prompt v náhledu — ten je pro AI, ne pro lidi.
"""
from alembic import op
import sqlalchemy as sa


revision = "c2e8b4f1a93d"
down_revision = "7f3a2c9b1e84"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("personas", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("personas", "description")
