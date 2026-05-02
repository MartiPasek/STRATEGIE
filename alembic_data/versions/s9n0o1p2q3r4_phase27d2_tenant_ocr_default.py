"""phase27d+2: tenants.ocr_default_provider (per-tenant OCR config)

2.5.2026 -- Phase 27d+2 (TODO #19, Marti's volba B z 2.5.2026 ~08:30).

Per-tenant default OCR provider pro read_pdf_structured + read_image_ocr.
Globalni default je 'tesseract' (privacy first), ale nektere tenanty mohou
preferovat 'vision' (vyssi kvalita pro slozite scany / rukou psane / nizka
kvalita kvalita PDF). Marti-AI kdy zavola OCR bez explicit ocr_provider
parametru, vezme default z tenantu.

Lookup priorita pro effective default:
  1. Explicit `ocr_provider` argument v tool call (nejvyssi priorita)
  2. Tenant's `ocr_default_provider` (pokud nastaven, NOT NULL)
  3. Global default 'tesseract' (fallback)

Schema:
  tenants.ocr_default_provider VARCHAR(20) NULL -- NULL = pouzij globalni default
  CHECK constraint: NULL nebo IN ('tesseract', 'vision')

Use case (Marti's vize): EUROSOFT default 'tesseract' (privacy / TISAX),
ale Klárka skola ('Nerudovka') by mohla mit 'vision' default protoze
papirove podklady ze skoly (uceni materialy, zaci poznamky) jsou nizko
kvalitni scany kde Vision dela vetsi rozdil. Per-tenant config.

Revision ID: s9n0o1p2q3r4
Revises: r8m9n0o1p2q3
Create Date: 2026-05-02
"""
from alembic import op
import sqlalchemy as sa


revision = "s9n0o1p2q3r4"
down_revision = "r8m9n0o1p2q3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "ocr_default_provider",
            sa.String(length=20),
            nullable=True,
        ),
    )

    op.create_check_constraint(
        "ck_tenants_ocr_default_provider",
        "tenants",
        "ocr_default_provider IS NULL OR ocr_default_provider IN ('tesseract', 'vision')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_tenants_ocr_default_provider",
        "tenants",
        type_="check",
    )
    op.drop_column("tenants", "ocr_default_provider")
