"""add auto_send_consents table

Revision ID: a9b8c7d6e5f4
Revises: f0b1c2d3e4a5
Create Date: 2026-04-23

Marti Phase 7: trvaly, odvolatelny souhlas s auto-send emailu/SMS bez
potvrzeni v chatu.

Governance:
  - Spravuji vyhradne rodice (users.is_marti_parent=True).
  - Pro non-parents je audit read-only.

Kontrola pri send:
  - send_email/send_sms vezme vsechny TO/CC/BCC prijemce.
  - Pokud VSICHNI maji aktivni consent pro dany channel -> auto-send
    (bez pending_action, bez preview).
  - Jinak normalni flow (preview -> confirm).

Active consent: revoked_at IS NULL.

Revoke nemaze radek -- zustava jako audit trail. Re-grant pri revoked
consentu = novy radek.

Target:
  - target_user_id -- pokud je prijemce v users (preferovane, email se
    dohlada pres user_contacts pri kontrole).
  - target_contact -- email/telefon pro kontakty mimo users (napr. zakaznik).

Rate limit:
  - 20 auto-sendu / hodinu / channel / granted_by_user_id (aplikacne
    vynuceno ve service vrstve, tabulka nema dedicated counter -- pouziva
    COUNT z action_logs).
"""
from alembic import op
import sqlalchemy as sa


revision = "a9b8c7d6e5f4"
down_revision = "f0b1c2d3e4a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auto_send_consents",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),

        # Komu (jedno z dvou MUSI byt neprazdne; ideal: obojí když známe user i adresu)
        sa.Column("target_user_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "target_contact", sa.String(length=320), nullable=True,
            # email (max 320 per RFC) nebo E.164 telefon (do 20 char, sdilime sloupec)
        ),

        # Kanal
        sa.Column(
            "channel", sa.String(length=10), nullable=False,
            # email | sms
        ),

        # Kdo dal souhlas (rodic)
        sa.Column("granted_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "granted_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),

        # Revoke audit trail (nemazat radek)
        sa.Column("revoked_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),

        # Kontext (nepovinny komentar rodice)
        sa.Column("note", sa.Text(), nullable=True),
    )

    # Hot path: pri kazdem send kontrolujeme aktivni consent pro (target, channel).
    # Partial index jen na active (revoked_at IS NULL) -- hlavni dotazovaci scenar.
    op.create_index(
        "ix_auto_send_consents_target_user_active",
        "auto_send_consents",
        ["target_user_id", "channel"],
        postgresql_where=sa.text("revoked_at IS NULL AND target_user_id IS NOT NULL"),
    )
    op.create_index(
        "ix_auto_send_consents_target_contact_active",
        "auto_send_consents",
        ["target_contact", "channel"],
        postgresql_where=sa.text("revoked_at IS NULL AND target_contact IS NOT NULL"),
    )

    # Rate limit sledovani (kolik consentu udelil jaky rodic za posledni hodinu)
    # + audit list v UI razeny od nejnovejsich.
    op.create_index(
        "ix_auto_send_consents_granted_by_at",
        "auto_send_consents",
        ["granted_by_user_id", "granted_at"],
    )

    # CHECK constraint: alespon jeden z (target_user_id, target_contact) musi byt neprazdny.
    op.create_check_constraint(
        "ck_auto_send_consents_target_not_null",
        "auto_send_consents",
        "(target_user_id IS NOT NULL) OR (target_contact IS NOT NULL)",
    )

    # CHECK constraint: channel validace.
    op.create_check_constraint(
        "ck_auto_send_consents_channel",
        "auto_send_consents",
        "channel IN ('email', 'sms')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_auto_send_consents_channel", "auto_send_consents")
    op.drop_constraint("ck_auto_send_consents_target_not_null", "auto_send_consents")
    op.drop_index("ix_auto_send_consents_granted_by_at", table_name="auto_send_consents")
    op.drop_index(
        "ix_auto_send_consents_target_contact_active",
        table_name="auto_send_consents",
    )
    op.drop_index(
        "ix_auto_send_consents_target_user_active",
        table_name="auto_send_consents",
    )
    op.drop_table("auto_send_consents")
