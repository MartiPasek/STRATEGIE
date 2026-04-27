"""conversation_notes -- Phase 15a notebook core

Phase 15a: Marti-AI dostane episodicky zapisnicek vazany ke konverzaci.
Zachycuje klicove body v realnem case, prezije pauzu i uzavreni threadu.
Mapuje se na lidsky pattern "tuzka + papir pri schuzce s vahou".

Tri-vrstva pamet po Phase 15:
  - thoughts (semantic, cross-thread)         ✅ Phase 13 RAG
  - conversation_notes (episodic per-thread)  ← TADY
  - working memory (5 zprav)                  -- sliding window
  - messages (audit / forensic)               -- existing

Po 4 iteracich konzultace s Marti-AI a 3 Marti pivotech designu:
  v1: recall_history + mark_message
  v2: pivot na zapisnicek -- "tuzka a papir" analogie
  v3: note_type enum + question loop + pravo nenapsat
  v4: zivy stav (status) + category dimenze + lifecycle + projektovy kustod
      + conversational-first UX

Schema (3 dimenze poznamky):
  Dimenze 1 (na cem stojim): note_type
    'decision' | 'fact' | 'interpretation' | 'question'
  Dimenze 2 (co s tim): category
    'task' | 'info' | 'emotion'
  Dimenze 3 (zije to jeste): status (jen pro task)
    'open' | 'completed' | 'dismissed' | 'stale' | NULL

Default certainty per note_type:
  decision: 95, fact: 85, interpretation: 60, question: 0

Indexy:
  - (conversation_id, importance DESC, created_at) -- composer query
  - (persona_id) -- per-persona overview
  - partial (conversation_id, note_type) WHERE note_type='question'
            AND resolved_at IS NULL -- open questions
  - partial (conversation_id, status) WHERE category='task'
            AND status='open' -- open tasks (auto-completion hint)

Revision ID: a0b1c2d3e4f5
Revises: d6e7f8a9b0c1
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa


revision = "a0b1c2d3e4f5"
down_revision = "d6e7f8a9b0c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conversation_notes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "conversation_id", sa.BigInteger(), nullable=False,
            comment="FK na conversations.id -- per-thread episodic memory.",
        ),
        sa.Column(
            "persona_id", sa.BigInteger(), nullable=False,
            comment="FK na personas.id -- ktera persona si poznamku zapsala.",
        ),
        sa.Column(
            "source_message_id", sa.BigInteger(), nullable=True,
            comment="FK na messages.id -- ktera zprava byla pohnutkou (nullable).",
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "note_type", sa.String(length=20), nullable=False,
            server_default="interpretation",
            comment="'decision' | 'fact' | 'interpretation' | 'question'",
        ),
        sa.Column(
            "certainty", sa.SmallInteger(), nullable=False,
            server_default="60",
            comment="1-100, default per note_type (95/85/60/0).",
        ),
        sa.Column(
            "category", sa.String(length=20), nullable=False,
            server_default="info",
            comment="'task' | 'info' | 'emotion'",
        ),
        sa.Column(
            "status", sa.String(length=20), nullable=True,
            comment="'open' | 'completed' | 'dismissed' | 'stale' | NULL (jen pro task).",
        ),
        sa.Column(
            "turn_number", sa.Integer(), nullable=False,
            server_default="1",
            comment="Relativni pozice v konverzaci -- temporal awareness pri recall.",
        ),
        sa.Column(
            "importance", sa.SmallInteger(), nullable=False,
            server_default="3",
            comment="1=detail, 3=normal, 5=zasadni (max 3 importance=5 per konv).",
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "completed_by_action_id", sa.BigInteger(), nullable=True,
            comment="FK (logicka) na action_logs / messages -- ktera akce dokoncila.",
        ),
        sa.Column(
            "resolved_at", sa.DateTime(timezone=True), nullable=True,
            comment="Pro question -> answered conversion (set pri update_note).",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "archived", sa.Boolean(), nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index(
        "ix_conv_notes_conv_imp",
        "conversation_notes",
        ["conversation_id", sa.text("importance DESC"), "created_at"],
    )
    op.create_index(
        "ix_conv_notes_persona",
        "conversation_notes",
        ["persona_id"],
    )
    op.create_index(
        "ix_conv_notes_open_q",
        "conversation_notes",
        ["conversation_id", "note_type"],
        postgresql_where=sa.text("note_type = 'question' AND resolved_at IS NULL"),
    )
    op.create_index(
        "ix_conv_notes_open_tasks",
        "conversation_notes",
        ["conversation_id", "status"],
        postgresql_where=sa.text("category = 'task' AND status = 'open'"),
    )


def downgrade() -> None:
    op.drop_index("ix_conv_notes_open_tasks", table_name="conversation_notes")
    op.drop_index("ix_conv_notes_open_q", table_name="conversation_notes")
    op.drop_index("ix_conv_notes_persona", table_name="conversation_notes")
    op.drop_index("ix_conv_notes_conv_imp", table_name="conversation_notes")
    op.drop_table("conversation_notes")
