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


# ── SMS INBOX ──────────────────────────────────────────────────────────────

class SmsInbox(BaseData):
    """
    Prichozi SMS od Android gateway (capcom6 webhook).
    persona_id = komu to prislo (majitel SIMky = persona s matching phone_number).

    Workflow pole:
      read_at       -- kdy si user zpravu poprve zobrazil v UI (binarni stav
                       "videna" vs "nova")
      processed_at  -- kdy byly vsechny souvisejici tasky dokonceny (inbox ->
                       processed). NULL = lezi ve slozce "Prichozi", NOT NULL
                       = slozka "Zpracovane". Plni se z tasks.completed_at,
                       kdyz posledni open task nad touhle SMS prejde do 'done'.
    """
    __tablename__ = "sms_inbox"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    persona_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    from_phone: Mapped[str] = mapped_column(String(20))
    body: Mapped[str] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    # JSON metadata z gateway (SIM slot, delivery reports, ...) -- kdyby
    # bylo treba debug.
    meta: Mapped[str | None] = mapped_column(Text, nullable=True)


# ── PHONE CALLS ────────────────────────────────────────────────────────────

class PhoneCall(BaseData):
    """
    Zaznam telefonniho hovoru z Android telefonu (Tasker push po skonceni / missed).

    direction:
      in      -- prichozi hovor prijat (duration_s > 0)
      out     -- odchozi hovor uskutecneny (duration_s >= 0)
      missed  -- prichozi hovor nezvednut (duration_s = NULL)
    """
    __tablename__ = "phone_calls"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    persona_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    peer_phone: Mapped[str] = mapped_column(String(20))
    direction: Mapped[str] = mapped_column(String(10))   # in | out | missed
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    meta: Mapped[str | None] = mapped_column(Text, nullable=True)


# ── TASKS (AI agent task queue) ────────────────────────────────────────────

class Task(BaseData):
    """
    Task jako first-class entita -- jednotka prace pro AI personu.

    Vznika bud:
      - automaticky pri prichozi zprave (source_type='sms_inbox' | 'email_inbox')
      - manualne od usera v UI (source_type='manual')
      - kdyz AI sama rozhodne ze neco potrebuje udelat (source_type='ai_generated')

    Lifecycle:
      open        -- prave vytvoreny, ceka na exekutora
      in_progress -- worker ho prevzal, AI na nem pracuje
      done        -- hotovo, result_summary obsahuje co se udelalo
      cancelled   -- zrusil user pred dokoncenim
      failed      -- exekuce selhala (error obsahuje detail), muze se retry-ovat

    source_id je weak reference (bez FK constraintu) na sms_inbox.id / email_inbox.id
    / manual=NULL. Takhle se vyhneme cross-table FK matici a zachovame flexibilitu.

    execution_conversation_id odkazuje na skrytou conversation (conversation_type=
    'task_execution'), kde probihal AI tool loop -- pro audit a pripadne UI
    zobrazeni postupu AI.

    priority je fixed string (misto int) kvuli citelnosti v SQL dotazech.
    """
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    persona_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    source_type: Mapped[str] = mapped_column(String(30))    # sms_inbox | email_inbox | manual | ai_generated
    source_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="open")        # open | in_progress | done | cancelled | failed
    priority: Mapped[str] = mapped_column(String(10), default="normal")    # high | normal | low
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Kdyz executor zalozi skrytou conversation, zapise sem jeji ID, aby UI
    # mohlo nabidnout "Zobrazit postup AI" a audit videl cely prubeh.
    execution_conversation_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Co AI udelala (final message od AI pri done, nebo stripped error pri failed).
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Kdo task vytvoril:
    #   NULL                 -- automaticky system (auto-create ze zpravy, AI)
    #   user_id (BigInteger) -- manualne clovek z UI
    created_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Kolikrat worker tenhle task prevzal (retry counter). Zabrana nekonecnemu
    # smyckovani kdyz AI opakovane selhava.
    attempts: Mapped[int] = mapped_column(Integer, default=0)


# ── EMAIL INBOX ────────────────────────────────────────────────────────────

class EmailInbox(BaseData):
    """
    Prichozi emaily z Exchange/EWS. Paralelni struktura k SmsInbox, ale
    plneni je pull-model: scripts/email_fetcher.py polluje INBOX persony
    kazdych ~60s, oznaci v EWS jako read, ulozi do teto tabulky.

    persona_id = majitel e-mailove schranky (persona_channel s channel_type
    = 'email' a matching identifier = to_email).

    message_id = RFC822 Message-ID z Exchange, pro dedup. UNIQUE per persona
    zajistuje ze opakovany fetch (restart workera, sit vypadla) neudela
    duplikat.

    Workflow pole:
      read_at       -- kdy si user zpravu poprve zobrazil v UI
      processed_at  -- kdy byl email uzavren (NULL = 'Prichozi' tab,
                       NOT NULL = 'Zpracovane' tab). Plni se bud manualne
                       z UI, nebo kaskadou z posledniho completed tasku
                       (stejne jako sms_inbox dnes).
    """
    __tablename__ = "email_inbox"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    persona_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    from_email: Mapped[str] = mapped_column(String(320))
    from_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    to_email: Mapped[str] = mapped_column(String(320))
    subject: Mapped[str | None] = mapped_column(String(998), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_id: Mapped[str] = mapped_column(String(998))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    # JSON metadata z EWS (cc, bcc, folder, importance, has_attachments, ...)
    # -- debug + budoucnost (reply threading, attachments handling).
    meta: Mapped[str | None] = mapped_column(Text, nullable=True)


# ── EMAIL OUTBOX ───────────────────────────────────────────────────────────

class EmailOutbox(BaseData):
    """
    Odchozi emaily -- asynchronni send pres worker. Paralelni struktura k
    SmsOutbox, ale provider je jeden (Exchange/EWS), takze nepotrebujeme
    "provider" sloupec.

    Lifecycle:
      pending -> queue_email() zapsal, worker ceka
      sent    -> worker odeslal (sent_at NOT NULL)
      failed  -> EWS selhal; last_error obsahuje detail, attempts++

    cc/bcc jsou JSON arrays emailu (ukladane jako Text pro prenositelnost).

    conversation_id = vazba na zpravy konverzaci, z nichz email vzesel
    (audit "zobraz v puvodnim chatu").

    from_identity:
      persona (default) -- posila jmenem persony, creds z persona_channels
      user              -- posila jmenem usera, creds z user_channel_service
      system            -- fallback na .env (legacy)
    """
    __tablename__ = "email_outbox"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    persona_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    to_email: Mapped[str] = mapped_column(String(320))
    cc: Mapped[str | None] = mapped_column(Text, nullable=True)        # JSON list
    bcc: Mapped[str | None] = mapped_column(Text, nullable=True)       # JSON list
    subject: Mapped[str | None] = mapped_column(String(998), nullable=True)
    body: Mapped[str] = mapped_column(Text)
    purpose: Mapped[str] = mapped_column(String(30), default="user_request")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    conversation_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    from_identity: Mapped[str] = mapped_column(String(20), default="persona")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ── MARTI MEMORY: THOUGHTS + ENTITY LINKS ──────────────────────────────────

class Thought(BaseData):
    """
    Zakladni atom Martiho pameti (viz docs/marti_memory_design.md).

    Faze 1 (aktualni): pouziva content, type, author_*, source_*, created_at,
    deleted_at. Ostatni pole jsou v schematu pro pozdejsi faze (zadne
    migrace se pak nebudou delat).

    type: fact | todo | observation | question | goal | experience
      Type-specific fields v `meta` JSON:
        fact        -> {}
        todo        -> {"done": bool, "due_at": iso-str}
        observation -> {"event_at": iso-str}
        question    -> {"answered_at": iso-str, "answered_by_user_id": int,
                        "answer_content": str}
        goal        -> {"progress_percent": int, "milestones": [...]}
        experience  -> {"emotion": str, "intensity": int 1-10}

    status: note (pracovni poznamka) | knowledge (trvala znalost).
      Faze 1 zapisuje vse jako 'note'. Povyseni na 'knowledge' prijde v Faze 2.

    certainty: 0-100, v Fazi 1 default 50. V Fazi 3 ridi auto-promoci (>=80).

    primary_parent_id: self-referential FK. Pro UI strom navigaci (jeden parent
      per myslenka pro zobrazeni); cross-reference k vice entitam resi
      ThoughtEntityLink.

    tenant_scope: NULL = universal (Martiho diar v Faze 5+), jinak id tenantu.

    Provenance:
      author_user_id / author_persona_id -- kdo myslenku zapsal
      source_event_type / source_event_id -- z ceho vzesla (konverzace, email,
        SMS, manual, ai_inferred)

    Soft delete: deleted_at NOT NULL = smazana. Service vzdy filtruje
    deleted_at IS NULL.
    """
    __tablename__ = "thoughts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Core content
    content: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(30))

    # Status & certainty
    status: Mapped[str] = mapped_column(String(20), default="note")
    certainty: Mapped[int] = mapped_column(Integer, default=50)

    # Tree structure (self-referential)
    primary_parent_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Tenant isolation
    tenant_scope: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Provenance
    author_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    author_persona_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_event_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    source_event_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Type-specific fields (JSON)
    meta: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ThoughtEntityLink(BaseData):
    """
    Many-to-many vazba mezi myslenkami a entitami (user/persona/tenant/project).

    Myslenka 'Petr pracuje na STRATEGII v EUROSOFTU' bude mit 3 linky:
      (thought_id=X, entity_type='user',    entity_id=petr_id)
      (thought_id=X, entity_type='project', entity_id=strategie_id)
      (thought_id=X, entity_type='tenant',  entity_id=eurosoft_id)

    entity_type: 'user' | 'persona' | 'tenant' | 'project'
    entity_id: odpovidajici id (FK bez constraintu -- zachovame flexibilitu
                                napric css_db / data_db)

    UNIQUE (thought_id, entity_type, entity_id) -- zabrani duplikum.
    Pro retrieval "vse o entite X" -- ix_entity.
    """
    __tablename__ = "thought_entity_links"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    thought_id: Mapped[int] = mapped_column(BigInteger)
    entity_type: Mapped[str] = mapped_column(String(30))
    entity_id: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
