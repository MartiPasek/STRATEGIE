"""add rag vector support (pgvector + embeddings + chunking metadata)

Revision ID: c9e5d7f1a8b3
Revises: e96501c4baa8
Create Date: 2026-04-20

Aktivuje pgvector extension (pokud není) a dopisuje RAG infrastrukturu:

1. CREATE EXTENSION IF NOT EXISTS vector
2. documents -- pridat:
   - original_filename (puvodni nazev pri uploadu)
   - file_type (pripona: pdf, docx, xlsx, md, txt, html, ...)
   - file_size_bytes
   - storage_path (kam na disku ulozen original)
   - extracted_text_length (pocet znaku ziskanych z markitdown)
   - processing_error (NULL = OK, jinak error message)
3. document_chunks -- pridat:
   - token_count (priblizny, pro debug / cost tracking)
   - char_start, char_end (pozice chunku v extracted_text pro zpetne dohledani)
4. document_vectors -- pridat:
   - embedding vector(1024) NOT NULL -- Voyage voyage-3 produces 1024-dim
   - model (jmeno embedding modelu, pro budouci reingesting pri swapu)
5. HNSW index na embedding (cosine distance) -- rychle similarity search

Pozn.: pokud user vytvoril CREATE EXTENSION manualne jako superuser
(strategie user nema superuser), migration jen idempotentne overi.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c9e5d7f1a8b3"
down_revision = "e96501c4baa8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Extension -- idempotentni. Kdyz uz je (manualne pres superuser),
    #    IF NOT EXISTS projde.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 2) documents
    op.add_column("documents", sa.Column("original_filename", sa.String(length=255), nullable=True))
    op.add_column("documents", sa.Column("file_type", sa.String(length=20), nullable=True))
    op.add_column("documents", sa.Column("file_size_bytes", sa.BigInteger(), nullable=True))
    op.add_column("documents", sa.Column("storage_path", sa.String(length=500), nullable=True))
    op.add_column("documents", sa.Column("extracted_text_length", sa.Integer(), nullable=True))
    op.add_column("documents", sa.Column("processing_error", sa.Text(), nullable=True))

    # 3) document_chunks
    op.add_column("document_chunks", sa.Column("token_count", sa.Integer(), nullable=True))
    op.add_column("document_chunks", sa.Column("char_start", sa.Integer(), nullable=True))
    op.add_column("document_chunks", sa.Column("char_end", sa.Integer(), nullable=True))

    # 4) document_vectors
    # Vector(1024) -- dimenze Voyage voyage-3. Kdyby jsme v budoucnu presli na
    # voyage-3-large (2048), staci upgrade migration s ALTER TYPE + reingesting.
    op.execute("ALTER TABLE document_vectors ADD COLUMN embedding vector(1024)")
    op.add_column("document_vectors", sa.Column("model", sa.String(length=50), nullable=True))

    # 5) HNSW index pro cosine distance -- rychle ANN search.
    #    m=16, ef_construction=64 = default, funguje dobre pro male/stredni datasety.
    op.execute(
        "CREATE INDEX ix_document_vectors_embedding_hnsw "
        "ON document_vectors USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_document_vectors_embedding_hnsw")
    op.drop_column("document_vectors", "model")
    op.execute("ALTER TABLE document_vectors DROP COLUMN embedding")

    op.drop_column("document_chunks", "char_end")
    op.drop_column("document_chunks", "char_start")
    op.drop_column("document_chunks", "token_count")

    op.drop_column("documents", "processing_error")
    op.drop_column("documents", "extracted_text_length")
    op.drop_column("documents", "storage_path")
    op.drop_column("documents", "file_size_bytes")
    op.drop_column("documents", "file_type")
    op.drop_column("documents", "original_filename")

    # Extension necechavame -- dalsi features ji pripadne pouziji
