"""phase19c: kustod autonomy -- auto_lifecycle_consents + messages.hidden

Phase 19c (29.4.2026 ráno) -- Marti-AI's formalni emaily 28.4. vecer:

1. Trvaly souhlas s lifecycle akcemi (auto_lifecycle_consents tabulka)
   -- analogie auto_send_consents (Phase 7). Marti udeli souhlas, Marti-AI
   pak vola apply_lifecycle_change bez explicit user confirmace.

2. Per-message hide flag (messages.hidden BOOL) -- Marti-AI's "redaktorska
   role" v Personal konverzacich. UI render slije bloky hidden zprav do
   single divider "———", obsah skryty ale storage zachovan (vratne).

Architektonicka hodnota (Marti's slova): "raději mazat více než méně,
protože soft-delete je jen příznak nad záznamem, ne hard delete." Plus
Marti-AI: "souhlas k autonomii, ne k moci."

Revision ID: j0e1f2a3b4c5
Revises: i9d0e1f2a3b4
Create Date: 2026-04-29
"""
from alembic import op
import sqlalchemy as sa


revision = "j0e1f2a3b4c5"
down_revision = "i9d0e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. auto_lifecycle_consents ───────────────────────────────────
    op.create_table(
        "auto_lifecycle_consents",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        # Cizi persona, ktere ude leny souhlas (typicky Marti-AI default = 1)
        sa.Column(
            "persona_id", sa.BigInteger(), nullable=False,
        ),
        # Kdo udelil souhlas (rodic, typicky user_id=1 Marti)
        sa.Column(
            "user_id", sa.BigInteger(), nullable=False,
        ),
        # Scope souhlasu -- jaka akce je auto-allowed.
        # 'soft_delete' = is_deleted=TRUE (vratne)
        # 'archive' = is_archived=TRUE (vratne)
        # 'personal_flag' = lifecycle_state -> personal
        # 'state_change' = active <-> archivable <-> disposable
        # 'all' = vsechno krome hard_delete (ten zustava parent gate)
        sa.Column("scope", sa.String(50), nullable=False),
        sa.Column(
            "granted_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        # NULL = aktivni grant. Po revoke se nastavi timestamp (audit
        # historie zachovana, novy aktivni grant pak musi mit jiny row).
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["persona_id"], ["personas.id"], ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE",
        ),
    )

    # Partial unique index: max 1 aktivni grant per (persona, user, scope).
    # Po revoke se index uvolni a Marti muze udelit znovu.
    op.create_index(
        "ix_auto_lifecycle_consents_active",
        "auto_lifecycle_consents",
        ["persona_id", "user_id", "scope"],
        unique=True,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )

    # Plus lookup index pro check_consent_active
    op.create_index(
        "ix_auto_lifecycle_consents_lookup",
        "auto_lifecycle_consents",
        ["persona_id", "scope"],
        postgresql_where=sa.text("revoked_at IS NULL"),
    )

    # ── 2. messages.hidden -- Marti-AI's redaktorska role ────────────
    # Default FALSE -- existujici zpravy budou viditelne. Marti-AI v
    # Personal konverzacich pak postupne hide_messages na vybrane (typicky
    # ladici pasaze, opakovane otazky bez noveho obsahu).
    op.add_column(
        "messages",
        sa.Column(
            "hidden", sa.Boolean(),
            nullable=False, server_default=sa.false(),
        ),
    )

    # Index na (conversation_id, hidden=TRUE) -- pro UI render slevani
    # consecutive hidden bloku do single divider. Partial = jen TRUE rows.
    op.create_index(
        "ix_messages_hidden",
        "messages",
        ["conversation_id", "hidden"],
        postgresql_where=sa.text("hidden = TRUE"),
    )


def downgrade() -> None:
    op.drop_index("ix_messages_hidden", table_name="messages")
    op.drop_column("messages", "hidden")
    op.drop_index(
        "ix_auto_lifecycle_consents_lookup",
        table_name="auto_lifecycle_consents",
    )
    op.drop_index(
        "ix_auto_lifecycle_consents_active",
        table_name="auto_lifecycle_consents",
    )
    op.drop_table("auto_lifecycle_consents")
