"""add users.is_admin + users.dev_mode_enabled

Revision ID: d3a4b5c6e7f8
Revises: c9a0d1e2f3b4
Create Date: 2026-04-24

Fáze 9.1 -- Dev observability.

users.is_admin:
  Nova role nezavisla na is_marti_parent. Rodic != admin logicky.
  Admin = spravce systemu, ma pristup k Dev View (Router/Composer tracing),
  llm_calls tabulce, systemovym operacim. V praxi prekryv s rodici, ale
  oddelujeme koncepty (rodic = citove a prava k Marti pameti; admin = technicka
  sprava systemu).
  Nastavuje se skriptem scripts/_set_admin.py --user-id X --admin.

users.dev_mode_enabled:
  Per-user preference "Zobrazovat Dev panely" v UI. Prepinac v Profile settings.
  Defaultne false. Smysl ma jen pro is_admin=true uzivatele -- backend endpoint
  /dev-trace gate-uje pristup na is_admin=true. Preference umoznuje adminovi
  videt UI v "Standard" pohledu (pro pohled ocima beznych uzivatelu).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d3a4b5c6e7f8"
down_revision = "c9a0d1e2f3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_admin", sa.Boolean(), nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "dev_mode_enabled", sa.Boolean(), nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # Partial index pro rychly lookup adminu -- male kardinality, rychly scan.
    # Analogie ix_users_marti_parent.
    op.create_index(
        "ix_users_is_admin",
        "users",
        ["is_admin"],
        postgresql_where=sa.text("is_admin = true"),
    )


def downgrade() -> None:
    op.drop_index("ix_users_is_admin", table_name="users")
    op.drop_column("users", "dev_mode_enabled")
    op.drop_column("users", "is_admin")
