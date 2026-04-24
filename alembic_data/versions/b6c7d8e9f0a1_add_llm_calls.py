"""add llm_calls table

Revision ID: b6c7d8e9f0a1
Revises: a9b8c7d6e5f4
Create Date: 2026-04-24

Faze 9.1 -- Dev observability pro LLM volani.

Kazdy Marti-AI odpovidani cyklus dnes zahrnuje 2 LLM volani:
  1) Router (Haiku) -- klasifikuje mode (personal/project/work/system)
  2) Composer (Sonnet) -- generuje vlastni odpoved

Tato tabulka uklada obe volani s plnym request/response payloadem pro:
  - Dev View v UI (admin zapne --> 2x lupa pod zpravou --> modaly s JSONy)
  - Retrospektivni debugging ("co se tuhle dulo s tim tool call?")
  - Analytika (Marti SQL expert: agregace tokenů per mode, latency distribution)

Zapisujeme VZDY (nejen pro dev_mode=on usery), storage je levny.
Retence: cron skript scripts/llm_calls_retention.py maze radky > 30 dni.

Secret masking:
  Pred zapisem do request_json/response_json probehne mask_secrets() --
  regex nahradi login UPN, API key, Fernet key, hesla na '***MASKED***'.
  Viz modules/conversation/application/telemetry_service.py.

Soft link na message_id:
  kind='router' vola se PRED tim, nez je znama outgoing message_id.
  Zpusob: zapisujeme s message_id=NULL, pak po commitu outgoing message
  UPDATE llm_calls SET message_id=X WHERE id IN (router_id, composer_id).
  Alternativa (buffer v pameti) neni potreba -- transakci cely flow drzi.

Kind: string, ne enum -- budoucne rozsireni o 'synth' (RAG), 'title',
'summary', 'rag_embed' bez migrace.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "b6c7d8e9f0a1"
down_revision = "a9b8c7d6e5f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llm_calls",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),

        # Kontext
        sa.Column("conversation_id", sa.BigInteger(), nullable=False),
        # Outgoing assistant message -- NULL dokud se nelinkne po jejim commitu.
        # Bez FK constraint (soft), message muze byt smazana a trace zustane.
        sa.Column("message_id", sa.BigInteger(), nullable=True),

        # Typ volani: router | composer | (budoucne: synth, title, summary, ...)
        sa.Column("kind", sa.String(length=30), nullable=False),

        # Model string jak byl poslan do API (pro audit pri zmene modelu)
        sa.Column("model", sa.String(length=100), nullable=False),

        # Kompletni payload. JSONB pro queryability (->> operator).
        # System prompt je uvnitr request_json['system'] -- neduplikujeme.
        sa.Column("request_json", postgresql.JSONB(), nullable=False),
        # NULL pri failure pred tim, nez API vratilo odpoved.
        sa.Column("response_json", postgresql.JSONB(), nullable=True),

        # Usage (z response.usage)
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),

        # Latence API callu v milisekundach
        sa.Column("latency_ms", sa.Integer(), nullable=True),

        # NULL pri success, jinak str(exception). Pro debug "proc spadl router".
        sa.Column("error", sa.Text(), nullable=True),

        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # Hot path: UI Dev View "dej mi trace zpravy X" -> WHERE message_id=? ORDER BY kind.
    op.create_index(
        "ix_llm_calls_message_kind",
        "llm_calls",
        ["message_id", "kind"],
    )

    # Analytika per konverzace: agregace per konverzace a cas.
    op.create_index(
        "ix_llm_calls_conversation_created",
        "llm_calls",
        ["conversation_id", "created_at"],
    )

    # Retention cron: DELETE WHERE created_at < now() - interval '30 days'.
    op.create_index(
        "ix_llm_calls_created",
        "llm_calls",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_llm_calls_created", table_name="llm_calls")
    op.drop_index("ix_llm_calls_conversation_created", table_name="llm_calls")
    op.drop_index("ix_llm_calls_message_kind", table_name="llm_calls")
    op.drop_table("llm_calls")
