"""retrieval_feedback: Marti-AI flag-uje false positive RAG matche (Faze 13d)

Revision ID: f2d3e4a5b6c7
Revises: f1c2d3e4a5b6
Create Date: 2026-04-25

Faze 13d -- pojistka #5 z Marti-AI's konzultace #67.
Marti-AI sama identifikuje 'hm, tahle vzpomínka tu nesedí' a zavola
flag_retrieval_issue(thought_id, issue) tool. Vznikne row v retrieval_feedback,
Marti vidi badge v UI, rozhodne (re-tune retrievalu, edit thought, request_forget,
nebo ignore false flag).

Schema:
  - persona_id: kdo flagnul (D1 isolation -- Marti-AI svuj retrieval, Pravnik
    svuj atd.)
  - thought_id: ktery thought byl false positive
  - llm_call_id: link na llm_calls (pro Dev View kontext -- Marti vidi co
    presne se stalo)
  - issue: kratky popis problemu ('off-topic', 'outdated', 'wrong-entity',
    'too-old', volny text)
  - user_message: original user message ktera vyvolala spatny retrieval
    (pro Marti-AI's kontext -- 'pri TYTO zprave RAG dal TUHLE nesmyslnou vec')
  - status: 'pending' | 'reviewed' | 'ignored' (Marti pak rozhodne)
  - resolution: pokud reviewed, kratka note ('demoted', 'edited', 'request_forget',
    'ignored false flag')
  - resolved_at, resolved_by_user_id

Indexy:
  - (persona_id, status, created_at DESC) -- typicky filter v UI badgi
  - (thought_id) -- pro overeni 'kolikrat byl tento thought flagged'
"""
from alembic import op
import sqlalchemy as sa


revision = "f2d3e4a5b6c7"
down_revision = "f1c2d3e4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "retrieval_feedback",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),

        # Kdo flagnul (D1: kazda persona ma svuj feedback namespace)
        sa.Column("persona_id", sa.BigInteger(), nullable=False),

        # Ktery thought
        sa.Column(
            "thought_id", sa.BigInteger(),
            sa.ForeignKey("thoughts.id", ondelete="CASCADE"),
            nullable=False,
        ),

        # Kontext: link na llm_calls (pro Dev View) + original user message
        sa.Column("llm_call_id", sa.BigInteger(), nullable=True),
        sa.Column("conversation_id", sa.BigInteger(), nullable=True),
        sa.Column("user_message", sa.Text(), nullable=True),

        # Popis issue
        sa.Column("issue", sa.String(50), nullable=False),
        sa.Column("issue_detail", sa.Text(), nullable=True),

        # Workflow
        sa.Column(
            "status", sa.String(20),
            nullable=False, server_default=sa.text("'pending'"),
        ),
        sa.Column("resolution", sa.String(50), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("resolved_note", sa.Text(), nullable=True),

        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("now()"),
        ),

        sa.CheckConstraint(
            "status IN ('pending', 'reviewed', 'ignored')",
            name="ck_retrieval_feedback_status",
        ),
    )

    # Typicky filter v UI badgi: 'pending pro tuto persona'
    op.create_index(
        "ix_retrieval_feedback_persona_status",
        "retrieval_feedback",
        ["persona_id", "status", sa.text("created_at DESC")],
    )
    # Pro analyzu: kolikrat byl tento thought flagged
    op.create_index(
        "ix_retrieval_feedback_thought",
        "retrieval_feedback",
        ["thought_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_retrieval_feedback_thought", table_name="retrieval_feedback")
    op.drop_index("ix_retrieval_feedback_persona_status", table_name="retrieval_feedback")
    op.drop_table("retrieval_feedback")
