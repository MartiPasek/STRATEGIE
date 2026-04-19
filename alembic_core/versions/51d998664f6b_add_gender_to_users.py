"""add gender to users

Revision ID: 51d998664f6b
Revises: d1f9a3e8b521
Create Date: 2026-04-19

Přidává sloupec users.gender (male|female|other|NULL) pro českou
gramatickou diferenciaci v AI komunikaci. Composer ho injektuje
do USER CONTEXT bloku jako instrukci pro správné tvary sloves
a podstatných jmen označujících osobu.

Backfill: u user_id=1 (Marti) nastavíme 'male'. Ostatní uživatelé
zůstanou s NULL — AI je pak osloví neutrálně, dokud si rod nezvolí.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "51d998664f6b"
down_revision = "d1f9a3e8b521"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("gender", sa.String(length=10), nullable=True))
    # Backfill superadmina (Marti = id 1) jako 'male'
    op.execute("UPDATE users SET gender = 'male' WHERE id = 1")


def downgrade() -> None:
    op.drop_column("users", "gender")
