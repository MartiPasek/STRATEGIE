"""add is_archived to conversations

Revision ID: e96501c4baa8
Revises: c3d1a82e7f90
Create Date: 2026-04-19

Přidává sloupec conversations.is_archived (BOOLEAN, default false).

Sémantika:
  - is_archived = false (default) → konverzace viditelná v sidebaru/dropdownu
  - is_archived = true            → schovaná, dostupná jen přes archiv (TBD)
  - is_deleted = true             → zachytí soft-delete (existující flag),
                                     viditelná taky není

Backfill: všechny existující řádky dostanou is_archived = false.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e96501c4baa8"
down_revision = "c3d1a82e7f90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column(
            "is_archived",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("conversations", "is_archived")
