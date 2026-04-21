"""add tasks table and sms_inbox.processed_at

Revision ID: b5c6d7e8f0a1
Revises: a4b5c6d7e8f9
Create Date: 2026-04-21

Zavadi task-driven workflow nad prichozi komunikaci:

sms_inbox.processed_at:
  NULL     -- zprava lezi ve slozce "Prichozi" v UI
  NOT NULL -- vsechny souvisejici tasky jsou 'done', slozka "Zpracovane"

tasks:
  First-class entita pro jednotku prace AI persony. Vznika automaticky pri
  prichozi zprave (source_type='sms_inbox' | 'email_inbox') nebo manualne
  (source_type='manual'). Executor nad nim spusti AI loop v skryte conversation.

  Lifecycle: open -> in_progress -> done / cancelled / failed.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b5c6d7e8f0a1"
down_revision = "a4b5c6d7e8f9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── sms_inbox.processed_at ──────────────────────────────────────────────
    op.add_column(
        "sms_inbox",
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Hot path v UI: filtrovat Prichozi (processed_at IS NULL) vs Zpracovane.
    op.create_index(
        "ix_sms_inbox_persona_processed",
        "sms_inbox",
        ["persona_id", "processed_at"],
    )

    # ── tasks ───────────────────────────────────────────────────────────────
    op.create_table(
        "tasks",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=True),
        sa.Column("persona_id", sa.BigInteger(), nullable=True),

        # sms_inbox | email_inbox | manual | ai_generated
        sa.Column("source_type", sa.String(length=30), nullable=False),
        # weak reference na source table (bez FK constraintu kvuli flexibilite).
        sa.Column("source_id", sa.BigInteger(), nullable=True),

        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),

        sa.Column("status", sa.String(length=20), nullable=False,
                  server_default="open"),        # open | in_progress | done | cancelled | failed
        sa.Column("priority", sa.String(length=10), nullable=False,
                  server_default="normal"),      # high | normal | low
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),

        # Skryta conversation kde AI loop pracoval -- pro audit + UI drilldown.
        sa.Column("execution_conversation_id", sa.BigInteger(), nullable=True),

        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),

        # NULL = system/AI vytvoril, BigInteger = user_id ktery to zalozil rucne.
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=True),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
    )

    # Worker poll hot path: "WHERE status='open' ORDER BY created_at LIMIT N".
    # Skenuje se casto (kazdych 5s), musi byt rychle.
    op.create_index(
        "ix_tasks_status_created",
        "tasks",
        ["status", "created_at"],
    )
    # UI hot path: list tasku pro personu v tenantu, filtrovat podle statusu.
    op.create_index(
        "ix_tasks_persona_status",
        "tasks",
        ["tenant_id", "persona_id", "status"],
    )
    # Join zpetne ze zpravy na task: "vsechny tasky pro sms_inbox.id=X".
    op.create_index(
        "ix_tasks_source",
        "tasks",
        ["source_type", "source_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_tasks_source", table_name="tasks")
    op.drop_index("ix_tasks_persona_status", table_name="tasks")
    op.drop_index("ix_tasks_status_created", table_name="tasks")
    op.drop_table("tasks")

    op.drop_index("ix_sms_inbox_persona_processed", table_name="sms_inbox")
    op.drop_column("sms_inbox", "processed_at")
