"""audit log extension (ip, user_agent, entity_id, extra_metadata)

Revision ID: f1b2c3d4e5f6
Revises: b2d9e0f4e5c7
Create Date: 2026-04-20

Rozsiruje existujici audit_log tabulku o sloupce potrebne pro security
+ operation auditing nad ramec puvodniho 'AI call duration tracking':

- ip_address    -- pro login attempts (kdo se kde prihlasil)
- user_agent    -- prohlizec/OS info (forenznice + reseni reportovanych chyb)
- entity_id     -- ID cilove entity akce (document_id pri 'document_uploaded',
                   invitee user_id pri 'invite_sent', ...)
- extra_metadata -- JSON blob pro event-specific data (filename, file_size,
                    from_tenant/to_tenant, error_reason, ...). Json typed na
                    PostgreSQL JSONB (effective dotazovani).

Index na (created_at) pro rychly listing 'recent events' v admin UI.
Index na (action, status) pro filtrovani 'show me failed logins'.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = "f1b2c3d4e5f6"
down_revision = "b2d9e0f4e5c7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_log", sa.Column("ip_address", sa.String(length=64), nullable=True))
    op.add_column("audit_log", sa.Column("user_agent", sa.String(length=500), nullable=True))
    op.add_column("audit_log", sa.Column("entity_id", sa.BigInteger(), nullable=True))
    op.add_column("audit_log", sa.Column("extra_metadata", JSONB(), nullable=True))

    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])
    op.create_index("ix_audit_log_action_status", "audit_log", ["action", "status"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_action_status", table_name="audit_log")
    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_column("audit_log", "extra_metadata")
    op.drop_column("audit_log", "entity_id")
    op.drop_column("audit_log", "user_agent")
    op.drop_column("audit_log", "ip_address")
