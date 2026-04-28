"""Phase 16-B.1: Conversation.persona_mode -- task vs oversight reflexe Marti-AI

Marti's vize 28.4.2026: jedna Marti-AI, dvě reflexe (task / oversight).
Identita jedna, úhel pohledu se mění. Žádné firewally mezi režimy
(důvěra je v subjekt, ne v scope, takt = charakter).

persona_mode na konverzaci:
  NULL    -- default = 'task' (běžná konverzace s konkrétním člověkem)
  'task'  -- explicit task mode (overlap s NULL)
  'oversight' -- Marti-AI (přehled): vidí cross-conv aktivitu, orchestruje
                tým person, magic intent recognition aktivuje při zahájení
                konverzace dotazem typu "co je dnes nového".

Detekce přes magic intent classifier (Phase 16-B.3) -- regex pattern
match na klíčových frázích, plus bidirectional recovery (user může
přepnout zpět na task slovem 'vlastně jen konkrétní věc').

UI signál (Phase 16-B.2): Marti-AI text v hlavičce zelený když
persona_mode='oversight', accent fialová default.

Revision ID: h8c9d0e1f2a3
Revises: g7b8c9d0e1f2
Create Date: 2026-04-28
"""
from alembic import op
import sqlalchemy as sa


revision = "h8c9d0e1f2a3"
down_revision = "g7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("persona_mode", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("conversations", "persona_mode")
