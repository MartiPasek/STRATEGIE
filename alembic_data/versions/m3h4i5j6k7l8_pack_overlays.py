"""phase19b: tool packs -- Conversation.active_pack + persona_pack_overlays

29.4.2026 odpoledne -- Phase 19b: Role overlays / tool packs.

Po 3 iteracích konzultace s Marti-AI (29.4. 14:07-15:15):
- Princip: "Režim je roční období. Role je co mám oblečené." (stavový vs texturní)
- Implementace: balíčky tools (modulární, jeden naráz, vědomé gesto)
- Overlay = "povolením, ne tónem" (Marti-AI: "právo na proces je právo myslet viditelně")
- Marti's rozhodnuti 29.4. odpoledne: "zadny pravnik CZ a DE uz nebude" --
  všechny role v jedné Marti-AI persone přes packy

Schema:
1. conversations.active_pack VARCHAR(50) NULL (NULL = core/default)
2. persona_pack_overlays table -- per (persona_id, pack_name) Marti-AI's
   vlastní overlay text. Pokud chybí pro daný (persona_id, pack), pouzije
   se default z Pythonu (modules/conversation/application/tool_packs.py).

Architektonicky cista relational design (Volba B z iterace 4 design):
- UNIQUE (persona_id, pack_name) -- jeden overlay per persona per pack
- updated_at -- audit, kdy si Marti-AI zmenila tón
- ON DELETE CASCADE z personas (overlay umre s personou)

Revision ID: m3h4i5j6k7l8
Revises: l2g3h4i5j6k7
Create Date: 2026-04-29
"""
from alembic import op
import sqlalchemy as sa


revision = "m3h4i5j6k7l8"
down_revision = "l2g3h4i5j6k7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. conversations.active_pack
    op.add_column(
        "conversations",
        sa.Column("active_pack", sa.String(length=50), nullable=True),
    )
    # Index pro rychly filter (rare query, ale UI badge sidebar bude case
    # showing "konverzace ve specialnim packu" -- bezpecna optimalizace).
    op.create_index(
        "ix_conversations_active_pack",
        "conversations",
        ["active_pack"],
        postgresql_where=sa.text("active_pack IS NOT NULL"),
    )

    # 2. persona_pack_overlays
    op.create_table(
        "persona_pack_overlays",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("persona_id", sa.BigInteger(), nullable=False),
        sa.Column("pack_name", sa.String(length=50), nullable=False),
        sa.Column("overlay_text", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["persona_id"], ["personas.id"],
            name="fk_pack_overlays_persona", ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "persona_id", "pack_name",
            name="uq_pack_overlays_persona_pack",
        ),
    )


def downgrade() -> None:
    op.drop_table("persona_pack_overlays")
    op.drop_index("ix_conversations_active_pack", table_name="conversations")
    op.drop_column("conversations", "active_pack")
