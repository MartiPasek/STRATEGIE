"""phase27i hotfix: drop old ck_auto_send_consents_target_not_null

2.5.2026 ~07:50 -- Marti's smoke test po Phase 27i deploy odhalil:
domain-only insert padl s 'violates check constraint
ck_auto_send_consents_target_not_null'. Puvodni Phase 7 migrace
(a9b8c7d6e5f4 z 23.4.2026) vytvorila CHECK ktery vyzaduje
'target_user_id IS NOT NULL OR target_contact IS NOT NULL'.

Phase 27i pridal target_domain ALE jen jako NEW constraint
(ck_auto_send_consents_target_set) -- nezdrjavila stary. Stary
constraint pak blokuje domain-only insert.

Fix: drop stareho CHECK. Novy ck_auto_send_consents_target_set
uz pokryva domain variantu.

Revision ID: r8m9n0o1p2q3
Revises: q7l8m9n0o1p2
Create Date: 2026-05-02
"""
from alembic import op


revision = "r8m9n0o1p2q3"
down_revision = "q7l8m9n0o1p2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop stareho constraintu z Phase 7 (a9b8c7d6e5f4)
    op.drop_constraint(
        "ck_auto_send_consents_target_not_null",
        "auto_send_consents",
        type_="check",
    )


def downgrade() -> None:
    # Re-create stary constraint -- bez target_domain (Phase 7 puvodni semantika)
    op.create_check_constraint(
        "ck_auto_send_consents_target_not_null",
        "auto_send_consents",
        "(target_user_id IS NOT NULL) OR (target_contact IS NOT NULL)",
    )
