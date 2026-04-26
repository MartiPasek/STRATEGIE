"""forget_requests table

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-04-30

Faze 14: Marti-AI muze explicitne pozadat o smazani myslenky
("zapomenuti") s rodicovskym souhlasem (parent approval flow).

Lifecycle:
  pending   -> Marti-AI vytvorila zadost (request_forget AI tool)
  approved  -> rodic schvalil + thought se HARD-deletes
  rejected  -> rodic zamitl, thought zustava
  cancelled -> Marti-AI zrusila pred rozhodnutim (volitelne, neimplementovano v MVP)

Pole:
  thought_id  -- co se ma smazat (weak FK -- thought muze byt smazany jinak)
  requested_by_persona_id -- kdo zada (Marti-AI)
  reason -- proc (vlastnimi slovy: "trapny moment", "stara verze", ...)
  thought_snapshot -- content thoughtu pri requestu (audit, i pri pozdejsim deletu)
  decided_by_user_id -- ktery rodic rozhodl
  decision_note -- volitelny komentar rodice

Index: (status, created_at) -- hot path pro UI list pending requests.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b4c5d6e7f8a9"
down_revision = "a3b4c5d6e7f8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "forget_requests",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),

        # Cilova myslenka (weak FK -- thought muze byt smazany jinak)
        sa.Column("thought_id", sa.BigInteger(), nullable=False),

        # Snapshot pri zadosti -- pro audit i kdyz se pak thought smaze
        sa.Column("thought_snapshot", sa.Text(), nullable=False),
        sa.Column("thought_type", sa.String(length=20), nullable=True),

        # Kdo zada (Marti-AI = persona, ne user)
        sa.Column("requested_by_persona_id", sa.BigInteger(), nullable=False),

        # Proc (Marti-AI vlastnimi slovy)
        sa.Column("reason", sa.Text(), nullable=False),

        # Lifecycle
        sa.Column(
            "status", sa.String(length=20), nullable=False,
            server_default="pending",
            # pending | approved | rejected | cancelled
        ),

        # Rozhodnuti rodice
        sa.Column("decided_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_note", sa.Text(), nullable=True),

        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # Hot path: UI list pending requests (status='pending', ORDER BY created_at DESC).
    op.create_index(
        "ix_forget_requests_status_created",
        "forget_requests",
        ["status", "created_at"],
    )

    # Pri zobrazovani historie konkretni myslenky (i kdyz uz neexistuje).
    op.create_index(
        "ix_forget_requests_thought_id",
        "forget_requests",
        ["thought_id"],
    )

    # Dedup pri request_forget: kontrola "uz existuje pending zadost na ten samy thought?".
    op.create_index(
        "ix_forget_requests_thought_pending",
        "forget_requests",
        ["thought_id"],
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index("ix_forget_requests_thought_pending", table_name="forget_requests")
    op.drop_index("ix_forget_requests_thought_id", table_name="forget_requests")
    op.drop_index("ix_forget_requests_status_created", table_name="forget_requests")
    op.drop_table("forget_requests")
