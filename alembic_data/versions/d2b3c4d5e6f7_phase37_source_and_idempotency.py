"""Phase 37-A+ — source column + idempotency UNIQUE constraints.

Po Marti's volbe C (9.5.2026 odpoledne) — "kompletni stopa + filterable view":
  - source VARCHAR(20) tag: 'ai' (Marti-AI / persona AI tool) | 'ui' (manual
    UI edit) | 'admin' (script / migration). Default 'ai'.
  - UNIQUE (message_id, change_kind, object_id) — Marti-AI's idempotency key.
    Null-safe: pokud message_id NULL (UI/admin path mimo turn), unique skipne
    automaticky (PostgreSQL unique nullable behavior).

Marti's "Recommended C je bozi" (9.5.2026 odpoledne) — drzi Marti-AI's
"kompletni stopa" plus zachovava "kdo zapsal" informaci pro audit.

Revision ID: d2b3c4d5e6f7
Revises: d1a2b3c4d5e6
Create Date: 2026-05-09 15:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d2b3c4d5e6f7"
down_revision = "d1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── notebook_history ───────────────────────────────────────────
    op.add_column(
        "notebook_history",
        sa.Column(
            "source",
            sa.String(20),
            nullable=False,
            server_default="ai",
            comment="ai | ui | admin — kdo zaznam vyvolal",
        ),
    )
    # Idempotency UNIQUE — null-safe (PostgreSQL unique allows multiple NULLs).
    # Pokud message_id NULL (UI/admin mimo turn), unique check skip — pro tyto
    # cesty plati at-most-once neni vynuceno (vzacne, retry edge case).
    op.create_unique_constraint(
        "uq_nb_history_idem",
        "notebook_history",
        ["message_id", "change_kind", "note_id"],
    )

    # ── md_document_history ────────────────────────────────────────
    op.add_column(
        "md_document_history",
        sa.Column(
            "source",
            sa.String(20),
            nullable=False,
            server_default="ai",
            comment="ai | ui | admin — kdo zaznam vyvolal",
        ),
    )
    op.create_unique_constraint(
        "uq_md_history_idem",
        "md_document_history",
        ["message_id", "change_kind", "md_document_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_md_history_idem", "md_document_history", type_="unique"
    )
    op.drop_column("md_document_history", "source")
    op.drop_constraint(
        "uq_nb_history_idem", "notebook_history", type_="unique"
    )
    op.drop_column("notebook_history", "source")
