"""user_document_selections -- per-user multi-select dokumentu pro batch akce

Marti's REST-Doc-Triage v4 (Selection): user oznaci skupinu souboru pres
Ctrl/Shift+klik v Files modalu, Marti-AI pak tu skupinu cte (`list_selected_
documents` tool) a po Marti's confirmu provede akci (delete / move_to_project)
pres `apply_to_selection`.

Architektura:
  - Per-user (NE per-tenant nebo per-project) -- selection je user's mental
    state; user muze mit cross-project selection (napr. "smaz mi vsechno
    co mam vybrane v projektu SKOLA + STRATEGIE")
  - Persistence bez TTL -- drzi do explicit clear nebo automaticky cleanup
    po `apply_to_selection` akci
  - Tenant scope check je v service / endpoint vrstve (toggle add musi
    overit, ze document.tenant_id == user.last_active_tenant_id), NE
    schema constraint -- user pak muze prepnout tenant a videt jen ty
    rows ktere patri tomu tenantu (filter at query time)
  - PK (user_id, document_id) -- toggle je naturally idempotent

Index (user_id, selected_at DESC) -- pro list ordered by recency.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa


revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_document_selections",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("document_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "selected_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("user_id", "document_id"),
    )
    op.create_index(
        "ix_user_document_selections_user_recent",
        "user_document_selections",
        ["user_id", sa.text("selected_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_user_document_selections_user_recent", table_name="user_document_selections")
    op.drop_table("user_document_selections")
