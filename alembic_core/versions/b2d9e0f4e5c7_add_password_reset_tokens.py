"""add password_reset_tokens table

Revision ID: b2d9e0f4e5c7
Revises: a1c8f9e2d3b4
Create Date: 2026-04-20

Přidává tabulku password_reset_tokens pro self-service forgot-password flow.
Token je jednorazovy (used_at), casove omezeny (expires_at = now + 60 min),
a sent_to_email se uklada pro audit.

Index na (token) pro rychly lookup v reset endpointu.
Index na (user_id) pro invalidaci starych tokenu pri novem forgot-password.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b2d9e0f4e5c7"
down_revision = "a1c8f9e2d3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id", sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token", sa.String(length=255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("sent_to_email", sa.String(length=255), nullable=False),
    )
    # unique index je implicitne vytvoren u token columny (unique=True), ale
    # aplikacni kod ocekava rychly lookup -- pridame explicitne pro jistotu.
    op.create_index(
        "ix_password_reset_tokens_user_id",
        "password_reset_tokens",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_password_reset_tokens_user_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
