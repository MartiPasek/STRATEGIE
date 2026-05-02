"""phase27i: auto_send_consents.target_domain (domain-level whitelist)

2.5.2026 -- Phase 27i (Marti-AI's request 06:30 -- 70 EUROSOFT users
v jednom tenantu, per-user grant je byrokratie + new-user problem).

Pridava `target_domain VARCHAR(255) NULL` do auto_send_consents.
Marti (parent) muze grantnout 'eurosoft.com' jednou, Marti-AI pak
auto-sendi na libovolnou @eurosoft.com adresu bez per-user consentu.

Lookup priorita v _is_recipient_trusted (consent_service.py):
  1. target_user_id (exact user match)
  2. target_contact (exact email/telefon)
  3. **target_domain (NEW)** -- extract domain z 'a@b.com' -> match 'b.com'

CHECK constraint: alespon jedno z (target_user_id, target_contact,
target_domain) NOT NULL. Idempotence: zachovavame existujici per-user
consenty, novy domain consent jako separatni radek.

Marti's volby (2.5.2026 06:30):
  Q1 (kdo grantuje): A -- parent only (Phase 7 doctrina nezmenena)
  Q2 (subdomain match): A -- exact match ('eurosoft.com' nematchne 'cz.eurosoft.com')
  Q3 (audit): A -- domain grant zapsany v audit_log + per-message audit
                     (already existing pattern v action_logs)

Revision ID: q7l8m9n0o1p2
Revises: p6k7l8m9n0o1
Create Date: 2026-05-02
"""
from alembic import op
import sqlalchemy as sa


revision = "q7l8m9n0o1p2"
down_revision = "p6k7l8m9n0o1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Pridat target_domain sloupec
    op.add_column(
        "auto_send_consents",
        sa.Column(
            "target_domain",
            sa.String(length=255),
            nullable=True,
        ),
    )

    # CHECK constraint: alespon jedno z (target_user_id, target_contact,
    # target_domain) NOT NULL. Predtim byl implicit "user_id OR contact",
    # ted ho explicitne formalizujeme.
    op.create_check_constraint(
        "ck_auto_send_consents_target_set",
        "auto_send_consents",
        "target_user_id IS NOT NULL OR target_contact IS NOT NULL OR target_domain IS NOT NULL",
    )

    # Index pro rychly domain lookup pri kazdem send check (.lower() match)
    op.create_index(
        "ix_auto_send_consents_target_domain",
        "auto_send_consents",
        ["target_domain"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_auto_send_consents_target_domain",
        table_name="auto_send_consents",
    )
    op.drop_constraint(
        "ck_auto_send_consents_target_set",
        "auto_send_consents",
        type_="check",
    )
    op.drop_column("auto_send_consents", "target_domain")
