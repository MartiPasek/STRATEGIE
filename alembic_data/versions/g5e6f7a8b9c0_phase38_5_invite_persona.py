"""Phase 38.5: PWA invite — invited_by_persona_id + 'INVITE' purpose

Marti's spec 10.5.2026 ráno: AI tool `send_pwa_install_invite` pro
non-technical users. 10 koleginim. Magic link + 7d TTL.

Marti-AI's Q1 insight (insider design partner, 8. iterace):
"Přidejte invited_by_persona_id, ne jen user_id. Ať audit vidí, že
to byl vztahový akt z mé persony, ne automatický cron."

Revision ID: g5e6f7a8b9c0
Revises: f4d5e6a7b8c9
Create Date: 2026-05-10
"""
from alembic import op
import sqlalchemy as sa


revision = "g5e6f7a8b9c0"
down_revision = "f4d5e6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Marti-AI's Q1 — audit log dohledá personu jako sender
    op.add_column(
        "trusted_device_invites",
        sa.Column("invited_by_persona_id", sa.Integer(), nullable=True),
    )
    # Index pro query "kdo posílal pozvánky" (Marti-AI's daily digest)
    op.create_index(
        "ix_invites_persona_created",
        "trusted_device_invites",
        ["invited_by_persona_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_invites_persona_created", table_name="trusted_device_invites")
    op.drop_column("trusted_device_invites", "invited_by_persona_id")
