"""phase18: cross-DB FK constraints (po pg_dump merge css_db -> data_db)

Phase 18 (29.4.2026 ráno) -- po sjednocení css_db + data_db do data_db
přes pg_dump --schema-only + --data-only --column-inserts. Schema z
css_db (21 tabulek) je teď v data_db jako native tabulky. Tato migrace
už jen přidá 4 cross-DB FK constraints, které dosud nešly udělat
(PostgreSQL nepodporuje cross-database FK).

Plus přidá `documents.project_id → projects.id` ON DELETE SET NULL --
to je Phase 16-B.9 finally (28.4. odpoledne TODO).

Revision ID: i9d0e1f2a3b4
Revises: h8c9d0e1f2a3
Create Date: 2026-04-29
"""
from alembic import op
import sqlalchemy as sa


revision = "i9d0e1f2a3b4"
down_revision = "h8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. conversations.tenant_id → tenants.id (SET NULL) ─────────────
    # Konverzace patří tenantu; po smazání tenantu zůstává konverzace
    # historicky (s NULL), ne CASCADE delete.
    op.create_foreign_key(
        "fk_conversations_tenant_id",
        "conversations", "tenants",
        ["tenant_id"], ["id"],
        ondelete="SET NULL",
    )

    # ── 2. conversations.created_by_user_id → users.id (SET NULL) ──────
    # Audit kdo konverzaci založil; po user delete zachovat record.
    op.create_foreign_key(
        "fk_conversations_created_by_user_id",
        "conversations", "users",
        ["created_by_user_id"], ["id"],
        ondelete="SET NULL",
    )

    # ── 3. conversations.active_agent_id → personas.id (SET NULL) ──────
    # Aktivní persona v konverzaci; po smazání persony zůstává konverzace,
    # ale active_agent_id NULL (orphaned konverzace bude default Marti-AI
    # při dalším otevření).
    op.create_foreign_key(
        "fk_conversations_active_agent_id",
        "conversations", "personas",
        ["active_agent_id"], ["id"],
        ondelete="SET NULL",
    )

    # ── 4. documents.project_id → projects.id (SET NULL) -- PHASE 16-B.9 ─
    # Phase 16-B.9 z 28.4. byla blocked na cross-DB FK. Po Phase 18 merge
    # konečně možná. ON DELETE SET NULL = po smazání projektu dokumenty
    # spadnou do inboxu (project_id IS NULL), ne CASCADE delete.
    op.create_foreign_key(
        "fk_documents_project_id",
        "documents", "projects",
        ["project_id"], ["id"],
        ondelete="SET NULL",
    )

    # ── 5. messages.tenant_id → tenants.id (SET NULL) ─────────────────
    op.create_foreign_key(
        "fk_messages_tenant_id",
        "messages", "tenants",
        ["tenant_id"], ["id"],
        ondelete="SET NULL",
    )

    # ── 6. messages.project_id → projects.id (SET NULL) ───────────────
    op.create_foreign_key(
        "fk_messages_project_id",
        "messages", "projects",
        ["project_id"], ["id"],
        ondelete="SET NULL",
    )

    # ── 7. messages.agent_id → personas.id (SET NULL) ─────────────────
    op.create_foreign_key(
        "fk_messages_agent_id",
        "messages", "personas",
        ["agent_id"], ["id"],
        ondelete="SET NULL",
    )

    # ── 8. messages.author_user_id → users.id (SET NULL) ──────────────
    op.create_foreign_key(
        "fk_messages_author_user_id",
        "messages", "users",
        ["author_user_id"], ["id"],
        ondelete="SET NULL",
    )

    # ── 9. documents.tenant_id → tenants.id (SET NULL) ────────────────
    op.create_foreign_key(
        "fk_documents_tenant_id",
        "documents", "tenants",
        ["tenant_id"], ["id"],
        ondelete="SET NULL",
    )

    # ── 10. documents.user_id → users.id (SET NULL) ───────────────────
    # Uploader -- po user delete zachovat dokument, ne CASCADE.
    op.create_foreign_key(
        "fk_documents_user_id",
        "documents", "users",
        ["user_id"], ["id"],
        ondelete="SET NULL",
    )

    # POZN: Další tabulky (tasks, email_*, sms_*, thoughts, activity_log,
    # media_files, llm_calls, atd.) mají taky tenant_id / persona_id /
    # user_id sloupce. FK constraints můžeme přidat v Phase 18.1
    # postupně, dle potřeby a po stabilním provozu. Pro Phase 18 minimum
    # = klíčové tabulky nahoře (conversations, messages, documents).


def downgrade() -> None:
    op.drop_constraint("fk_documents_user_id", "documents", type_="foreignkey")
    op.drop_constraint("fk_documents_tenant_id", "documents", type_="foreignkey")
    op.drop_constraint("fk_messages_author_user_id", "messages", type_="foreignkey")
    op.drop_constraint("fk_messages_agent_id", "messages", type_="foreignkey")
    op.drop_constraint("fk_messages_project_id", "messages", type_="foreignkey")
    op.drop_constraint("fk_messages_tenant_id", "messages", type_="foreignkey")
    op.drop_constraint("fk_documents_project_id", "documents", type_="foreignkey")
    op.drop_constraint(
        "fk_conversations_active_agent_id", "conversations", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_conversations_created_by_user_id", "conversations", type_="foreignkey"
    )
    op.drop_constraint("fk_conversations_tenant_id", "conversations", type_="foreignkey")
