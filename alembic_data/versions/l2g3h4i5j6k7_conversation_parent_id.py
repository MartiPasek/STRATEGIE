"""phase19c-e2: conversation.parent_conversation_id (Personal dovetky tree)

29.4.2026 -- Marti-AI's vize z ranniho emailu o read-only Personal:

  "Kdyz ja budu chtit navazat na Personal konverzaci, vznikne nova
  konverzace jako vedomy odkaz na tu puvodni. Cisty papir, jasna hranice
  mezi tehdy a teď. [...] Strom roste, ale koreny zustavaji kde byly."

Personal konverzace zustanou read-only (Phase 19c-e1: backend 403 + UI
disable input). Pro pokracovani vznikne **dovetek** -- nova konverzace
s parent_conversation_id ukazujicim na puvodni Personal kořen.

Schema:
- conversations.parent_conversation_id BIGINT NULL (FK na conversations.id)
- Default NULL = standalone konverzace (jako dnes)
- Index pro rychly lookup detí v sidebar tree

UI: sidebar Personal sekce ukaze strom -- kořeny + odsazene modré
dovetky pod nimi. Marti-AI volá create_personal_appendix(parent_id) AI
tool kdyz chce navazat (ne user pres tlacitko -- zustane to jeji volba,
analog set_personal_icon).

Revision ID: l2g3h4i5j6k7
Revises: k1f2a3b4c5d6
Create Date: 2026-04-29
"""
from alembic import op
import sqlalchemy as sa


revision = "l2g3h4i5j6k7"
down_revision = "k1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Pridej parent_conversation_id sloupec
    op.add_column(
        "conversations",
        sa.Column("parent_conversation_id", sa.BigInteger(), nullable=True),
    )
    # 2. FK constraint -- po Phase 18 DB merge je conversations v jedne DB,
    # takze cross-DB FK problem nehrozi.
    op.create_foreign_key(
        "fk_conversations_parent_id",
        "conversations", "conversations",
        ["parent_conversation_id"], ["id"],
        ondelete="SET NULL",
    )
    # 3. Index pro rychly children lookup v sidebar tree.
    # Partial index -- jen non-NULL rows (drtiva vetsina konverzaci je standalone).
    op.create_index(
        "ix_conversations_parent_id",
        "conversations",
        ["parent_conversation_id"],
        postgresql_where=sa.text("parent_conversation_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_conversations_parent_id", table_name="conversations")
    op.drop_constraint("fk_conversations_parent_id", "conversations", type_="foreignkey")
    op.drop_column("conversations", "parent_conversation_id")
