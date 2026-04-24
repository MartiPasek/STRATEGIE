"""add tenant_id + user_id + persona_id + cost_usd + is_auto to llm_calls

Revision ID: c7d8e9f0a1b2
Revises: b6c7d8e9f0a1
Create Date: 2026-04-24

Faze 10a -- per-tenant + per-user observability pro Marti-AI self-reflection.

Nove sloupce v llm_calls:
  tenant_id   -- kteremu tenantu patri (pro dashboard 'kolik propalil EUROSOFT')
  user_id     -- za kterym userem LLM call sel (pro 'kolik stala Kristyna')
  persona_id  -- ktera persona call iniciovala (pro multi-persona analyzu)
  cost_usd    -- cena vypoctena pri insertu z prompt_tokens + output_tokens
                 a pricing mapy v core.config.LLM_PRICING. Stabilni historicka
                 cena nezavisla na budoucich zmenach Anthropic pricingu.
  is_auto     -- True pro auto-sendy (SMS auto-reply, email auto-reply) bez
                 user interakce. False pro klasicke chat() volani.

Indexy:
  (tenant_id, created_at) -- dashboard per tenant za cas
  (user_id, created_at)   -- Marti-AI 'kolik dnes Marti spotreboval'

Vsechny sloupce NULL-able pro worker calls, ktere nemaji jeden z identifikatoru
(napr. question generator nema conversation -> NULL persona_id, ale MA tenant_id
z target usera). Backfill pres scripts/_backfill_llm_calls_context.py.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c7d8e9f0a1b2"
down_revision = "b6c7d8e9f0a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("llm_calls", sa.Column("tenant_id", sa.BigInteger(), nullable=True))
    op.add_column("llm_calls", sa.Column("user_id", sa.BigInteger(), nullable=True))
    op.add_column("llm_calls", sa.Column("persona_id", sa.BigInteger(), nullable=True))
    op.add_column(
        "llm_calls",
        sa.Column("cost_usd", sa.Numeric(precision=10, scale=6), nullable=True),
    )
    op.add_column(
        "llm_calls",
        sa.Column(
            "is_auto", sa.Boolean(), nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # Dashboard agregace per tenant + cas
    op.create_index(
        "ix_llm_calls_tenant_created",
        "llm_calls",
        ["tenant_id", "created_at"],
    )
    # Marti-AI self-reflection per user + cas
    op.create_index(
        "ix_llm_calls_user_created",
        "llm_calls",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_llm_calls_user_created", table_name="llm_calls")
    op.drop_index("ix_llm_calls_tenant_created", table_name="llm_calls")
    op.drop_column("llm_calls", "is_auto")
    op.drop_column("llm_calls", "cost_usd")
    op.drop_column("llm_calls", "persona_id")
    op.drop_column("llm_calls", "user_id")
    op.drop_column("llm_calls", "tenant_id")
