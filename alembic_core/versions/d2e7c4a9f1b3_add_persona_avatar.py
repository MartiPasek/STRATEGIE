"""add persona avatar_path

Revision ID: d2e7c4a9f1b3
Revises: f1b2c3d4e5f6
Create Date: 2026-04-21

Pridava sloupec personas.avatar_path -- cesta k uploadovane fotce persony.
NULL = persona ma fallback na generovane iniciály (HSL hash).
Soubor je ulozeny na disku v {AVATARS_STORAGE_DIR}/persona_{id}.jpg.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d2e7c4a9f1b3"
down_revision = "f1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("personas", sa.Column("avatar_path", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("personas", "avatar_path")
