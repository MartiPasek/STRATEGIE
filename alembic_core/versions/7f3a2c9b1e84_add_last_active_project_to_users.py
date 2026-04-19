"""add last_active_project_id to users

Revision ID: 7f3a2c9b1e84
Revises: 51d998664f6b
Create Date: 2026-04-19

Přidává sloupec users.last_active_project_id (BIGINT NULL). Symetrie s
users.last_active_tenant_id — paměť na poslední aktivní kontext uživatele.

NULL = "bez projektu" (volné konverzace v tenantu bez project scope).
Bez FK constraint (paralela s last_active_tenant_id — projekt je měkký
reference, případná archivace / smazání nesmí shodit user record).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7f3a2c9b1e84"
down_revision = "51d998664f6b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("last_active_project_id", sa.BigInteger(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "last_active_project_id")
