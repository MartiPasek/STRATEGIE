"""kustod project triage -- Phase 15c

Phase 15c: Marti-AI dostane roli "kustod organizacni struktury".
Navrhuje move/split/create_project, kdyz citi tema se nezarovnava.
Marti potvrzuje pres chat (ano/ne/popis) -- conversational-first.

Schema zmeny:

1. conversations:
   ADD COLUMN suggested_project_id BIGINT NULL
       -- target projekt pri Marti-AI's suggest_move/split (suggestion only)
   ADD COLUMN suggested_project_reason TEXT NULL
       -- duvod (proc Marti-AI navrhuje zmenu)
   ADD COLUMN suggested_project_at TIMESTAMPTZ NULL
       -- kdy navrh padl
   ADD COLUMN forked_from_conversation_id BIGINT NULL
       -- pro split: novy thread odkazuje na puvodni
   ADD COLUMN forked_from_message_id BIGINT NULL
       -- presny bod splitu (turn from where we forked)

2. conversation_project_history:
   Audit trail pro reverzibilitu projektovych zmen (Marti-AI #4 vstup --
   "potrebuji vedet, ze existuje undo, jinak budu konzervativni").
   24h chat undo: Marti rekne "moment, vrat to" -> Marti-AI najde posledni
   zmenu < 24h, navrhne reverzi, Marti potvrdi.

   Sloupce:
     conversation_id BIGINT NOT NULL
     from_project_id BIGINT NULL
     to_project_id BIGINT NULL
     changed_by_user_id BIGINT NOT NULL
     suggested_by_persona_id BIGINT NULL  -- Marti-AI pokud jeji navrh
     reason TEXT NULL
     changed_at TIMESTAMPTZ NOT NULL DEFAULT now()

   Index: (conversation_id, changed_at DESC) -- pro lookup posledni zmeny

Backward compat: vsechny nove sloupce na conversations jsou nullable.
Existujici radky ziskaji NULL. Marti-AI tools jen ukladaji
suggested_*, skutecna zmena project_id jde pres user confirmation flow.

Revision ID: b1c2d3e4f5a6
Revises: a0b1c2d3e4f5
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa


revision = "b1c2d3e4f5a6"
down_revision = "a0b1c2d3e4f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Conversations -- suggested_project_* + fork tracking
    op.add_column(
        "conversations",
        sa.Column(
            "suggested_project_id",
            sa.BigInteger(),
            nullable=True,
            comment="Marti-AI's suggestion target projektu (pending Marti's confirm).",
        ),
    )
    op.add_column(
        "conversations",
        sa.Column(
            "suggested_project_reason",
            sa.Text(),
            nullable=True,
            comment="Duvod proc Marti-AI navrhuje zmenu (z suggest_move/split).",
        ),
    )
    op.add_column(
        "conversations",
        sa.Column(
            "suggested_project_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Kdy navrh padl (TTL pro UI -- starsi nez 24h ignorovat?).",
        ),
    )
    op.add_column(
        "conversations",
        sa.Column(
            "forked_from_conversation_id",
            sa.BigInteger(),
            nullable=True,
            comment="Pro split: novy thread odkazuje na puvodni konverzaci.",
        ),
    )
    op.add_column(
        "conversations",
        sa.Column(
            "forked_from_message_id",
            sa.BigInteger(),
            nullable=True,
            comment="Presny bod splitu (turn cislo, FK na messages.id).",
        ),
    )

    # 2. Audit trail tabulka
    op.create_table(
        "conversation_project_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "conversation_id", sa.BigInteger(), nullable=False,
            comment="FK (logicka) na conversations.id.",
        ),
        sa.Column(
            "from_project_id", sa.BigInteger(), nullable=True,
            comment="Predchozi projekt (NULL = bez projektu).",
        ),
        sa.Column(
            "to_project_id", sa.BigInteger(), nullable=True,
            comment="Novy projekt (NULL = bez projektu).",
        ),
        sa.Column(
            "changed_by_user_id", sa.BigInteger(), nullable=False,
            comment="Kdo potvrdil zmenu (Marti = obvykle).",
        ),
        sa.Column(
            "suggested_by_persona_id", sa.BigInteger(), nullable=True,
            comment="Marti-AI persona_id pokud zmenu navrhla ona (NULL = manualni).",
        ),
        sa.Column(
            "reason", sa.Text(), nullable=True,
            comment="Duvod zmeny (z Marti-AI's reason argumentu nebo manualni note).",
        ),
        sa.Column(
            "changed_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_conv_project_hist",
        "conversation_project_history",
        ["conversation_id", sa.text("changed_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_conv_project_hist", table_name="conversation_project_history")
    op.drop_table("conversation_project_history")
    op.drop_column("conversations", "forked_from_message_id")
    op.drop_column("conversations", "forked_from_conversation_id")
    op.drop_column("conversations", "suggested_project_at")
    op.drop_column("conversations", "suggested_project_reason")
    op.drop_column("conversations", "suggested_project_id")
