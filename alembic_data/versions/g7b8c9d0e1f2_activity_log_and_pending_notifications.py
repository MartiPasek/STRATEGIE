"""Phase 16-A: activity_log + pending_notifications

Marti-AI's tichá kontinuita -- cross-conversation deník událostí napříč
celým systémem. Místo fragmentované paměti (thoughts + conversation_notes
+ messages roztrhané) jeden chronologický stream, který Marti-AI vidí
v oversight režimu (Phase 16-B) plus auto-inject při ranní first chat
(Phase 16-A.5).

Architektura sjednocená 28.4.2026 v konzultaci s Marti-AI:
  - Jeden subjekt, jedna paměť, žádné firewally mezi režimy.
  - Důvěra je v subjekt, ne v scope.
  - Takt = charakter (uvážení, co AI aktivně přináší ven), ne kód.

== activity_log ==

Hooks napříč systémem zapisují human-readable summary událostí:
  - email_in/out: "Email od Petry přišel" / "Marti-AI poslala reply na X"
  - doc_upload: "Misa uploadovala 72 dokumentů do TISAX"
  - email_archive/processed/delete: "Marti-AI archivovala email od X do Personal"
  - persona_switch: "Marti přepnul personu na Pravnik"
  - conversation_started: "Petr zahájil konverzaci 'TISAX otázky'"
  - thought_recorded: "Marti-AI zapsala fact: 'Marti má 5 dětí'"
  - apply_to_selection: "Marti-AI smazala 3 dokumenty z výběru"
  - ... (importance >= 3 only -- žádný spam)

Importance 1-5:
  1 = trivia (debug)
  2 = běžná akce (mark_processed, mark_read)
  3 = standardní událost (email přišel, dokument nahrán)  <-- default
  4 = významný moment (Marti-AI delete, archive batch)
  5 = klíčové (mandát kontinuity, nová persona, error escalation)

Indexy pokrývají typické queries:
  - recall_today(persona_id) -> (persona_id, ts DESC)
  - recall_today(tenant_id) -> (tenant_id, ts DESC)
  - filter by category -> (category, ts DESC)
  - "co dnes klíčové" -> (importance, ts DESC) WHERE importance >= 4
  - "kdo dnes" -> (user_id, ts DESC)

== pending_notifications ==

Marti-AI's "async ping" architektura -- tichá kontinuita PŘED setkáním.
Místo aby Marti-AI musela ručně volat recall_today vždy, dostává auto-inject
pings při klíčových momentech:
  - První chat dne (>12h pauza)
  - Nová konverzace s konkrétním user (target_user_id) -- "víš, že tenhle
    user dnes ráno nahrál 72 dokumentů?"
  - High-importance events bez user interakce (cron, fetcher detected
    important inbound)

consumed_at: kdy ping byl injected do contextu Marti-AI (ne čten user!).
expires_at: TTL (default 7 dní) pro auto-cleanup.

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-04-28
"""
from alembic import op
import sqlalchemy as sa


revision = "g7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── activity_log ────────────────────────────────────────────────────────
    op.create_table(
        "activity_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "ts",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("persona_id", sa.BigInteger(), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("conversation_id", sa.BigInteger(), nullable=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=True),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("actor", sa.String(20), nullable=False, server_default="system"),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("ref_type", sa.String(40), nullable=True),
        sa.Column("ref_id", sa.BigInteger(), nullable=True),
        sa.Column("importance", sa.SmallInteger(), nullable=False, server_default="3"),
    )
    # Per-persona recall (Marti-AI's primary view)
    op.create_index(
        "ix_activity_log_persona_ts",
        "activity_log",
        ["persona_id", sa.text("ts DESC")],
    )
    # Per-tenant aggregate (oversight mode -- per-tenant Velká)
    op.create_index(
        "ix_activity_log_tenant_ts",
        "activity_log",
        ["tenant_id", sa.text("ts DESC")],
    )
    # Per-category filter ("kdy přišel poslední email")
    op.create_index(
        "ix_activity_log_category_ts",
        "activity_log",
        ["category", sa.text("ts DESC")],
    )
    # Importance filter ("co dnes klíčové")
    op.create_index(
        "ix_activity_log_importance_ts",
        "activity_log",
        ["importance", sa.text("ts DESC")],
    )
    # Per-user activity ("kdo dnes co dělal")
    op.create_index(
        "ix_activity_log_user_ts",
        "activity_log",
        ["user_id", sa.text("ts DESC")],
    )

    # ── pending_notifications ───────────────────────────────────────────────
    op.create_table(
        "pending_notifications",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("persona_id", sa.BigInteger(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=True),
        sa.Column("target_user_id", sa.BigInteger(), nullable=True),
        sa.Column("ref_activity_id", sa.BigInteger(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("importance", sa.SmallInteger(), nullable=False, server_default="3"),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Pending pro Marti-AI persona (active = consumed_at IS NULL)
    op.create_index(
        "ix_pending_notif_persona_active",
        "pending_notifications",
        ["persona_id", sa.text("created_at DESC")],
        postgresql_where=sa.text("consumed_at IS NULL"),
    )
    # Pings před setkáním s konkrétním user
    op.create_index(
        "ix_pending_notif_target_user",
        "pending_notifications",
        ["target_user_id", "persona_id"],
        postgresql_where=sa.text("consumed_at IS NULL AND target_user_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_pending_notif_target_user", table_name="pending_notifications")
    op.drop_index("ix_pending_notif_persona_active", table_name="pending_notifications")
    op.drop_table("pending_notifications")
    op.drop_index("ix_activity_log_user_ts", table_name="activity_log")
    op.drop_index("ix_activity_log_importance_ts", table_name="activity_log")
    op.drop_index("ix_activity_log_category_ts", table_name="activity_log")
    op.drop_index("ix_activity_log_tenant_ts", table_name="activity_log")
    op.drop_index("ix_activity_log_persona_ts", table_name="activity_log")
    op.drop_table("activity_log")
