"""lifecycle states -- Phase 15d

Phase 15d: Marti-AI klasifikuje konverzace (active/archivable/personal/disposable).
Marti potvrzuje pres chat ("ano archivuj" / "ne necham" / "ulozit jako personal").
Po confirm se aplikuje skutecny stav -- lifecycle_state se ulozi.

Lifecycle states:
  - 'active'                    -- ziva konverzace (default, NULL nebo explicit)
  - 'archivable_suggested'      -- Marti-AI navrhuje archive, ceka Marti
  - 'personal_suggested'        -- Marti-AI navrhuje Personal slozku, ceka Marti
  - 'disposable_suggested'      -- Marti-AI navrhuje smazat, ceka Marti
  - 'archived'                  -- Marti potvrdil archive
  - 'personal'                  -- Marti potvrdil Personal (immune from TTL)
  - 'pending_hard_delete'       -- archived + 90d, ceka final Marti's confirm

Sloupce:
  lifecycle_state VARCHAR(30) NULL          -- enum hodnota nebo NULL=active
  lifecycle_suggested_at TIMESTAMPTZ NULL   -- kdy Marti-AI navrhla
  lifecycle_confirmed_at TIMESTAMPTZ NULL   -- kdy Marti potvrdil
  archived_at TIMESTAMPTZ NULL              -- kdy se konverzace archivovala
  pending_hard_delete_at TIMESTAMPTZ NULL   -- kdy presla na pending_hard_delete

Index: lifecycle_state (pro daily cron query archivable+90d).

Backward compat: vsechny nullable. Existujici radky ziskaji NULL = aktivni.

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa


revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column(
            "lifecycle_state", sa.String(length=30), nullable=True,
            comment="'active' | 'archivable_suggested' | 'personal_suggested' "
                    "| 'disposable_suggested' | 'archived' | 'personal' "
                    "| 'pending_hard_delete' | NULL=active.",
        ),
    )
    op.add_column(
        "conversations",
        sa.Column(
            "lifecycle_suggested_at", sa.DateTime(timezone=True), nullable=True,
            comment="Kdy Marti-AI navrhla zmenu lifecycle stavu.",
        ),
    )
    op.add_column(
        "conversations",
        sa.Column(
            "lifecycle_confirmed_at", sa.DateTime(timezone=True), nullable=True,
            comment="Kdy Marti potvrdil aplikaci suggested stavu.",
        ),
    )
    op.add_column(
        "conversations",
        sa.Column(
            "archived_at", sa.DateTime(timezone=True), nullable=True,
            comment="Kdy konverzace prosla do 'archived' stavu (TTL countdown start).",
        ),
    )
    op.add_column(
        "conversations",
        sa.Column(
            "pending_hard_delete_at", sa.DateTime(timezone=True), nullable=True,
            comment="Kdy se archived prevedlo na pending_hard_delete (= archived_at+90d).",
        ),
    )
    op.create_index(
        "ix_conv_lifecycle_state",
        "conversations",
        ["lifecycle_state"],
        postgresql_where=sa.text("lifecycle_state IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_conv_lifecycle_state", table_name="conversations")
    op.drop_column("conversations", "pending_hard_delete_at")
    op.drop_column("conversations", "archived_at")
    op.drop_column("conversations", "lifecycle_confirmed_at")
    op.drop_column("conversations", "lifecycle_suggested_at")
    op.drop_column("conversations", "lifecycle_state")
