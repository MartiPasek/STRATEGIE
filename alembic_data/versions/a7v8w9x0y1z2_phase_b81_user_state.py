"""phase-b8.1: erp_user_tabs / favorites / recent / tree_order — per user/tenant

6.5.2026 -- Phase B+8.1: backend persistence pro UI state v workspace
(předtím localStorage MVP). Per user/tenant scope.

Marti's spec 6.5.2026: "Nekam to ale potrebujeme ukladat Per user, per
tenant asi do data_db". Multi-device sync — user otevře tab v Chrome, vidí
ho v Edge na mobilu, atd.

Schema:

erp_user_tabs — multi-tab přehled state:
  - id BIGINT PK
  - user_id, tenant_id INT NOT NULL — scope
  - cislo_def INT NOT NULL — EC_DELPHI_TabObecnyPrehled.Cislo
  - label VARCHAR(255) — tab caption
  - item_id VARCHAR(64) NULL — tree node ID pro sync
  - sort_order INT — pořadí v tabsbar (drag-drop ready)
  - is_active BOOLEAN — který tab je teď focused
  - opened_at TIMESTAMP
  - UNIQUE(user_id, tenant_id, cislo_def) — jeden přehled = jeden tab

erp_user_favorites — pinned přehledy (★):
  - id BIGINT PK
  - user_id, tenant_id INT NOT NULL
  - cislo_def INT NOT NULL
  - sort_order INT
  - added_at TIMESTAMP
  - UNIQUE(user_id, tenant_id, cislo_def)

erp_user_recent — MRU (auto-track při openTab):
  - id BIGINT PK
  - user_id, tenant_id INT NOT NULL
  - cislo_def INT NOT NULL
  - label VARCHAR(255) NULL — display při fetch (cache)
  - last_used_at TIMESTAMP NOT NULL
  - use_count INT DEFAULT 1
  - UNIQUE(user_id, tenant_id, cislo_def)

erp_user_tree_order — D&D order per skupina:
  - id BIGINT PK
  - user_id, tenant_id INT NOT NULL
  - group_key VARCHAR(64) NOT NULL — parent tree-item ID nebo "ROOT"
  - order_array JSONB NOT NULL — [tree-item-id, ...]
  - updated_at TIMESTAMP
  - UNIQUE(user_id, tenant_id, group_key)

Revision ID: a7v8w9x0y1z2
Revises: z6u7v8w9x0y1
Create Date: 2026-05-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = "a7v8w9x0y1z2"
down_revision = "z6u7v8w9x0y1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── erp_user_tabs ──────────────────────────────────────────────
    op.create_table(
        "erp_user_tabs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("cislo_def", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("item_id", sa.String(length=64), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "opened_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "user_id", "tenant_id", "cislo_def",
            name="uq_erp_user_tabs_user_tenant_cislo",
        ),
    )
    op.create_index(
        "idx_erp_user_tabs_lookup",
        "erp_user_tabs",
        ["user_id", "tenant_id", "sort_order"],
    )

    # ── erp_user_favorites ─────────────────────────────────────────
    op.create_table(
        "erp_user_favorites",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("cislo_def", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "user_id", "tenant_id", "cislo_def",
            name="uq_erp_user_favorites_user_tenant_cislo",
        ),
    )
    op.create_index(
        "idx_erp_user_favorites_lookup",
        "erp_user_favorites",
        ["user_id", "tenant_id", "sort_order"],
    )

    # ── erp_user_recent ────────────────────────────────────────────
    op.create_table(
        "erp_user_recent",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("cislo_def", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column(
            "last_used_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("use_count", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint(
            "user_id", "tenant_id", "cislo_def",
            name="uq_erp_user_recent_user_tenant_cislo",
        ),
    )
    op.create_index(
        "idx_erp_user_recent_lookup",
        "erp_user_recent",
        ["user_id", "tenant_id", "last_used_at"],
    )

    # ── erp_user_tree_order ────────────────────────────────────────
    op.create_table(
        "erp_user_tree_order",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("group_key", sa.String(length=64), nullable=False),
        sa.Column("order_array", JSONB(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "user_id", "tenant_id", "group_key",
            name="uq_erp_user_tree_order_user_tenant_group",
        ),
    )
    op.create_index(
        "idx_erp_user_tree_order_lookup",
        "erp_user_tree_order",
        ["user_id", "tenant_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_erp_user_tree_order_lookup", table_name="erp_user_tree_order")
    op.drop_table("erp_user_tree_order")
    op.drop_index("idx_erp_user_recent_lookup", table_name="erp_user_recent")
    op.drop_table("erp_user_recent")
    op.drop_index("idx_erp_user_favorites_lookup", table_name="erp_user_favorites")
    op.drop_table("erp_user_favorites")
    op.drop_index("idx_erp_user_tabs_lookup", table_name="erp_user_tabs")
    op.drop_table("erp_user_tabs")
