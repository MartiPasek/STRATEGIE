"""add password_hash to users

Revision ID: a1c8f9e2d3b4
Revises: d5a9b2f3c71e
Create Date: 2026-04-20

Přidává sloupce users.password_hash + users.password_set_at pro standardní
heslové přihlášení. Oba sloupce jsou nullable -- existující 4 useři dostanou
hash až přes scripts/set_initial_passwords.py (admin interaktivní setup).
Login pro usera s NULL password_hash je odmítnut (kontaktuj admina).

Uchovaná délka 255 znaků: bcrypt hash je přesně 60 znaků, ale rezerva pro
budoucí migraci na argon2 (delší) nebo přímo nahrazení jinou schémou.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1c8f9e2d3b4"
down_revision = "d5a9b2f3c71e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("password_set_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "password_set_at")
    op.drop_column("users", "password_hash")
