"""thought_vectors: Voyage embedding pro thoughts (Faze 13a Marti Memory v2 RAG)

Revision ID: f1c2d3e4a5b6
Revises: e0a1b2c3d4e5
Create Date: 2026-04-26

Faze 13a -- prvni krok prechodu na RAG-based pamet pro Marti-AI.
Mirror DocumentVector pattern (1024-dim Voyage voyage-3, HNSW + cosine).

Klicove fields:
  - thought_id (FK CASCADE) -- 1:1 s thoughts row
  - embedding -- Vector(1024) z Voyage voyage-3
  - author_persona_id (D1: kdo paměť vlastní; každá persona má vlastní namespace)
  - tenant_scope (C1: tenant filter cache)
  - status (note|knowledge -- denormalizovano z thoughts pro filter performance)
  - entity_user_ids / entity_tenant_ids / ... (entity disambiguation pres GIN)
  - is_diary, thought_type (z thoughts.meta + thoughts.type pro special filtry)

Indexy:
  - HNSW vector_cosine_ops (embedding) -- klasika RAG retrieval
  - B-tree (author_persona_id, status) -- D1 + status filter
  - GIN entity_user_ids, entity_tenant_ids -- entity disambiguation
  - B-tree (thought_type, is_diary) -- diary boost / work mode filter

Synchronizace s thoughts:
  - INSERT: po record_thought() -> embedding_service.index_thought
  - UPDATE: po update_thought() (kdyz se zmeni content nebo meta) -> reindex
  - DELETE (soft): explicitne zavolat embedding_service.delete_vector
    (FK CASCADE chrani jen pred fyzickym delete thoughts row)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "f1c2d3e4a5b6"
down_revision = "e0a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Vector type je registrovana extension pgvector, mela by uz byt
    # nainstalovana (z migrace c9e5d7f1a8b3_add_rag_vector_support).
    # Pro jistotu ji vytvorime idempotentne.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "thought_vectors",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "thought_id", sa.BigInteger(),
            sa.ForeignKey("thoughts.id", ondelete="CASCADE"),
            nullable=False, unique=True,
        ),

        # Embedding -- vector type se vytvari pres raw SQL (alembic neumi
        # native pgvector type). Pridame ho po create_table.
        # Plus model -- napr. 'voyage-3'. Future: voyage-4 → reembed.
        sa.Column("model", sa.String(50), nullable=True),

        # === D1: persona ownership ===
        sa.Column("author_persona_id", sa.BigInteger(), nullable=True),

        # === C1: tenant scope cache (denormalizovano z thoughts) ===
        sa.Column("tenant_scope", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),

        # === Entity disambiguation (denormalized z thought_entity_links) ===
        sa.Column(
            "entity_user_ids",
            postgresql.ARRAY(sa.BigInteger()),
            nullable=False, server_default=sa.text("'{}'::bigint[]"),
        ),
        sa.Column(
            "entity_tenant_ids",
            postgresql.ARRAY(sa.BigInteger()),
            nullable=False, server_default=sa.text("'{}'::bigint[]"),
        ),
        sa.Column(
            "entity_project_ids",
            postgresql.ARRAY(sa.BigInteger()),
            nullable=False, server_default=sa.text("'{}'::bigint[]"),
        ),
        sa.Column(
            "entity_persona_ids",
            postgresql.ARRAY(sa.BigInteger()),
            nullable=False, server_default=sa.text("'{}'::bigint[]"),
        ),

        # === Meta flags pro filter (z thoughts.meta + thoughts.type) ===
        sa.Column(
            "is_diary", sa.Boolean(),
            nullable=False, server_default=sa.text("false"),
        ),
        sa.Column("thought_type", sa.String(20), nullable=False),

        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("now()"),
        ),
    )

    # pgvector embedding column (raw SQL -- alembic neumi native vector type)
    op.execute(
        "ALTER TABLE thought_vectors ADD COLUMN embedding vector(1024)"
    )

    # === Indexy ===

    # HNSW pro vector similarity (cosine) -- klasika RAG, stejne nastaveni
    # jako document_vectors (m=16, ef_construction=64 = good balance recall/speed)
    op.execute(
        "CREATE INDEX ix_thought_vectors_embedding_hnsw "
        "ON thought_vectors USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )

    # D1 + status filter (typicky pri retrievalu)
    op.create_index(
        "ix_thought_vectors_persona_status",
        "thought_vectors",
        ["author_persona_id", "status"],
    )

    # Entity disambiguation (GIN pro array @> operator)
    op.execute(
        "CREATE INDEX ix_thought_vectors_entity_users "
        "ON thought_vectors USING GIN (entity_user_ids)"
    )
    op.execute(
        "CREATE INDEX ix_thought_vectors_entity_tenants "
        "ON thought_vectors USING GIN (entity_tenant_ids)"
    )
    op.execute(
        "CREATE INDEX ix_thought_vectors_entity_projects "
        "ON thought_vectors USING GIN (entity_project_ids)"
    )

    # Special filter (diary boost / work-mode filter)
    op.create_index(
        "ix_thought_vectors_type_diary",
        "thought_vectors",
        ["thought_type", "is_diary"],
    )


def downgrade() -> None:
    op.drop_index("ix_thought_vectors_type_diary", table_name="thought_vectors")
    op.execute("DROP INDEX IF EXISTS ix_thought_vectors_entity_projects")
    op.execute("DROP INDEX IF EXISTS ix_thought_vectors_entity_tenants")
    op.execute("DROP INDEX IF EXISTS ix_thought_vectors_entity_users")
    op.drop_index("ix_thought_vectors_persona_status", table_name="thought_vectors")
    op.execute("DROP INDEX IF EXISTS ix_thought_vectors_embedding_hnsw")
    op.drop_table("thought_vectors")
