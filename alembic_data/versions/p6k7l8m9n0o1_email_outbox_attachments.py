"""phase27b: email outbox attachment_document_ids

1.5.2026 -- Phase 27b (Marti-AI's feature request #2).

Rozsireni send_email + reply + reply_all + forward AI tools o
`attachment_document_ids: list[int]` parametr. Backend nacte file
z documents.storage_path, mime-detect, exchangelib FileAttachment.

Schema: email_outbox.attachment_document_ids (Text NULL, JSON encoded
list[int]). Konzistentni s `cc` / `bcc` pattern (Text JSON arrays).

Workflow Klárka:
  1. Klárka posle email s xlsx -> EWS fetcher import -> documents row
  2. Marti-AI cte: read_excel_structured(document_id)
  3. Marti-AI vyrobi vystup (Phase 27c sandbox bude pozdeji; zatim manual)
  4. Marti-AI: reply(email_inbox_id, body, attachment_document_ids=[N])
  5. Backend: documents[N].storage_path -> bytes -> _FileAtt -> draft.attach()
  6. Klárka dostane email s prilohou v Outlooku.

Revision ID: p6k7l8m9n0o1
Revises: o5j6k7l8m9n0
Create Date: 2026-05-01
"""
from alembic import op
import sqlalchemy as sa


revision = "p6k7l8m9n0o1"
down_revision = "o5j6k7l8m9n0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "email_outbox",
        sa.Column(
            "attachment_document_ids",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("email_outbox", "attachment_document_ids")
