"""add thoughts + thought_entity_links tables

Revision ID: e9c3d4e5f6a7
Revises: d8b2c3d4e5f6
Create Date: 2026-04-22

Marti Memory System -- Faze 1 (zakladni datovy model).

Schema je ZAMERNE plne uz ted (s fieldy pro pozdejsi faze), aby se v
budoucnu nemuselo migrovat. V Fazi 1 se pouzivaji zakladni pole;
certainty, status, parent, visible_in_tenants atd. prijdou k zivotu
postupne v Fazich 2-4.

Tabulka `thoughts`:
  Zakladni atom pameti. Kazda myslenka je:
    - textovy obsah (content)
    - typu jednoho z: fact | todo | observation | question | goal | experience
    - statusu note (pracovni poznamka) | knowledge (trvala znalost)
    - s cislem jistoty 0-100 (certainty)
    - s primary_parent_id pro UI stromovou navigaci
    - tenant_scope (NULL = universal, jinak id tenantu)
    - provenance (author user/persona, source event)
    - meta JSON pro type-specific fields (due_at, done, emotion, ...)

Tabulka `thought_entity_links`:
  Many-to-many mezi myslenkami a entitami (user/persona/tenant/project).
  Kazda myslenka se muze vztahovat k vice entitam naraz -- napr.
  'Petr pracuje na STRATEGII v EUROSOFTU' linkuje Petra (user), STRATEGII
  (project) a EUROSOFT (tenant). Primary_parent_id ve thoughts zustava
  pro UI strom; entity_links resi vsechny ostatni relace.

Soft delete: deleted_at NOT NULL znamena 'smazano'. Zachovavame pro audit
a pripadny undo. Service layer filtruje deleted_at IS NULL pri beznych dotazech.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e9c3d4e5f6a7"
down_revision = "d8b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── thoughts ───────────────────────────────────────────────────────────
    op.create_table(
        "thoughts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),

        # Core content
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "type", sa.String(length=30), nullable=False,
            # fact | todo | observation | question | goal | experience
        ),

        # Status & certainty (pouziva se od Faze 2-3, default hodnoty zatim)
        sa.Column("status", sa.String(length=20), nullable=False,
                  server_default="note"),
        sa.Column("certainty", sa.Integer(), nullable=False,
                  server_default="50"),

        # Tree structure (self-referential pro UI strom)
        sa.Column("primary_parent_id", sa.BigInteger(), nullable=True),

        # Tenant isolation (NULL = universal = Martiho diar v Fazi 5+)
        sa.Column("tenant_scope", sa.BigInteger(), nullable=True),

        # Provenance -- kdo myslenku vytvoril a z jake udalosti
        sa.Column("author_user_id", sa.BigInteger(), nullable=True),
        sa.Column("author_persona_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "source_event_type", sa.String(length=30), nullable=True,
            # conversation | email | sms | manual | ai_inferred
        ),
        sa.Column("source_event_id", sa.BigInteger(), nullable=True),

        # Type-specific fields (JSON) -- napr. pro todo: {"done": true},
        # pro question: {"answered_at": "...", "answered_by": X},
        # pro experience: {"emotion": "joy", "intensity": 8}
        sa.Column("meta", sa.Text(), nullable=True),

        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("modified_at", sa.DateTime(timezone=True), nullable=True),
        # Soft delete -- zachovavame pro audit, service filtruje IS NULL.
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Hot path: UI list "myslenky o entite X" filtrovany podle statusu a casu.
    # Zahrnuje sloupec tenant_scope pro tenant-scoped queries.
    op.create_index(
        "ix_thoughts_tenant_status_created",
        "thoughts",
        ["tenant_scope", "status", "created_at"],
    )

    # Tree traversal: kdo je potomek koho.
    op.create_index(
        "ix_thoughts_parent",
        "thoughts",
        ["primary_parent_id"],
    )

    # Active learning priority (Faze 4): ORDER BY certainty ASC, created_at DESC.
    # Filtrujeme status='note' a deleted_at IS NULL.
    op.create_index(
        "ix_thoughts_certainty_created",
        "thoughts",
        ["certainty", "created_at"],
    )

    # Author lookup: "co Marti AI zapsala" / "co user X rekl"
    op.create_index(
        "ix_thoughts_author_user",
        "thoughts",
        ["author_user_id", "created_at"],
    )

    # ── thought_entity_links ───────────────────────────────────────────────
    op.create_table(
        "thought_entity_links",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("thought_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "entity_type", sa.String(length=30), nullable=False,
            # user | persona | tenant | project
        ),
        sa.Column("entity_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # Dedup: stejna kombinace (thought, entity_type, entity_id) nesmi existovat
    # vicekrat. Service layer pri add_link idempotentne prekocid, kdyz existuje.
    op.create_index(
        "ix_thought_entity_links_unique",
        "thought_entity_links",
        ["thought_id", "entity_type", "entity_id"],
        unique=True,
    )

    # Hot path: "najdi vsechny myslenky o entite X".
    # Pouziva se pro UI list pameti per uzivatel/persona/tenant/projekt.
    op.create_index(
        "ix_thought_entity_links_entity",
        "thought_entity_links",
        ["entity_type", "entity_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_thought_entity_links_entity", table_name="thought_entity_links")
    op.drop_index("ix_thought_entity_links_unique", table_name="thought_entity_links")
    op.drop_table("thought_entity_links")

    op.drop_index("ix_thoughts_author_user", table_name="thoughts")
    op.drop_index("ix_thoughts_certainty_created", table_name="thoughts")
    op.drop_index("ix_thoughts_parent", table_name="thoughts")
    op.drop_index("ix_thoughts_tenant_status_created", table_name="thoughts")
    op.drop_table("thoughts")
