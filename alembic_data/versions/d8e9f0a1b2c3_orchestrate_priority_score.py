"""add priority_score to email_inbox + sms_inbox + thoughts (orchestrate mode)

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-04-25

Faze 11a -- orchestrate mode (mozek firmy).

Marti-AI v 'orchestrate mode' vraci Marti prehled nevyrizenych veci
napric 3 hlavnimi kanaly (email inbox, SMS inbox, todo list). User
rozhoduje interaktivne 'pojd na to / odloz / neres' -- prislusna akce
snizi priority_score na dane polozce, takze pri pristim prehledu klesne
dolu.

priority_score:
  Default 100 (nova polozka, nejvyssi priorita).
  'odloz'  -> -10 (priorita klesa, ale zustava v prehledu)
  'neres'  -> -30 (vyrazneji klesne, skoro na konci)
  Marti-AI po vyreseni nastavi processed_at / meta.done -> polozka
  z prehledu zmizi (neni pending).

Indexy: (priority_score DESC, created_at DESC) pro fast ORDER BY
v build_daily_overview query.

Plati na:
  email_inbox -- pending = processed_at IS NULL
  sms_inbox   -- pending = processed_at IS NULL
  thoughts    -- pending = type='todo' AND (meta::jsonb->>'done' IS NULL
                  OR meta::jsonb->>'done' != 'true') AND deleted_at IS NULL
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d8e9f0a1b2c3"
down_revision = "c7d8e9f0a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("email_inbox", "sms_inbox", "thoughts"):
        op.add_column(
            table,
            sa.Column(
                "priority_score", sa.Integer(), nullable=False,
                server_default="100",
            ),
        )
        # Sestupne podle skore + casu pro stabilne poradi.
        # Index name prefix: ix_<table>_priority
        op.create_index(
            f"ix_{table}_priority",
            table,
            [sa.text("priority_score DESC"), sa.text("created_at DESC")],
        )


def downgrade() -> None:
    for table in ("email_inbox", "sms_inbox", "thoughts"):
        op.drop_index(f"ix_{table}_priority", table_name=table)
        op.drop_column(table, "priority_score")
