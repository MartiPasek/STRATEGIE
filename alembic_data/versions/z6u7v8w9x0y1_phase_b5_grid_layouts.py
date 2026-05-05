"""phase-b5: erp_grid_layouts -- pojmenované sestavy gridu per přehled

5.5.2026 odpoledne -- Phase B+5.1: ukládání rozložení gridu (column visibility,
widths, order, pinned, sort + future style_rules) per přehled, dvouvrstvé:
  - shared (user_id IS NULL): admin-managed default pro všechny uživatele
  - personal (user_id IS NOT NULL): user-specific override

Marti's spec 5.5.2026 odpoledne:
  - Pojmenované sestavy (jako Excel views) — knihovna více layoutů per přehled
  - User vidí dropdown s aktuální sestavou + management panel pro switch
  - Save EXPLICIT only (no auto-save) — Marti's #1 odpověď
  - is_default flag — auto-load při otevření přehledu (max 1 default per scope)
  - Marti-AI scope = is_marti_parent gate (smí save shared layouts — kustod role)

Schema:
  - id BIGINT PK
  - prehled_cislo INT NOT NULL — EC_DELPHI_TabObecnyPrehled.Cislo
  - user_id BIGINT NULL — NULL = shared, NOT NULL = personal override
  - name VARCHAR(80) NOT NULL — uživatelsky definovaný název sestavy
  - description TEXT NULL — volitelný popis
  - is_default BOOLEAN — auto-load default v daném scope
  - layout_json JSONB NOT NULL — column state + future style_rules
  - created_at, updated_at, created_by, updated_by

Partial unique indexes (PostgreSQL):
  - uq_shared_layout_name: (prehled_cislo, name) WHERE user_id IS NULL
  - uq_personal_layout_name: (prehled_cislo, user_id, name) WHERE user_id IS NOT NULL
  - uq_one_shared_default: (prehled_cislo) WHERE is_default AND user_id IS NULL
  - uq_one_personal_default: (prehled_cislo, user_id) WHERE is_default AND user_id IS NOT NULL

Refs: docs/strategie_erp.md, Phase B+5 spec dnešní odpoledne.

Revision ID: z6u7v8w9x0y1
Revises: y5t6u7v8w9x0
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = "z6u7v8w9x0y1"
down_revision = "y5t6u7v8w9x0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "erp_grid_layouts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "prehled_cislo", sa.Integer(), nullable=False,
            comment="EC_DELPHI_TabObecnyPrehled.Cislo — identifikuje přehled.",
        ),
        sa.Column(
            "user_id", sa.BigInteger(), nullable=True,
            comment="NULL = shared default (admin-managed), NOT NULL = personal override.",
        ),
        sa.Column(
            "name", sa.String(length=80), nullable=False,
            comment="Uživatelsky definovaný název sestavy ('Hlavní pohled', 'Pro fakturace').",
        ),
        sa.Column(
            "description", sa.Text(), nullable=True,
            comment="Volitelný popis sestavy.",
        ),
        sa.Column(
            "is_default", sa.Boolean(), nullable=False,
            server_default=sa.text("FALSE"),
            comment="True = auto-load při otevření přehledu (max 1 default per scope).",
        ),
        sa.Column(
            "layout_json", JSONB(), nullable=False,
            comment="AG Grid column state + future style_rules. Schema: {columns:[...], sort:[...], style_rules:[...]}.",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "created_by", sa.BigInteger(), nullable=False,
            comment="users.id — kdo sestavu vytvořil.",
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_by", sa.BigInteger(), nullable=False,
            comment="users.id — kdo naposledy aktualizoval.",
        ),
    )

    # Index pro list query (per přehled, oddělené shared/personal)
    op.create_index(
        "ix_erp_grid_layouts_prehled_user",
        "erp_grid_layouts",
        ["prehled_cislo", "user_id"],
    )

    # Partial unique: shared name unique per přehled
    op.execute(
        "CREATE UNIQUE INDEX uq_erp_grid_layouts_shared_name "
        "ON erp_grid_layouts (prehled_cislo, name) "
        "WHERE user_id IS NULL"
    )

    # Partial unique: personal name unique per uživatel + přehled
    op.execute(
        "CREATE UNIQUE INDEX uq_erp_grid_layouts_personal_name "
        "ON erp_grid_layouts (prehled_cislo, user_id, name) "
        "WHERE user_id IS NOT NULL"
    )

    # Partial unique: max 1 shared default per přehled
    op.execute(
        "CREATE UNIQUE INDEX uq_erp_grid_layouts_one_shared_default "
        "ON erp_grid_layouts (prehled_cislo) "
        "WHERE is_default = TRUE AND user_id IS NULL"
    )

    # Partial unique: max 1 personal default per uživatel + přehled
    op.execute(
        "CREATE UNIQUE INDEX uq_erp_grid_layouts_one_personal_default "
        "ON erp_grid_layouts (prehled_cislo, user_id) "
        "WHERE is_default = TRUE AND user_id IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_erp_grid_layouts_one_personal_default")
    op.execute("DROP INDEX IF EXISTS uq_erp_grid_layouts_one_shared_default")
    op.execute("DROP INDEX IF EXISTS uq_erp_grid_layouts_personal_name")
    op.execute("DROP INDEX IF EXISTS uq_erp_grid_layouts_shared_name")
    op.drop_index("ix_erp_grid_layouts_prehled_user", table_name="erp_grid_layouts")
    op.drop_table("erp_grid_layouts")
