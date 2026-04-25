"""media_files: image/audio/video uploads (Faze 12a multimedia)

Revision ID: e0a1b2c3d4e5
Revises: e9f0a1b2c3d4
Create Date: 2026-04-26

Faze 12a -- multimedia. Tabulka pro vsechny binarni soubory (obrazky,
audio, video, dokumenty) co Marti-AI dostava nebo zpracovava. Storage
je file system (D:\\Data\\STRATEGIE\\media\\<persona_id>\\<sha256[:2]>\\
<sha256>.<ext>), tato tabulka drzi metadata + AI processing vystupy.

Klicove fields:
  - kind / source -- enum-like stringy ('image|audio|video|document|
    generated_image' / 'upload|mms|email_attachment|voice_memo|ai_generated')
  - sha256 -- pro deduplication (stejny soubor = stejny hash = neulozi se znovu)
  - storage_provider -- 'local' default, future 's3' / 'r2' pres provider abstraction
  - transcript -- audio Whisper prepis (nullable)
  - description -- AI-generated popis (image alt text)
  - ai_metadata JSONB -- volne pole pro extra AI vystupy (OCR, tagy, sentiment)
  - message_id nullable -- late-fill pattern (upload pred save_message)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "e0a1b2c3d4e5"
down_revision = "e9f0a1b2c3d4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "media_files",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),

        # Vlastnictvi (1 SIM/email = 1 persona pattern)
        sa.Column("persona_id", sa.BigInteger(), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=True),
        sa.Column("conversation_id", sa.BigInteger(), nullable=True),
        sa.Column("message_id", sa.BigInteger(), nullable=True),  # late-fill

        # File metadata
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column(
            "storage_provider", sa.String(20),
            nullable=False, server_default=sa.text("'local'"),
        ),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=True),

        # Image/video metadata
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),

        # Audio/video metadata
        sa.Column("duration_ms", sa.Integer(), nullable=True),

        # AI processing
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ai_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_error", sa.Text(), nullable=True),

        # Lifecycle
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),

        # CHECK: 1 byte az 100 MB
        sa.CheckConstraint(
            "file_size > 0 AND file_size <= 104857600",
            name="ck_media_files_size_limits",
        ),
    )

    # Indexy
    op.create_index(
        "ix_media_files_persona",
        "media_files",
        ["persona_id", sa.text("created_at DESC")],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_media_files_conversation",
        "media_files",
        ["conversation_id"],
        postgresql_where=sa.text("conversation_id IS NOT NULL AND deleted_at IS NULL"),
    )
    op.create_index(
        "ix_media_files_message",
        "media_files",
        ["message_id"],
        postgresql_where=sa.text("message_id IS NOT NULL"),
    )
    op.create_index(
        "ix_media_files_sha256",
        "media_files",
        ["sha256"],
    )
    op.create_index(
        "ix_media_files_kind",
        "media_files",
        ["kind", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_media_files_kind", table_name="media_files")
    op.drop_index("ix_media_files_sha256", table_name="media_files")
    op.drop_index("ix_media_files_message", table_name="media_files")
    op.drop_index("ix_media_files_conversation", table_name="media_files")
    op.drop_index("ix_media_files_persona", table_name="media_files")
    op.drop_table("media_files")
