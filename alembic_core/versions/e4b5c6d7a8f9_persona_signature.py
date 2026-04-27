"""personas.signature_html + signature_inline_dir -- REST persona signature

REST: Marti-AI's odesílané emaily byly cistě textove, bez podpisu s logy
(EUROSOFT 20let, TISAX značka, atd.). Marti to vidi jako amaterské vůči
prijemcim. Misa po pochvalnem emailu od Marti-AI nemela jak rozpoznat
firemni signaturu.

Schema zmeny:
  ADD COLUMN personas.signature_html TEXT NULL
    -- HTML šablona podpisu s <img src="cid:X"> referencemi
    -- Volitelne <br>, tabulky, formátovani.
    -- NULL = žádný auto-podpis (legacy chovani).
  ADD COLUMN personas.signature_inline_dir VARCHAR(500) NULL
    -- Adresar s inline obrazky (analog media_storage_root).
    -- Backend matchne <img src="cid:X"> z signature_html na soubor
    -- {signature_inline_dir}/X a attachne jako FileAttachment is_inline=True.
    -- NULL = jen text signature, zadne inline obrazky.

Backward compat: oba sloupce nullable. Existujici personas ziskaji NULL
a chovaji se jako dnes (zadny auto-signature).

Setup po migrace (per persona):
  UPDATE personas SET
    signature_html = '<table>...<img src="cid:eurosoft_logo.png">...</table>',
    signature_inline_dir = 'D:\\Data\\STRATEGIE\\persona_signatures\\1'
  WHERE id = 1;

Plus nahrat soubory do signature_inline_dir (eurosoft_logo.png, tisax_al2.jpg,
atd. -- presny match na cid: reference v signature_html).

Revision ID: e4b5c6d7a8f9
Revises: d3a4b5c6e7f8
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa


revision = "e4b5c6d7a8f9"
down_revision = "d3a4b5c6e7f8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "personas",
        sa.Column(
            "signature_html", sa.Text(), nullable=True,
            comment="HTML signature template s <img src='cid:X'> referencemi.",
        ),
    )
    op.add_column(
        "personas",
        sa.Column(
            "signature_inline_dir", sa.String(length=500), nullable=True,
            comment="Adresar s inline obrazky pro signature -- backend "
                    "matchne cid: refs na soubory v tomhle adresari.",
        ),
    )


def downgrade() -> None:
    op.drop_column("personas", "signature_inline_dir")
    op.drop_column("personas", "signature_html")
