"""
DB_Data (data_db) SQLAlchemy models.
Obsahuje všechny tabulky pro provozní a obsahová data.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey,
    Integer, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column
from core.database_data import BaseData

# pgvector integrace do SQLAlchemy. Import je hned vedle ostatnich typu,
# aby Vector typ byl dostupny v model definici (DocumentVector.embedding).
from pgvector.sqlalchemy import Vector

# Voyage voyage-3 produces 1024-dim embeddings.
EMBEDDING_DIM = 1024


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ── KONVERZACE ─────────────────────────────────────────────────────────────

class Conversation(BaseData):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    project_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    active_agent_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    interaction_mode: Mapped[str] = mapped_column(String(10), default="ai")   # ai | human
    handoff_state: Mapped[str] = mapped_column(String(30), default="idle")    # idle | clarifying_request | ready_for_handoff | sent_to_human
    conversation_type: Mapped[str] = mapped_column(String(20), default="ai")  # ai | dm | (group later)
    created_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Pro DM: uspořádaná dvojice user_id (low < high) pro jednoznačný lookup a partial unique index.
    dm_user_low_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    dm_user_high_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    # Archivace: konverzace zmizí ze sidebaru/dropdownu, ale zůstává v DB.
    # Přístup k archivním konverzacím bude přes samostatný 'archiv' (TBD).
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Message(BaseData):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("conversations.id", ondelete="CASCADE"))
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    project_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    role: Mapped[str] = mapped_column(String(20))           # user | assistant
    content: Mapped[str] = mapped_column(Text)
    agent_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    author_type: Mapped[str] = mapped_column(String(10), default="ai")   # ai | human
    author_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    message_type: Mapped[str] = mapped_column(String(20), default="text")  # text | system | ai_summary
    last_human_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_human_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class ConversationSummary(BaseData):
    __tablename__ = "conversation_summaries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("conversations.id", ondelete="CASCADE"))
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    project_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    summary_text: Mapped[str] = mapped_column(Text)
    from_message_id: Mapped[int] = mapped_column(BigInteger)
    to_message_id: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class ConversationShare(BaseData):
    __tablename__ = "conversation_shares"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("conversations.id", ondelete="CASCADE"))
    project_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    shared_with_user_id: Mapped[int] = mapped_column(BigInteger)
    access_level: Mapped[str] = mapped_column(String(10))   # read | write
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class ConversationParticipant(BaseData):
    """
    Účastníci konverzace (MVP: pouze DM = dva řádky na konverzaci).
    Každý účastník drží svůj read-state, mute/archive flag.
    Pro AI konverzace se tento záznam NEvyplňuje — vlastníka drží Conversation.user_id.
    """
    __tablename__ = "conversation_participants"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("conversations.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(BigInteger)   # FK logická — users žijí v css_db
    participant_role: Mapped[str] = mapped_column(String(20), default="member")   # owner | member
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    last_read_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_muted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)


# ── PAMĚŤ ──────────────────────────────────────────────────────────────────

class Memory(BaseData):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    project_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


# ── DOKUMENTY / RAG ────────────────────────────────────────────────────────

class Document(BaseData):
    """
    RAG dokument -- jeden uploadovany soubor (PDF, DOCX, MD, ...).
    Scope: tenant_id povinny, project_id volitelny (NULL = tenantovy obecny dokument).
    user_id = uploader (pro audit + budouci access control).

    Lifecycle:
      is_processed=False, processing_error=NULL  -> upload prosel, ceka na chunking
      is_processed=False, processing_error=NOT NULL -> chunking failed (viz error)
      is_processed=True                          -> chunky + embeddings hotove, RAG ready
    """
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    project_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    name: Mapped[str] = mapped_column(String(255))                       # human-readable display name
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(20), nullable=True)   # pdf, docx, md, txt, ...
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)  # absolutni cesta na disku
    extracted_text_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class DocumentChunk(BaseData):
    """
    Chunk = ~500 token vyrez z dokumentu. Drzi original text + pozici v
    extrahovanem textu pro zpetne dohledani (highlight v UI atp.).
    """
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("documents.id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(Text)
    chunk_index: Mapped[int] = mapped_column(Integer)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_end: Mapped[int | None] = mapped_column(Integer, nullable=True)


class DocumentVector(BaseData):
    """
    Voyage voyage-3 embedding pro chunk. 1024 dimensions, cosine distance.
    HNSW index (vector_cosine_ops) -- viz migrace c9e5d7f1a8b3.
    """
    __tablename__ = "document_vectors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chunk_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("document_chunks.id", ondelete="CASCADE"))
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)   # "voyage-3", pro budouci reingesting


# ── AUDIT AKCÍ ─────────────────────────────────────────────────────────────

class ActionLog(BaseData):
    __tablename__ = "action_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    agent_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    action_type: Mapped[str] = mapped_column(String(20))   # auto | confirm | critical
    tool_name: Mapped[str] = mapped_column(String(100))
    input: Mapped[str | None] = mapped_column(Text, nullable=True)
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20))         # success | fail
    execution_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    approval_required: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class PendingAction(BaseData):
    __tablename__ = "pending_actions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("conversations.id", ondelete="CASCADE"))
    action_type: Mapped[str] = mapped_column(String(50))   # "send_email"
    payload: Mapped[str] = mapped_column(Text)             # JSON
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


# ── SMS OUTBOX ─────────────────────────────────────────────────────────────

class SmsOutbox(BaseData):
    """
    Outbox pro odchozi SMS -- write-only z aplikace, poll-read Android gateway.

    Lifecycle:
      pending   -> queue_sms() zapsal, ceka na telefon
      sent      -> telefon potvrdil (POST /gateway/outbox/{id}/sent)
      failed    -> telefon reportoval chybu / rate limit / provider error

    purpose:
      user_request  -- AI tool `send_sms` na zadost usera (s potvrzenim)
      notification  -- automaticka notifikace (offline zpravy apod.)
      system        -- alerting / audit / bezpecnost

    to_phone format: E.164 (+420777180511), normalizovano v sms_service.
    """
    __tablename__ = "sms_outbox"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    to_phone: Mapped[str] = mapped_column(String(20))
    body: Mapped[str] = mapped_column(Text)
    purpose: Mapped[str] = mapped_column(String(30), default="user_request")
    status: Mapped[str] = mapped_column(String(20), default="pending")   # pending | sent | failed
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
