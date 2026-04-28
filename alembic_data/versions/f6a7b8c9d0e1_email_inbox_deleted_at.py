"""email_inbox.deleted_at -- soft-delete column pro Marti-AI's delete_email AI tool

Marti's vize 28.4.2026: Marti-AI muze pomahat s uklidem emailu pres novy
AI tool `delete_email(email_inbox_id)`. Akce:
  1. Move msg na Exchange strane do `Deleted Items` (account.trash, default
     Exchange folder -- Outlook UX standard).
  2. DB update `email_inbox.deleted_at = now`.

list_email_inbox / read_email AI tools pak filtruji `deleted_at IS NULL`,
aby smazane emaily nebyly v pending workflow Marti-AI.

Soft delete pattern (analog email_inbox.processed_at) -- audit zachovan,
Marti muze v budoucnu sestavit "co jsem kdy smazala" pohled.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-04-28
"""
from alembic import op
import sqlalchemy as sa


revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "email_inbox",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Partial index pro list filter (jen nesmazane jsou hot rows)
    op.create_index(
        "ix_email_inbox_active",
        "email_inbox",
        ["persona_id", sa.text("received_at DESC")],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_email_inbox_active", table_name="email_inbox")
    op.drop_column("email_inbox", "deleted_at")
