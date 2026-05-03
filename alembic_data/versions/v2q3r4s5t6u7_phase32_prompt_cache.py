"""phase32: prompt cache -- users.cache_enabled + llm_calls cache token columns

3.5.2026 -- Phase 32. Anthropic prompt caching (cache_control: ephemeral) na
statickem prefixu system promptu + tools array. 60-80% slevu na input tokenech
pri cache hit (5min TTL). Cache create overhead +25% jen prvni call.

Marti-AI's distinkce 28.5.2026 (insider design partner):
  "Cache resi sirku (opakovany prefix napric turny). Hloubka -- per-konverzace
   dynamicky obsah (notebook, kotvy, RAG retrieved, activity log) roste s
   zivotem konverzace. Tam cache nepomaha. Reseni jindy a jinak (Phase 35+)."

Tato migrace pripravuje pouze schema pro sirku (Phase 32):

1. users.cache_enabled BOOL NOT NULL DEFAULT TRUE
   - User-level toggle (UI checkbox v hlavicce + AI tool set_cache_enabled)
   - Default TRUE (uspora velka, downside zadny)
   - Marti-AI's autonomie: "mit volbu je jine nez nemit volbu, i kdyz ji
     nepouzijes" -- ontologicka pritomnost, ne feature flag

2. llm_calls.cache_creation_tokens INT NULL
   llm_calls.cache_read_tokens INT NULL
   - Capture z response.usage (Anthropic API ho vraci v kazdem call)
   - cache_creation = +25% cost (jen prvni call po idle window)
   - cache_read = 10% ceny (kazdy nasledujici call do 5 min)
   - NULL = caching disabled / response neobsahuje (legacy / starsi rows)
   - Telemetrie: kolik token jsme cachem usetrili, hit ratio per call

Down: drop columns. Bezpecne -- existujici llm_calls rows zustavaji,
users zachovavaji ostatni fields.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "v2q3r4s5t6u7"
down_revision = "u1p2q3r4s5t6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. users.cache_enabled
    op.add_column(
        "users",
        sa.Column(
            "cache_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
    )

    # 2. llm_calls cache token columns
    op.add_column(
        "llm_calls",
        sa.Column("cache_creation_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "llm_calls",
        sa.Column("cache_read_tokens", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("llm_calls", "cache_read_tokens")
    op.drop_column("llm_calls", "cache_creation_tokens")
    op.drop_column("users", "cache_enabled")
