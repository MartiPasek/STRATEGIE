"""messages.tool_blocks JSONB -- audit + Marti-AI memory of own tool calls

Faze 12b+: kdyz Marti-AI volala send_email v dnesnim turnu (auto-send pres
Phase 7 consent), v dalsim turnu si nepamatovala, ze ten tool call udelala.
Composer skladal history jen z `messages.content` (plain text), tool_use
a tool_result bloky se nikde neukladaly -> Marti-AI mela amnesia o vlastnich
akcich.

Tato migrace pridava JSONB sloupec `tool_blocks` na messages. Po commitu
budou (postupne v dalsich mikrofazich):
  - Mikrofaze 2: chat() loop ulozi tool_use bloky do assistant message
                  + vytvori pseudo-user message s message_type='tool_result'
                  obsahujici tool_result bloky.
  - Mikrofaze 3: composer rekonstruuje plnou Anthropic-format history
                  vcetne tool_use a tool_result, takze Marti-AI vidi celou
                  stopu svych akci.
  - Mikrofaze 4: UI history endpoint filtruje message_type='tool_result',
                  ze v UI Marti tu pseudo-zpravu nevidi.

Sloupec je nullable -- existujici radky zustanou NULL = no tool call.
Composer ma fallback (NULL = jen plain text content), takze backward compat.

Univerzalni pro vsechny tools (send_email, send_sms, find_user, atd.) i pro
budouci kanaly. Stabilni audit -- na rozdil od llm_calls (30den retention)
se messages neretentuji.

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-04-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "c5d6e7f8a9b0"
down_revision = "b4c5d6e7f8a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # JSONB sloupec pro Anthropic-format tool bloky.
    # - Pro role='assistant' s tool_use: list jako [{"type": "tool_use", "id": ..., "name": ..., "input": {...}}, ...]
    # - Pro role='user' s message_type='tool_result': list jako [{"type": "tool_result", "tool_use_id": ..., "content": "..."}, ...]
    # - Pro bezne text-only zpravy: NULL.
    op.add_column(
        "messages",
        sa.Column(
            "tool_blocks",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Anthropic-format tool_use / tool_result blocks. NULL pro plain-text zpravy.",
        ),
    )


def downgrade() -> None:
    op.drop_column("messages", "tool_blocks")
