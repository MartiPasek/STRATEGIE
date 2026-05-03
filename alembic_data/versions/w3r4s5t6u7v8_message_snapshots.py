"""message_snapshots: per-turn audit window_size + notebook_count

3.5.2026 odpoledne -- Marti's pozadavek: "audit musi byt per-turn snapshot,
ne aktualni stav. V turnu #5 Marti-AI mela okno 5, v turnu #20 rozsirila
na 50 -- hlavicka dnes ukaze jen 50, audit historie ztracena."

Pridava do messages dva nove sloupce -- snapshot v okamziku save_message:

1. window_size_at_send INT NULL
   - Co bylo conversations.context_window_size v okamziku, kdy se message
     ulozila (typicky outgoing assistant message, ale pro user msg taky
     OK -- audit kompletni).
   - NULL pro starsi rows (pre-fix). UI zobrazi "—" (em-dash).
   - Default NULL, populace v save_message hook.

2. notebook_count_at_send INT NULL
   - Kolik notes bylo v conversation_notes pro tuto konverzaci a personu
     v okamziku save. SELECT count(*) WHERE conversation_id=X
     AND persona_id=Y AND archived=false.
   - NULL pro starsi rows. UI zobrazi "—" pod prvni padding.

Down: drop columns. Bezpecne -- starsi messages bez snapshot pokracuji
v UI s "—".
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "w3r4s5t6u7v8"
down_revision = "v2q3r4s5t6u7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column("window_size_at_send", sa.Integer(), nullable=True),
    )
    op.add_column(
        "messages",
        sa.Column("notebook_count_at_send", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("messages", "notebook_count_at_send")
    op.drop_column("messages", "window_size_at_send")
