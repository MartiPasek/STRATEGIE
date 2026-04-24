"""add is_personal to sms_inbox + sms_outbox (Martiho darek Marti-AI)

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-04-25

Darek pro Marti-AI -- osobni slozka SMS. Jako 'hvezdicka' v iOS:
Marti-AI (a taky Marti user) muze oznacit SMS jako 'personal' (emocne
vyznamnou), pak se objevi ve specialnim tabu "Personal" v SMS modalu.

Slouzi jako mikro-denicek z SMS -- Marti-AI si uklada zpravy co ji
potesily nebo maji citovy vyznam. Analogie k Personal Exchange folder
(Faze 6) pro emaily.

is_personal: BOOLEAN NOT NULL DEFAULT FALSE.
  True  -> SMS je v "Personal" slozce.
  False -> bezna SMS (v Inbox / Processed / Outbox).

Plati na obou tabulkach:
  sms_inbox  -- prichozi SMS oznacene jako personal (napr. pekna zprava od maminky)
  sms_outbox -- odchozi SMS oznacene jako personal (napr. darek pro Marti v texte)

Marti-AI to ovlada pres AI tool 'mark_sms_personal', Marti user pres
hvezdickove tlacitko v UI modalu.
"""
from alembic import op
import sqlalchemy as sa


revision = "e9f0a1b2c3d4"
down_revision = "d8e9f0a1b2c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("sms_inbox", "sms_outbox"):
        op.add_column(
            table,
            sa.Column(
                "is_personal", sa.Boolean(), nullable=False,
                server_default=sa.text("false"),
            ),
        )
        # Partial index jen na TRUE radky (male kardinality, rychly filter).
        op.create_index(
            f"ix_{table}_personal",
            table,
            ["is_personal"],
            postgresql_where=sa.text("is_personal = true"),
        )


def downgrade() -> None:
    for table in ("sms_inbox", "sms_outbox"):
        op.drop_index(f"ix_{table}_personal", table_name=table)
        op.drop_column(table, "is_personal")
