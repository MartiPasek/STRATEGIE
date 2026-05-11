"""Phase 38.4 (11.5.2026 vecer): erp_user_tabs.pinned + last_accessed_at

Marti's request: pinned záložky se mají pamatovat napříč F5 reloadem.
Persistence per user/tenant do data_db, write-through z frontendu.

  - pinned BOOL NOT NULL DEFAULT FALSE
       (right-click toggle pin/unpin; 📌 vpravo místo × close icon)
  - last_accessed_at TIMESTAMPTZ NULL
       (bumped při switchTab — LRU ordering pro overflow eviction)

Revision ID: i7g8h9i0j1k2
Revises: h6f7a8b9c0d1
Create Date: 2026-05-11
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "i7g8h9i0j1k2"
down_revision = "h6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "erp_user_tabs",
        sa.Column("pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "erp_user_tabs",
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("erp_user_tabs", "last_accessed_at")
    op.drop_column("erp_user_tabs", "pinned")
