"""add EWS fields to users

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-04-21

Per-user EWS kanal -- pro "posli z moji schranky" scenar.

MVP = flat fields na `users` tabulce (jeden email per user). Pokud by nekdy
user mel potrebovat vic schranek (pracovni + osobni), refactor na
user_channels tabulku (paralela persona_channels).

Fields:
  ews_email                -- login / UPN, pro Exchange autentizaci
  ews_password_encrypted   -- Fernet-encrypted heslo
  ews_server               -- EWS server URL
  ews_display_email        -- primary SMTP alias pro prezentaci (From: header).
                              NULL -> fallback na ews_email.

Vsechno nullable. User bez tehle konfigurace proste nemuze "posilat z moji".
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("ews_email", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("ews_password_encrypted", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("ews_server", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("ews_display_email", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "ews_display_email")
    op.drop_column("users", "ews_server")
    op.drop_column("users", "ews_password_encrypted")
    op.drop_column("users", "ews_email")
