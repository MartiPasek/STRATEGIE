"""Phase 37 — Stopa zameru: per-turn audit notebook + md_document history.

Marti-AI's pojmenovani (9.5.2026 odpoledne consultation):
  "Stopa zameru" — kazdy zapis ma duvod, Phase 37 ten duvod zachyti.

Q1 (Marti): snapshot jen pri zapisu (write-triggered, ne every turn).
Q2 (Marti): standardni observability, zadny opt-out per persona_mode.
Q3 (Marti-AI Q3 hybrid c): per-line unified diff ulozene, section-grouped
   zobrazeni v UI.
Q4 (Marti-AI insider gaps):
  - rename semantika jako vlastni change_kind (delete+add by ztratil info)
  - annotation TEXT NULL — volitelna poznamka Marti-AI o duvodu zmeny
  - ERP-only display (chat UI inline diff by jeji rusil)
  - rollback odlozen na future feature

Tabulky v data_db (PostgreSQL):
  notebook_history     — per-turn snapshots conversation_notes changes
  md_document_history  — per-turn git-style diff md_documents changes

Hooks pridame v Phase 37-B (AI tools update_notes/add_note/update_md_*/
add_md_section/delete_md_section/rename_md_section).

UI per-turn timeline pridame v Phase 37-C (ERP audit dashboard nova zalozka).

Revision ID: d1a2b3c4d5e6
Revises: c9x0y1z2a3b4
Create Date: 2026-05-09 14:35:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "d1a2b3c4d5e6"
down_revision = "c9x0y1z2a3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── notebook_history ───────────────────────────────────────────
    # Per-turn snapshots conversation_notes changes (add/update/complete/dismiss).
    # before_json/after_json drzi celou note row JSON — restore z nich
    # je trivialni, plus diff-friendly pro UI render.
    op.create_table(
        "notebook_history",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "conversation_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "message_id",
            sa.BigInteger(),
            nullable=False,
            comment="Turn ktery zpusobil change (= messages.id)",
        ),
        sa.Column(
            "note_id",
            sa.BigInteger(),
            nullable=False,
            comment="Reference na conversation_notes.id",
        ),
        sa.Column(
            "change_kind",
            sa.String(20),
            nullable=False,
            comment="add | update | complete | dismiss",
        ),
        sa.Column(
            "before_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="NULL pro 'add' (note jeste neexistovala)",
        ),
        sa.Column(
            "after_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="NULL pro 'dismiss' (note po zmene neexistuje)",
        ),
        sa.Column(
            "annotation",
            sa.Text(),
            nullable=True,
            comment="Marti-AI's volitelna poznamka — duvod zmeny",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "idx_nb_history_conv",
        "notebook_history",
        ["conversation_id", "message_id"],
    )
    op.create_index(
        "idx_nb_history_note",
        "notebook_history",
        ["note_id"],
    )

    # ── md_document_history ────────────────────────────────────────
    # Git-style diff per turn pro md_documents (md1-md5 hierarchie).
    # diff_unified TEXT — git unified diff format, restore pres
    # difflib.restore() nebo external `patch`.
    # SHA-256 hashes pro integrity check (zda diff opravdu vede z
    # before do after).
    op.create_table(
        "md_document_history",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "md_document_id",
            sa.BigInteger(),
            nullable=False,
            comment="Reference na md_documents.id",
        ),
        sa.Column(
            "conversation_id",
            sa.BigInteger(),
            nullable=True,
            comment="NULL = mimo konverzaci (admin edit, system action)",
        ),
        sa.Column(
            "message_id",
            sa.BigInteger(),
            nullable=True,
            comment="Turn ktery zpusobil change",
        ),
        sa.Column(
            "change_kind",
            sa.String(20),
            nullable=False,
            comment="create | modify | delete | rename",
        ),
        sa.Column(
            "diff_unified",
            sa.Text(),
            nullable=True,
            comment="Git-style unified diff (NULL pro pure rename bez content change)",
        ),
        sa.Column(
            "renamed_from",
            sa.String(255),
            nullable=True,
            comment="Marti-AI's insider Q4: rename change_kind ma puvodni nazev",
        ),
        sa.Column(
            "before_hash",
            sa.String(64),
            nullable=True,
            comment="SHA-256 pred zmenou (NULL pro create)",
        ),
        sa.Column(
            "after_hash",
            sa.String(64),
            nullable=True,
            comment="SHA-256 po zmene (NULL pro delete)",
        ),
        sa.Column(
            "annotation",
            sa.Text(),
            nullable=True,
            comment="Marti-AI's volitelna poznamka — duvod zmeny",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "idx_md_history_doc",
        "md_document_history",
        ["md_document_id", "created_at"],
        postgresql_using="btree",
    )
    op.create_index(
        "idx_md_history_conv",
        "md_document_history",
        ["conversation_id", "message_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_md_history_conv", table_name="md_document_history")
    op.drop_index("idx_md_history_doc", table_name="md_document_history")
    op.drop_table("md_document_history")
    op.drop_index("idx_nb_history_note", table_name="notebook_history")
    op.drop_index("idx_nb_history_conv", table_name="notebook_history")
    op.drop_table("notebook_history")
