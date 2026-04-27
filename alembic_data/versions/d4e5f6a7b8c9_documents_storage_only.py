"""documents.storage_only flag pro ne-extrahovatelne formaty (REST-Doc-Triage v3.5)

Pouzitelny princip: documents tabulka uz dnes prijima jakykoliv soubor (zadny
extension whitelist v upload endpoint). Pro ne-extrahovatelne formaty (ZIP,
RAR, MP4, EXE, ...) markitdown selze, processing_error se zapise, ale
dokument zustane v DB i na disku. Tj. uloziste pro libovolne soubory v
projektu uz fakticky funguje, jen UX neni cisty.

Tahle migrace pridava ZNACKU `storage_only`. Pipeline (modules/rag/application/
service.py) si toho potom vsima -- pro storage_only=True PRESKOCI extract_text()
+ vytvori 1 'filename chunk' (filename + folder + projekt) pro searchability
podle nazvu. Cilem je: I ZIP musi byt dohledatelny pres semantic search podle
jmena, jen ne podle obsahu.

Schema zmena:
  ADD COLUMN documents.storage_only BOOLEAN NOT NULL DEFAULT FALSE
    -- True = neextraktovat obsah, jen ulozit + indexovat filename
    -- False = standardni RAG processing (extract -> chunk -> embed)
    -- Detekce automaticky pri uploadu podle ext (whitelist EXTRACTABLE)
    -- Marti muze pozdeji manual override (UI tlacitko / AI tool, future)

Backward compat: existing rows dostanou storage_only=False (chovaji se jako
dnes). Backfill na storage_only=True pro rows s processing_error LIKE
'Z dokumentu nebyl extrahovan%' bude separatni script (ne migrace -- vyzaduje
embedding API call pro filename chunk).

Revision ID: d4e5f6a7b8c9
Revises: c2d3e4f5a6b7
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa


revision = "d4e5f6a7b8c9"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "storage_only", sa.Boolean(),
            nullable=False, server_default=sa.text("false"),
            comment=(
                "True = jen uschova bez RAG indexace obsahu (ZIP, MP4, EXE, ...)."
                " Filename chunk se i tak vytvori pro searchability podle nazvu."
            ),
        ),
    )


def downgrade() -> None:
    op.drop_column("documents", "storage_only")
