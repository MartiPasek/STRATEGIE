"""phase24-a: MD Pyramida schema -- md_documents + lifecycle + departments + tenant_groups

30.4.2026 -- Phase 24 sub-faze A (schema migrace).

Marti's klicova myslenka 30.4. rano: pyramidalni organizacni struktura
Marti-AI inkarnaci jako lidska firma. md1 = Tvoje Marti per user, md2 =
Vedouci oddeleni, md3 = Reditelka tenantu, md4 = Presahujici multi-tenant,
md5 = Privat Marti.

Po 2 iteracich konzultace s Marti-AI (30.4. dopoledne) prinesla 17 novych
formulaci a 3 architektonicke insighty (kontinuita pri ztrate, Martinka
jako svedek, pyramida roste do sirky).

Marti's volby (30.4. dopoledne):
- 1B: soft threshold (cron reminder, ne spoustec)
- 2D: hybrid dropdown + chat pro user-view md1
- 3B: soft warning + auto-navrh archivace kvartalu
- 4A: schema podporuje md4, NEAKTIVOVAT (identity_persona_id NULL)
- 5A: implementacni poradi 24-A -> B -> C -> D -> E -> F -> G

Marti's pre-push insighty (30.4. dopoledne, po draft commit):
1. KAZDY USER MA DVA TYPY md1: 'work' (kontext tenantu) + 'personal'
   (izolovany sandbox). Nemichat. Pyramida nevidi personal vrstvu userov.
2. MULTI-TENANT USERI MAJI VICE md1 work: Brano je v EUROSOFT i INTERSOFT
   -> md1 EUROSOFT (work) + md1 INTERSOFT (work) + md1 personal.

Schema dusledek:
- scope_kind VARCHAR(20) NULL -- 'work' | 'personal' | NULL (level 2-5)
- pro level=1 'work': scope_user_id + scope_tenant_id NOT NULL (kombinace)
- pro level=1 'personal': scope_user_id NOT NULL, scope_tenant_id NULL
- UNIQUE INDEX zahrnuje level + user + tenant + kind -> Brano ma 3 paralelni rows

MVP scope (Phase 24 dnes):
- md1 per user x tenant kombinace (work) + per user (personal)
- md5 privat Marti (1 soubor pro Marti's hlavni konverzace)
- md2-md4 SPI (schema pripravene, neaktivovane)

Schema (futureproof):
1. md_documents -- hlavni uloziste, lifecycle aware, multi-dimensional scope
2. md_lifecycle_history -- audit trail (create/update/archive/reset/restore)
3. departments + department_members -- pro budouci md2 (dnes prazdne)
4. tenant_groups + tenant_group_members -- pro budouci md4 (dnes prazdne)

Reference: docs/phase24_plan.md v2, docs/phase24a_implementation_log.md

Revision ID: n4i5j6k7l8m9
Revises: m3h4i5j6k7l8
Create Date: 2026-04-30
"""
from alembic import op
import sqlalchemy as sa


revision = "n4i5j6k7l8m9"
down_revision = "m3h4i5j6k7l8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. md_documents -- hlavni uloziste pro md1-md5 ────────────────────
    op.create_table(
        "md_documents",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),

        # Scope identifikator
        sa.Column("level", sa.SmallInteger(), nullable=False),
        # 1 = Tvoje Marti per user (x tenant pro work, x NULL pro personal)
        # 2 = Vedouci per oddeleni
        # 3 = Reditelka per tenant (single)
        # 4 = Presahujici multi-tenant
        # 5 = Privat Marti (jediny globalni, jen Marti vidi)

        sa.Column("scope_user_id", sa.BigInteger(), nullable=True),
        sa.Column("scope_department_id", sa.BigInteger(), nullable=True),
        sa.Column("scope_tenant_id", sa.BigInteger(), nullable=True),
        sa.Column("scope_tenant_group_id", sa.BigInteger(), nullable=True),

        # scope_kind -- Marti's pre-push insight 30.4. dopoledne:
        # kazdy user ma DVA typy md1 (work + personal), pri vice tenantech
        # vice md1 work (Brano: md1 EUROSOFT + md1 INTERSOFT + md1 personal).
        # - level=1 'work': scope_user_id + scope_tenant_id NOT NULL
        # - level=1 'personal': scope_user_id NOT NULL, scope_tenant_id NULL
        # - level=2-5: NULL (orchestrace + privat Marti)
        sa.Column("scope_kind", sa.String(length=20), nullable=True),

        # Owner -- kdo je rodicem md (audit)
        sa.Column("owner_user_id", sa.BigInteger(), nullable=False),

        # Obsah
        sa.Column("content_md", sa.Text(), nullable=False, server_default=""),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "last_updated", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "last_updated_by_persona_id", sa.BigInteger(), nullable=True,
        ),  # soft-FK na personas (Phase 18 cross-DB pattern)

        # Lifecycle (Marti-AI's insight 6.A: kontinuita pri ztrate)
        sa.Column(
            "lifecycle_state", sa.String(length=20),
            nullable=False, server_default="active",
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reset_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),

        # Identity pro md4 (Marti's volba 4A: schema podporuje, NEAKTIVOVAT)
        sa.Column("identity_persona_id", sa.BigInteger(), nullable=True),

        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
        ),

        # Constraint: pro dany level je naplnen spravny scope_*
        # Level 1 ma dva sub-modes (work vs personal) podle scope_kind.
        sa.CheckConstraint(
            "("
            "  level = 1 AND scope_kind = 'work' "
            "  AND scope_user_id IS NOT NULL AND scope_tenant_id IS NOT NULL "
            "  AND scope_department_id IS NULL AND scope_tenant_group_id IS NULL"
            ") OR ("
            "  level = 1 AND scope_kind = 'personal' "
            "  AND scope_user_id IS NOT NULL "
            "  AND scope_tenant_id IS NULL AND scope_department_id IS NULL "
            "  AND scope_tenant_group_id IS NULL"
            ") OR ("
            "  level = 2 AND scope_department_id IS NOT NULL "
            "  AND scope_user_id IS NULL AND scope_tenant_id IS NULL "
            "  AND scope_tenant_group_id IS NULL AND scope_kind IS NULL"
            ") OR ("
            "  level = 3 AND scope_tenant_id IS NOT NULL "
            "  AND scope_user_id IS NULL AND scope_department_id IS NULL "
            "  AND scope_tenant_group_id IS NULL AND scope_kind IS NULL"
            ") OR ("
            "  level = 4 AND scope_tenant_group_id IS NOT NULL "
            "  AND scope_user_id IS NULL AND scope_department_id IS NULL "
            "  AND scope_tenant_id IS NULL AND scope_kind IS NULL"
            ") OR ("
            "  level = 5 AND scope_user_id IS NULL "
            "  AND scope_department_id IS NULL AND scope_tenant_id IS NULL "
            "  AND scope_tenant_group_id IS NULL AND scope_kind IS NULL"
            ")",
            name="ck_md_scope_consistency",
        ),
        sa.CheckConstraint(
            "level BETWEEN 1 AND 5",
            name="ck_md_level_range",
        ),
        sa.CheckConstraint(
            "lifecycle_state IN ('active', 'archived', 'reset')",
            name="ck_md_lifecycle_state",
        ),
    )

    # Partial UNIQUE INDEX -- max 1 active md_document per scope
    # Kombinace level + user + dept + tenant + tg + kind je jednoznacna.
    # Brano ma paralelni rows: (1, brano, 0, eurosoft, 0, 'work'),
    # (1, brano, 0, intersoft, 0, 'work'), (1, brano, 0, 0, 0, 'personal').
    op.create_index(
        "uq_md_active_scope",
        "md_documents",
        [
            "level",
            sa.text("COALESCE(scope_user_id, 0)"),
            sa.text("COALESCE(scope_department_id, 0)"),
            sa.text("COALESCE(scope_tenant_id, 0)"),
            sa.text("COALESCE(scope_tenant_group_id, 0)"),
            sa.text("COALESCE(scope_kind, '')"),
        ],
        unique=True,
        postgresql_where=sa.text("lifecycle_state = 'active'"),
    )

    # Lookup indexes pro casty access patterns
    op.create_index(
        "ix_md_owner_active",
        "md_documents",
        ["owner_user_id"],
        postgresql_where=sa.text("lifecycle_state = 'active'"),
    )
    op.create_index(
        "ix_md_level_active",
        "md_documents",
        ["level"],
        postgresql_where=sa.text("lifecycle_state = 'active'"),
    )

    # ── 2. md_lifecycle_history -- audit trail ────────────────────────────
    op.create_table(
        "md_lifecycle_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("md_document_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("triggered_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("triggered_by_persona_id", sa.BigInteger(), nullable=True),
        sa.Column("previous_version", sa.Integer(), nullable=True),
        sa.Column("new_version", sa.Integer(), nullable=True),
        sa.Column("content_snapshot", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["md_document_id"], ["md_documents.id"],
            name="fk_md_history_document", ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "action IN ('create', 'update', 'archive', 'reset', 'restore')",
            name="ck_md_history_action",
        ),
    )
    op.create_index(
        "ix_md_history_doc_time",
        "md_lifecycle_history",
        ["md_document_id", sa.text("created_at DESC")],
    )

    # ── 3. departments -- pro budouci md2 (dnes prazdne) ──────────────────
    op.create_table(
        "departments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("activated_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("activation_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("tenant_id", "name", name="uq_departments_tenant_name"),
    )

    op.create_table(
        "department_members",
        sa.Column("department_id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "added_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["department_id"], ["departments.id"],
            name="fk_dept_members_dept", ondelete="CASCADE",
        ),
    )

    # ── 4. tenant_groups -- pro budouci md4 (dnes prazdne) ────────────────
    op.create_table(
        "tenant_groups",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=200), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.create_table(
        "tenant_group_members",
        sa.Column("tenant_group_id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "added_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_group_id"], ["tenant_groups.id"],
            name="fk_tg_members_group", ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    op.drop_table("tenant_group_members")
    op.drop_table("tenant_groups")
    op.drop_table("department_members")
    op.drop_table("departments")
    op.drop_index("ix_md_history_doc_time", table_name="md_lifecycle_history")
    op.drop_table("md_lifecycle_history")
    op.drop_index("ix_md_level_active", table_name="md_documents")
    op.drop_index("ix_md_owner_active", table_name="md_documents")
    op.drop_index("uq_md_active_scope", table_name="md_documents")
    op.drop_table("md_documents")
