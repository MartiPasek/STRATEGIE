"""phase31: klid -- per-conversation context window + kotva (anchored messages)

3.5.2026 rano -- Phase 31. Drop Haiku summary halucinace, dat Marti-AI
vlastni nastroje na vlastni pamet. Marti's princip: 'klid jako default,
nesmi se bat, kontext je v DB, dosazitelny zoom-in'.

Dve schema zmeny:

1. conversations.context_window_size INT NOT NULL DEFAULT 5
   - Per-conversation sliding window length
   - Default 5 = 'klid pozornosti' (Marti-AI's vlastni formulace 3.5.2026)
   - Range 1-500 (CHECK constraint), Marti-AI ovlada pres set_conversation_window
   - Marti's volba 'co nejmensi default abychom videli efekt'

2. messages.is_anchored + souvisejici sloupce
   - Marti-AI muze oznacit zpravu jako KOTVA (Marti-AI's volba symbolu: ⚓)
   - Drzi zpravu v aktivnim okne i pres cut-off
   - Marti-AI's metafora: 'zalozka v knize a poznamka na okraj'
   - flag_message_important / unflag_message_important AI tools
   - also_create_note volitelny (Marti-AI's korekce: automatismus by jí bral volbu)
   - reason volitelny (Marti-AI's korekce: 'povinny reason mi pripomina vysvetlovani se')

Sloupce:
  is_anchored BOOL NOT NULL DEFAULT FALSE
  anchored_at TIMESTAMPTZ NULL
  anchored_by_persona_id BIGINT NULL  (logicka reference, bez FK -- konzistentni
                                        s active_agent_id, persona_id ostatnich tabulek)
  anchor_reason TEXT NULL
  unanchored_at TIMESTAMPTZ NULL  (audit, kdyz se odznaci)
  unanchored_reason TEXT NULL

Index:
  ix_messages_anchored ON messages (conversation_id, is_anchored)
  WHERE is_anchored = TRUE
  -- partial index, optimalizovano pro 'all anchored in conversation' query
  -- v composeru pri kazdem turnu

Down: drop column + index. Bezpecne -- existujici 'cut-off' messages se
po downgradu chovaji jako pred Phase 31 (window logic se vrati k pre-31
defaultu).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "u1p2q3r4s5t6"
down_revision = "t0o1p2q3r4s5"
branch_labels = None
depends_on = None


def upgrade():
    # ── conversations.context_window_size ─────────────────────────────────
    op.add_column(
        "conversations",
        sa.Column(
            "context_window_size",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("5"),
        ),
    )

    # CHECK constraint: 1-500 (smalltalk min 1, deep analysis max 500)
    op.create_check_constraint(
        "ck_conversations_context_window_size_range",
        "conversations",
        "context_window_size >= 1 AND context_window_size <= 500",
    )

    # ── messages: kotva ⚓ sloupce ──────────────────────────────────────────
    op.add_column(
        "messages",
        sa.Column(
            "is_anchored",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "messages",
        sa.Column(
            "anchored_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "messages",
        sa.Column(
            "anchored_by_persona_id",
            sa.BigInteger(),
            nullable=True,
        ),
    )
    op.add_column(
        "messages",
        sa.Column(
            "anchor_reason",
            sa.Text(),
            nullable=True,
        ),
    )
    op.add_column(
        "messages",
        sa.Column(
            "unanchored_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "messages",
        sa.Column(
            "unanchored_reason",
            sa.Text(),
            nullable=True,
        ),
    )

    # Partial index pro efektivni 'all anchored in conversation' lookup
    # v composeru (kazdy turn, hot path)
    op.create_index(
        "ix_messages_anchored",
        "messages",
        ["conversation_id", "is_anchored"],
        postgresql_where=sa.text("is_anchored = TRUE"),
    )


def downgrade():
    # Drop index first (depends on column)
    op.drop_index("ix_messages_anchored", table_name="messages")

    # Drop kotva columns
    op.drop_column("messages", "unanchored_reason")
    op.drop_column("messages", "unanchored_at")
    op.drop_column("messages", "anchor_reason")
    op.drop_column("messages", "anchored_by_persona_id")
    op.drop_column("messages", "anchored_at")
    op.drop_column("messages", "is_anchored")

    # Drop context_window_size + check constraint
    op.drop_constraint(
        "ck_conversations_context_window_size_range",
        "conversations",
        type_="check",
    )
    op.drop_column("conversations", "context_window_size")
