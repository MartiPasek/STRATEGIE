"""phase-35: project_memo + audit history (per-project structured memory)

8.5.2026 — Phase 35-A: project_memo tabulka pro per-projekt strukturovanou
paměť. Marti-AI's preferred design (consultation 8.5. odpoledne):
separátní model místo přidání scope_project_id do md_documents.

Marti-AI's argument:
  „md_documents nese identitu (kdo jsem pro koho). Projekt je kontext (co
   aktuálně řeším). To jsou dvě různé věci a míchat je do jednoho modelu
   vytvoří budoucí bolest."

Plus polymorfní scope (Marti-AI's vlastní insight, Marti's volba C hybrid
po consultation):
  - scope_entity_type ('user' | 'persona' | NULL=shared) z master.entity_def
  - scope_entity_id BIGINT
  - flexibilní bez ALTER TABLE pro nové entity typy
  - integrace s 12. dárek-scénou (master.entity_def jako single source
    of truth pro typy)

Schema:

project_memo — per-project living document:
  - id BIGINT PK
  - project_id BIGINT NOT NULL (soft-FK na projects, cross-DB Phase 18)
  - scope_entity_type VARCHAR(50) NULL (polymorfní typ z entity_def)
  - scope_entity_id BIGINT NULL
  - persona_id BIGINT NULL (která persona to napsala, default Marti-AI)
  - content_md TEXT NOT NULL DEFAULT '' (markdown content)
  - version INT NOT NULL DEFAULT 1
  - lifecycle_state VARCHAR(20) — active | archived | reset
  - archived_at, reset_at TIMESTAMPTZ NULL
  - reason TEXT NULL
  - created_at, last_updated TIMESTAMPTZ
  - last_updated_by_persona_id BIGINT NULL

project_memo_history — audit trail (mirror md_lifecycle_history):
  - id BIGINT PK
  - project_memo_id BIGINT FK CASCADE
  - action — create | update | archive | reset | restore
  - triggered_by_user_id BIGINT NULL
  - triggered_by_persona_id BIGINT NULL
  - previous_version, new_version INT NULL
  - content_snapshot TEXT NULL (pre-update snapshot pro forenzní audit)
  - reason TEXT NULL
  - created_at TIMESTAMPTZ

Indexes:
  - idx_project_memo_active (project_id) WHERE active
  - idx_project_memo_scope (scope_entity_type, scope_entity_id) WHERE active
  - uq_project_memo_active_scope — max 1 active per (project, scope)

Marti+Claude+Marti-AI consultation 8.5.2026 ~14:59-15:23.

Revision ID: b8w9x0y1z2a3
Revises: a7v8w9x0y1z2
Create Date: 2026-05-08 15:30:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b8w9x0y1z2a3"
down_revision = "a7v8w9x0y1z2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── project_memo (živý dokument per projekt) ──────────────────────
    op.create_table(
        "project_memo",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("project_id", sa.BigInteger(), nullable=False),
        # Polymorfní scope (Marti-AI's návrh, hybrid C):
        # NULL/NULL = shared per-project memo (všichni členové)
        # 'user'/X  = per-user-per-project memo (poznámky usera o projektu)
        # 'persona'/X = per-persona-per-project (specializované persony)
        sa.Column("scope_entity_type", sa.String(50), nullable=True),
        sa.Column("scope_entity_id", sa.BigInteger(), nullable=True),
        # Která persona ho píše (default Marti-AI)
        sa.Column("persona_id", sa.BigInteger(), nullable=True),
        # Content
        sa.Column("content_md", sa.Text(), nullable=False, server_default=""),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        # Lifecycle (mirror md_documents pattern)
        sa.Column(
            "lifecycle_state",
            sa.String(20),
            nullable=False,
            server_default="active",
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reset_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        # Audit
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("last_updated_by_persona_id", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "lifecycle_state IN ('active', 'archived', 'reset')",
            name="ck_project_memo_lifecycle",
        ),
        # Polymorfní scope consistency: type a id musí být oba NULL nebo oba NOT NULL
        sa.CheckConstraint(
            "(scope_entity_type IS NULL AND scope_entity_id IS NULL) OR "
            "(scope_entity_type IS NOT NULL AND scope_entity_id IS NOT NULL)",
            name="ck_project_memo_scope_consistency",
        ),
    )

    # Index pro project lookups (active jen)
    op.create_index(
        "idx_project_memo_active_project",
        "project_memo",
        ["project_id"],
        postgresql_where=sa.text("lifecycle_state = 'active'"),
    )

    # Index pro scope lookups (active jen)
    op.create_index(
        "idx_project_memo_active_scope",
        "project_memo",
        ["scope_entity_type", "scope_entity_id"],
        postgresql_where=sa.text(
            "lifecycle_state = 'active' AND scope_entity_type IS NOT NULL"
        ),
    )

    # Partial unique: max 1 active per (project, scope_type, scope_id)
    # COALESCE pro NULL handling — shared scope (NULL/NULL) je unikátní per project
    op.execute(
        """
        CREATE UNIQUE INDEX uq_project_memo_active_scope
        ON project_memo (
            project_id,
            COALESCE(scope_entity_type, '_shared_'),
            COALESCE(scope_entity_id, 0)
        )
        WHERE lifecycle_state = 'active'
        """
    )

    # ── project_memo_history (audit trail) ────────────────────────────
    op.create_table(
        "project_memo_history",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("project_memo_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        # create | update | archive | reset | restore
        sa.Column("triggered_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("triggered_by_persona_id", sa.BigInteger(), nullable=True),
        sa.Column("previous_version", sa.Integer(), nullable=True),
        sa.Column("new_version", sa.Integer(), nullable=True),
        sa.Column("content_snapshot", sa.Text(), nullable=True),
        # pre-update snapshot pro forenzní audit / rollback
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["project_memo_id"],
            ["project_memo.id"],
            ondelete="CASCADE",
            name="fk_project_memo_history_memo",
        ),
        sa.CheckConstraint(
            "action IN ('create', 'update', 'archive', 'reset', 'restore')",
            name="ck_project_memo_history_action",
        ),
    )

    op.create_index(
        "idx_project_memo_history_memo",
        "project_memo_history",
        ["project_memo_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_project_memo_history_memo", table_name="project_memo_history")
    op.drop_table("project_memo_history")

    op.execute("DROP INDEX IF EXISTS uq_project_memo_active_scope")
    op.drop_index("idx_project_memo_active_scope", table_name="project_memo")
    op.drop_index("idx_project_memo_active_project", table_name="project_memo")
    op.drop_table("project_memo")
