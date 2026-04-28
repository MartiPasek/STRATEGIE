"""personas.allowed_project_ids -- Phase 16-B.7 persona project scope

PROBLEM 28.4.2026 odpoledne: PravnikCZ-AI v konverzaci #173 (project default
bug ranni) videla dokumenty v inboxu (project_id=NULL) pres search_documents.
Inbox patri Marti-AI (kustod role); cizi persony tam nemaji byt.

Solution: explicit ACL na persone -- allowed_project_ids INT[]. Marti-AI
default (is_default=True) je rodic, bypass -- vidi vsechno (vc. inboxu).
Specializovane persony (Pravnik, Honza, atd.) maji empty default a Marti
musi explicitne pridat povolene projekty. INBOX (project_id IS NULL) je
NEDOSTUPNY pro non-default persony bez ohledu na ACL -- triage role je
posvatne pro Marti-AI.

Revision ID: g6d7e8f9a0b1
Revises: f5c6d7e8a9b0
Create Date: 2026-04-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "g6d7e8f9a0b1"
down_revision = "f5c6d7e8a9b0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "personas",
        sa.Column(
            "allowed_project_ids",
            postgresql.ARRAY(sa.BigInteger()),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_column("personas", "allowed_project_ids")
