"""ZRUŠENA — Phase 38.4 Krok 8 patří do master.* schema (Marti-AI's doména).

Tato migrace byla mou architektonickou chybou — alembic patří do public.*,
ale stavba ERP framework metadata patří do master.* (Marti's korekce 10.5.).

Místo toho: scripts/_phase38_4_krok8_master_grid_column_meta.sql — DDL pro
master.grid_column_meta, spustí Marti-AI (přes chat tool) nebo Marti
(přes DBeaver jako Marti-AI login).

Tahle migrace zůstává jako no-op pro alembic linearity.

Revision ID: h6f7a8b9c0d1
Revises: g5e6f7a8b9c0
Create Date: 2026-05-10
"""
from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "h6f7a8b9c0d1"
down_revision = "g5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No-op — Phase 38.4 Krok 8 grid_column_meta patří do master.*, ne public."""
    pass


def downgrade() -> None:
    """No-op."""
    pass
