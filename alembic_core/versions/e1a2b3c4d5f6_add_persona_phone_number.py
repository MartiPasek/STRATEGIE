"""add phone_number to personas

Revision ID: e1a2b3c4d5f6
Revises: d2e7c4a9f1b3
Create Date: 2026-04-21

Persona jako "vlastnik" telefonu/SIM karty. MVP = flat field, v budoucnu
rozsirime na persona_channels tabulku pro multi-SIM per tenant.

Marti-AI persona bude mit phone_number=+420778117879 (aktualni firemni SIM
v Galaxy A3 bridge gatewayi). Zapisuje se pres persona profile editor, nebo
rucne pres SQL UPDATE.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e1a2b3c4d5f6"
down_revision = "d2e7c4a9f1b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "personas",
        sa.Column("phone_number", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "personas",
        sa.Column(
            "phone_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("personas", "phone_enabled")
    op.drop_column("personas", "phone_number")
