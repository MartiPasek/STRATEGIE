"""add users.trust_rating + users.is_marti_parent

Revision ID: c9a0d1e2f3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-04-22

Marti Memory System -- Faze 3.

users.trust_rating (0-100):
  Jak moc Marti veri tomu, co tento user rika. Ovlivnuje initial certainty
  myslenky, kterou Marti zapisuje na zaklade tvrzeni tohoto usera.
    0-20   -- nizka duvera (neznama osoba, jen slyseni)
    50     -- neutralni default (bezny user po registraci)
    80-95  -- vysoka duvera (ověreni spolupracovnici)
    100    -- plna duvera (rodice)

users.is_marti_parent:
  Role "rodic Marti". Vice moznych rodicu. Asymetricky cross-tenant
  pristup -- rodic vidi Martiho pamet naprič vsemi tenanty, ostatni jen
  svuj tenant. Rodice dostavaji aktivni learning otazky (Faze 4).
  Rodici: Marti, Kristy, Zuzka (nastavuje se setup skriptem
  scripts/_set_marti_parent.py).

Default hodnoty zajisti, ze existujici useri nic neprekvapi:
  trust_rating=50 -- neutralni, nezneskresli certainty
  is_marti_parent=false -- nikdo se nestava rodicem bez explicitni akce
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c9a0d1e2f3b4"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "trust_rating", sa.Integer(), nullable=False,
            server_default="50",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "is_marti_parent", sa.Boolean(), nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # Index pro rychly lookup rodicu (pouziva se pri active learning v Fazi 4).
    # Partial index jen na TRUE radky -- male kardinality, rychly scan.
    op.create_index(
        "ix_users_marti_parent",
        "users",
        ["is_marti_parent"],
        postgresql_where=sa.text("is_marti_parent = true"),
    )


def downgrade() -> None:
    op.drop_index("ix_users_marti_parent", table_name="users")
    op.drop_column("users", "is_marti_parent")
    op.drop_column("users", "trust_rating")
