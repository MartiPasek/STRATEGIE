"""add marti_questions table

Revision ID: f0b1c2d3e4a5
Revises: e9c3d4e5f6a7
Create Date: 2026-04-22

Marti Memory -- Faze 4 (aktivni uceni). Samostatna tabulka pro otazky,
ktere Marti chce polozit rodicum kvuli overeni nejasnych myslenek.

Designove rozhodnuti #6e v docs/marti_memory_design.md:
  Oddeleno od `thoughts` (myslenky = "co Marti vi") a `tasks` (tasky
  = "co AI ma vykonat"). marti_questions = "co Marti chce vedet od
  rodice".

Lifecycle:
  open      -- Marti otazku vygenerovala, ceka na rodice
  answered  -- rodic kliknul na Ano/Ne/Nejsem si jist (+ pripadny text)
  skipped   -- rodic zvolil "Preskoc", myslenka se nezmenila
  cancelled -- systemove zruseno (myslenka smazana, rodic smazan, ...)

Processing:
  Mechanicka uprava certainty probehne ihned pri odpovedi:
    yes       -> thought.certainty += 25 (auto-promote pokud >= 80)
    no        -> thought.certainty -= 40
    not_sure  -> thought.certainty += 0 (jen oznacena)
    skipped   -> thought nemeni

  Textove odpovedi (answer_text != NULL) ceka na nocni LLM batch
  (scripts/question_generator.py review cycle), ktery text interpretuje
  a muze thought dodatecne upravit (korekce obsahu, nove myslenky).
  text_reviewed_at sloupec sleduje, zda uz LLM batch text zpracoval.

priority_score:
  V MVP generator naplnuje (100 - certainty) + urgency pro razeni v UI.
  Vysoke skore = drive v listu.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f0b1c2d3e4a5"
down_revision = "e9c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "marti_questions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),

        # Reference na myslenku (weak FK -- thought muze byt smazana, otazka zustava jako audit)
        sa.Column("thought_id", sa.BigInteger(), nullable=False),

        # Vlastni otazka vygenerovana LLM
        sa.Column("question_text", sa.Text(), nullable=False),

        # Komu se pta (rodic)
        sa.Column("target_user_id", sa.BigInteger(), nullable=False),

        # Lifecycle
        sa.Column(
            "status", sa.String(length=20), nullable=False,
            server_default="open",
            # open | answered | skipped | cancelled
        ),

        # Odpoved -- strukturovana + volitelny text
        sa.Column(
            "answer_choice", sa.String(length=20), nullable=True,
            # yes | no | not_sure
        ),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("answered_by_user_id", sa.BigInteger(), nullable=True),

        # Kdy LLM batch zpracoval answer_text (NULL = jeste nezpracovano,
        # answer_text byl set -> kandidat pro review).
        sa.Column("text_reviewed_at", sa.DateTime(timezone=True), nullable=True),

        # Priority score pro razeni v UI listu
        sa.Column("priority_score", sa.Integer(), nullable=False, server_default="50"),

        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # Hot path: UI list otazek pro rodice ('open' status, razeni priority).
    op.create_index(
        "ix_marti_questions_target_status_priority",
        "marti_questions",
        ["target_user_id", "status", "priority_score"],
    )

    # Dedup: pri generovani se chceme vyhnout duplikaci otazky k te same myslence.
    # Uzivatelske dotazy: "ma tato myslenka jiz otevrenou otazku?"
    op.create_index(
        "ix_marti_questions_thought_status",
        "marti_questions",
        ["thought_id", "status"],
    )

    # Text review batch: kandidati maji answer_text NOT NULL + text_reviewed_at NULL.
    # Partial index setri prostor (jen rady ktere batch zpracuje).
    op.create_index(
        "ix_marti_questions_pending_text_review",
        "marti_questions",
        ["answered_at"],
        postgresql_where=sa.text(
            "answer_text IS NOT NULL AND text_reviewed_at IS NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_marti_questions_pending_text_review",
        table_name="marti_questions",
    )
    op.drop_index(
        "ix_marti_questions_thought_status",
        table_name="marti_questions",
    )
    op.drop_index(
        "ix_marti_questions_target_status_priority",
        table_name="marti_questions",
    )
    op.drop_table("marti_questions")
