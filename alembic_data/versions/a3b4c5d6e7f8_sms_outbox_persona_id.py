"""sms_outbox: add persona_id column

Revision ID: a3b4c5d6e7f8
Revises: f2d3e4a5b6c7
Create Date: 2026-04-30

Faze 14 prep #3:
  Pridava `persona_id` do `sms_outbox` (analog email_outbox.persona_id).
  1 SIM = 1 persona -- query po persona_id je presnejsi nez heuristika
  pres tenant_id + to_phone.

Predtim:
  Filter v sms UI / list_outbox_for_ui / list_all_for_ui se delal pres
  tenant_id (rodicovsky bypass = cross-tenant). U auto-reply rows mohlo
  dochazet ke kolize, kdy ruzne persony s tym stejnym tenantem mely
  prolinajici se historii.

Po:
  queue_sms() bere persona_id, ulozi ho. UI filter pak presny per persona.
  Backfill: existujici rows -> NULL persona_id (legacy data); UI to umi.

Index: nullable column, index pro query rychlejsi list_*_for_ui.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a3b4c5d6e7f8"
down_revision = "f2d3e4a5b6c7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sms_outbox",
        sa.Column("persona_id", sa.BigInteger(), nullable=True),
    )
    op.create_index(
        "ix_sms_outbox_persona_id_created_at",
        "sms_outbox",
        ["persona_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_sms_outbox_persona_id_created_at", table_name="sms_outbox")
    op.drop_column("sms_outbox", "persona_id")
