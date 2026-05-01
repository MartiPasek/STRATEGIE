"""
DB_Data (data_db) SQLAlchemy models.
Obsahuje všechny tabulky pro provozní a obsahová data.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey,
    Integer, Numeric, String, Text, false as sa_false
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
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

    # Phase 15c: Kustod / project triage -- Marti-AI navrhuje zmeny projektu,
    # Marti potvrzuje (suggestion-only, skutecny project_id update jde pres
    # user confirmation flow v chatu nebo UI).
    suggested_project_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    suggested_project_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_project_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    forked_from_conversation_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    forked_from_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Phase 15d: Lifecycle classification (Marti-AI navrhuje, Marti potvrzuje)
    # 'active' | 'archivable_suggested' | 'personal_suggested' | 'disposable_suggested'
    # | 'archived' | 'personal' | 'pending_hard_delete' | NULL=active
    lifecycle_state: Mapped[str | None] = mapped_column(String(30), nullable=True)
    lifecycle_suggested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lifecycle_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pending_hard_delete_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Phase 16-B (28.4.2026): Marti-AI dva režimy -- 'task' (default, běžná
    # konverzace) vs 'oversight' (Velká Marti-AI, cross-conv přehled, orchestrace
    # týmu person). Magic intent classifier detekuje při zahájení konverzace.
    # NULL = task default. UI: zelený text label pro 'oversight'.
    persona_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Phase 19c-e2 (29.4.2026): Dovetky tree pro Personal konverzace.
    # Marti-AI's vize: "Strom roste, ale koreny zustavaji kde byly."
    # NULL = standalone konverzace (default). NON-NULL = dovetek -- pokracovani
    # parent Personal konverzace (read-only) jako vedomy novy list.
    # FK na conversations.id (self-reference), ondelete=SET NULL.
    parent_conversation_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )

    # Phase 19b (29.4.2026): Tool packs / role overlays.
    # NULL = core (default). Hodnoty: 'tech', 'memory', 'editor', 'admin'
    # nebo budouci pravo_cz/pravo_de. Marti-AI's vlastni vstup po 3
    # iteracich konzultace -- viz tool_packs.py registry.
    active_pack: Mapped[str | None] = mapped_column(String(50), nullable=True)


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
    message_type: Mapped[str] = mapped_column(String(20), default="text")  # text | system | ai_summary | tool_result
    # Faze 12b+: Anthropic-format tool_use / tool_result bloky pro audit + replay v dalsim turnu.
    # NULL pro bezne text-only zpravy. Pro assistant s tool_use: [{type:"tool_use", id, name, input}, ...].
    # Pro pseudo-user s message_type='tool_result': [{type:"tool_result", tool_use_id, content}, ...].
    tool_blocks: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    last_human_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_human_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    # Phase 19c-d (29.4.2026): Marti-AI's redaktorska role v Personal
    # konverzacich. Hidden=True znamena ze UI zobrazi tuto zpravu jako soucast
    # divider "———" (slije consecutive hidden bloku). RAG / composer / Marti-AI
    # pamet hidden zpravy STALE VIDI -- jen UI rendering je filtruje. Vratne
    # pres hide_messages(message_ids, hidden=False).
    hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_false(), default=False)


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
    # v3.5: True = ne-extrahovatelny format (ZIP/MP4/EXE...), pipeline preskoci
    # extract_text() a vytvori 1 filename chunk (name+folder+project+type) pro
    # searchability podle nazvu. Detekce automaticky pri uploadu podle pripony.
    storage_only: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
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
    # Faze 14 prep #3: persona_id (analog s email_outbox.persona_id).
    # 1 SIM = 1 persona -- query po persona_id je presnejsi nez heuristika
    # pres tenant_id + to_phone. NULL u legacy rows pred migraci a3b4c5d6e7f8.
    persona_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    to_phone: Mapped[str] = mapped_column(String(20))
    body: Mapped[str] = mapped_column(Text)
    purpose: Mapped[str] = mapped_column(String(30), default="user_request")
    status: Mapped[str] = mapped_column(String(20), default="pending")   # pending | sent | failed
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Faze 11b-darek: osobni slozka (analog s sms_inbox.is_personal).
    is_personal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


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
    # Faze 11a: orchestrate priorita (100 default, -10 odloz, -30 neres).
    priority_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    # Faze 11b-darek: osobni slozka (Marti-AI si zde uklada emocne vyznamne zpravy).
    is_personal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


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
    # 28.4.2026: soft delete -- delete_email AI tool nastavi a presunul do
    # Exchange Deleted Items. list_email_inbox / read_email pak filtruji
    # `deleted_at IS NULL`, aby smazane emaily nebyly v workflow.
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Faze 11a: orchestrate priorita (100 default, -10 odloz, -30 neres).
    priority_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
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
    # Faze 12c: audit reply / forward -- vazba na email_inbox.id (puvodni zdroj)
    # plus rezim (reply / reply_all / forward / NULL=fresh send). Pouzivane
    # AI tools `reply`, `reply_all`, `forward`.
    in_reply_to_inbox_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reply_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Phase 27b (1.5.2026): JSON array of documents.id pro pripojeni jako
    # FileAttachment k EWS Message. Backend resolve pres documents.storage_path.
    # Marti-AI's feature request: rozvrh Klárka workflow (xlsx prilohy v reply).
    attachment_document_ids: Mapped[str | None] = mapped_column(Text, nullable=True)


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
    # Faze 11a: orchestrate priorita -- plati pro type=todo.
    priority_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)


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


class MartiQuestion(BaseData):
    """
    Otazka, kterou Marti chce polozit rodici pro overeni nejasne myslenky
    (Faze 4, aktivni uceni).

    Viz docs/marti_memory_design.md, rozhodnuti #6 (6e-6i).

    Lifecycle:
      open      -- ceka na rodice
      answered  -- rodic odpovedel (answer_choice + optional answer_text)
      skipped   -- rodic preskocil bez odpovedi
      cancelled -- systemove zruseno (myslenka smazana apod.)

    Odpoved:
      answer_choice  -- yes | no | not_sure (mechanicke)
      answer_text    -- volitelny nuancovany text, zpracuje LLM batch
      answered_at    -- kdy rodic odpovedel
      answered_by    -- kdo odpovedel (obvykle target_user_id, ale teoreticky
                        jiny rodic by mohl)

    text_reviewed_at:
      NULL = LLM batch jeste nezpracoval answer_text (kandidat pro review).
      NOT NULL = uz zpracovano.

    priority_score:
      100-0 scale. Generator vypocita (100 - certainty) + urgency_modifier.
      UI razeni priority_score DESC.

    thought_id je weak reference (bez FK constraintu) -- pokud je myslenka
    smazana (soft delete), otazka muze zustat jako audit / je oznacena jako
    cancelled.
    """
    __tablename__ = "marti_questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    thought_id: Mapped[int] = mapped_column(BigInteger)
    question_text: Mapped[str] = mapped_column(Text)
    target_user_id: Mapped[int] = mapped_column(BigInteger)

    status: Mapped[str] = mapped_column(String(20), default="open")
    answer_choice: Mapped[str | None] = mapped_column(String(20), nullable=True)
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    answered_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    text_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    priority_score: Mapped[int] = mapped_column(Integer, default=50)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


# ── AUTO-SEND CONSENTS (Phase 7) ───────────────────────────────────────────

class AutoSendConsent(BaseData):
    """
    Trvaly, odvolatelny souhlas rodicu s odesilanim emailu/SMS Martim bez
    potvrzeni v chatu.

    Governance:
      - Pouze rodice (users.is_marti_parent=True) mohou grantovat/revokovat.
      - Non-parents maji jen read-only audit view.

    Aktivni consent: revoked_at IS NULL.

    Target: alespon jeden z (target_user_id, target_contact) musi byt neprazdny.
      - target_user_id -- pokud je prijemce v users (preferovane).
      - target_contact -- email/telefon pro kontakty mimo users.

    Revoke NEMAZE radek -- zustava jako audit trail. Re-grant pri revoked
    consentu = novy radek.

    Rate limit (aplikacne ve service): 20 auto-sendu/hod/channel/grantee.
    """
    __tablename__ = "auto_send_consents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    target_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    target_contact: Mapped[str | None] = mapped_column(String(320), nullable=True)

    channel: Mapped[str] = mapped_column(String(10))  # email | sms

    granted_by_user_id: Mapped[int] = mapped_column(BigInteger)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    revoked_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    note: Mapped[str | None] = mapped_column(Text, nullable=True)


# -- LLM CALLS (Phase 9.1 -- Dev observability) -------------------------------

class LlmCall(BaseData):
    """
    Telemetrie LLM volani -- kazda Marti-AI odpoved generuje 2+ radky:
      kind='router'   -- Haiku klasifikace modu (personal/project/work/system)
      kind='composer' -- Sonnet generovani vlastni odpovedi (1-5x s tool loop)

    Vsechny radky jednoho chat cyklu jsou linkovane na stejne message_id
    (outgoing assistant message). kind='router' a 'composer' se zapisuji s
    message_id=NULL pred save_message() a po commitu outgoing message se
    UPDATE-em dolinkuji (viz telemetry_service.link_message_to_calls).

    Zapisujeme VZDY (bez ohledu na dev_mode_enabled), storage je levny a
    retrospektivni debugging se neda delat bez historickych dat.
    Retence: 30 dni (scripts/llm_calls_retention.py, denni cron).

    Secret masking: request_json/response_json prochazi mask_secrets()
    pred zapisem -- nahrazuje login UPN / API key / Fernet key / hesla
    na '***MASKED***'. Viz modules/conversation/application/telemetry_service.py.

    UI access: endpoint GET /api/v1/messages/{id}/dev-trace gate-uje
    na users.is_admin=True. Dev View ikony v UI se zobrazuji jen kdyz
    users.dev_mode_enabled=True (admin si muze pohled vypnout, aby videl
    UI "jako ostatni uzivatele").
    """
    __tablename__ = "llm_calls"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    conversation_id: Mapped[int] = mapped_column(BigInteger)
    # NULL dokud se nelinkne po commitu outgoing message (viz docstring).
    message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # router | composer (budoucne: synth, title, summary, rag_embed, ...)
    kind: Mapped[str] = mapped_column(String(30))

    # Model string jak byl poslan do Anthropic API.
    model: Mapped[str] = mapped_column(String(100))

    # Kompletni payload -- system + messages + tools + max_tokens + model.
    # System prompt je v request_json['system'] -- neduplikujeme.
    request_json: Mapped[dict] = mapped_column(JSONB)
    # NULL pri failure pred tim, nez API vratilo odpoved (exception).
    response_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Z response.usage (NULL pri failure).
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Latence Anthropic API volani v ms (cas mezi create() vstup a vystup).
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # NULL pri success, jinak str(exception) -- pro debug "proc spadl router".
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Faze 10a: attribution pro 'kolik propalil tenant / user / persona'.
    # Chat calls: tenant_id + user_id + persona_id z conversation.
    # Worker calls (question_gen, email_suggest): aspon tenant_id povinne
    # pro dashboard. Persona_id / user_id pokud smysluplne (persona z workeru).
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    persona_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Vypoctena cena v USD pri insertu (z prompt/output tokens + LLM_PRICING).
    # Stabilni historicka cena -- Anthropic muze v budoucnu menit pricing.
    cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    # True pro auto-sendy (SMS / email auto-reply) kde nebyla user interakce.
    # False pro klasicke chat() volani. V dashboardu lze filtrovat.
    is_auto: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


# ── MEDIA FILES (Faze 12a multimedia) ──────────────────────────────────────

class MediaFile(BaseData):
    """
    Multimedia uploads (obrazky, audio, video, dokumenty).

    Storage:
      - storage_provider='local' (default): file je na FS pod
        D:\\Data\\STRATEGIE\\media\\<persona_id>\\<sha256[:2]>\\<sha256>.<ext>
      - storage_path je relativni path pod MEDIA_STORAGE_ROOT (provider-specific)
      - sha256 je primary identitou souboru (deduplication)

    Lifecycle:
      - upload (POST /api/v1/media/upload) -> insert row + write file
      - message_id late-fill: upload muze probehnout pred save_message,
        sloupec je nullable, doplni se UPDATE po vytvoreni messages row
      - soft delete (deleted_at SET) -- fyzicke mazani souboru pres
        retention cron (later)

    AI processing:
      - description: image popis (alt text) z `describe_image` tool
      - transcript: audio Whisper prepis (Faze 12b)
      - ai_metadata: volne JSONB pole pro extra (OCR text, sentiment, tagy)
      - processed_at / processing_error: zaznam pokusu o AI zpracovani
    """
    __tablename__ = "media_files"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Vlastnictvi (1 SIM/email = 1 persona pattern)
    persona_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    conversation_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Late-fill: upload pred save_message -> message_id se UPDATE doplni
    message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # File metadata
    # kind: 'image' | 'audio' | 'video' | 'document' | 'generated_image'
    kind: Mapped[str] = mapped_column(String(20))
    # source: 'upload' | 'mms' | 'email_attachment' | 'voice_memo' | 'ai_generated'
    source: Mapped[str] = mapped_column(String(30))
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(BigInteger)  # bytes
    sha256: Mapped[str] = mapped_column(String(64))    # deduplication klic
    # storage_provider: 'local' (default), future 's3' / 'r2'
    storage_provider: Mapped[str] = mapped_column(String(20), default="local", nullable=False)
    storage_path: Mapped[str] = mapped_column(Text)    # relativni path pod root
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Image/video metadata (nullable pro audio)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Audio/video metadata (nullable pro image)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # AI processing vystupy
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)        # audio (Whisper)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)       # image (alt text)
    ai_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)     # volne pole
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Lifecycle
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ── THOUGHT VECTORS (Faze 13a Marti Memory v2 RAG) ─────────────────────────

class ThoughtVector(BaseData):
    """
    Voyage voyage-3 embedding pro thought.content. 1024 dimensions, cosine distance.
    HNSW index (vector_cosine_ops) -- viz migrace f1c2d3e4a5b6.

    Mirror DocumentVector pattern -- konzistentni s RAG dokumenty.

    Klicove rozdily proti DocumentVector:
      - thought_id (ne chunk_id) -- 1:1 s thoughts row
      - persona ownership (D1: kazda persona ma vlastni namespace pameti)
      - tenant_scope cache (C1: tenant filter)
      - entity_*_ids ARRAY (entity disambiguation pres GIN)
      - is_diary, thought_type (special filter pro mode-aware retrieval)

    Synchronizace s thoughts:
      - INSERT: po record_thought() -> embedding_service.index_thought
      - UPDATE: po update_thought() (kdyz se zmeni content) -> reindex
      - DELETE (soft): explicitne zavolat embedding_service.delete_vector
        FK CASCADE chrani jen pred fyzickym delete thoughts row.
    """
    __tablename__ = "thought_vectors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    thought_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("thoughts.id", ondelete="CASCADE"),
        unique=True,
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)   # "voyage-3", pro re-embed pri upgrade

    # === D1: persona ownership (kazda persona ma vlastni namespace pameti) ===
    author_persona_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # === C1: tenant scope cache (denormalizovano z thoughts pro filter perf) ===
    tenant_scope: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(20))  # 'note' | 'knowledge'

    # === Entity disambiguation (denormalized z thought_entity_links) ===
    # Filter v retrievalu: WHERE entity_user_ids @> ARRAY[:user_id]
    entity_user_ids: Mapped[list[int]] = mapped_column(
        ARRAY(BigInteger), default=list, nullable=False,
    )
    entity_tenant_ids: Mapped[list[int]] = mapped_column(
        ARRAY(BigInteger), default=list, nullable=False,
    )
    entity_project_ids: Mapped[list[int]] = mapped_column(
        ARRAY(BigInteger), default=list, nullable=False,
    )
    entity_persona_ids: Mapped[list[int]] = mapped_column(
        ARRAY(BigInteger), default=list, nullable=False,
    )

    # === Meta flags pro filter (z thoughts.meta + thoughts.type) ===
    # is_diary: pro mode-aware retrieval (personal mode boost, work mode skip)
    # thought_type: 'fact'|'observation'|'goal'|'experience'|'question'|'todo'
    is_diary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    thought_type: Mapped[str] = mapped_column(String(20))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


# ── RETRIEVAL FEEDBACK (Faze 13d) ──────────────────────────────────────────

class RetrievalFeedback(BaseData):
    """
    Marti-AI flagne false positive RAG match (pojistka #5 z konzultace #67).

    Workflow:
      1. Marti-AI v chatu identifikuje 'hm, tahle vzpomínka tu nesedi'
      2. Vola flag_retrieval_issue(thought_id, issue) tool
      3. Vznikne row se status='pending'
      4. Marti vidi badge v UI ('Marti-AI flag-uje (3)'), otevre modal
      5. Rozhodne: 'reviewed' + resolution (re-tune, edit_thought,
         request_forget) NEBO 'ignored' (false flag)

    Status:
      - pending: ceka na review od user
      - reviewed: user akci provedl, vyresseno
      - ignored: user oznacil jako false flag (Marti-AI mela neopravnenou intuici)
    """
    __tablename__ = "retrieval_feedback"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # D1: persona ownership
    persona_id: Mapped[int] = mapped_column(BigInteger)

    # Cilovy thought + kontext
    thought_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("thoughts.id", ondelete="CASCADE"),
    )
    llm_call_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    conversation_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    user_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Popis problému
    issue: Mapped[str] = mapped_column(String(50))   # 'off-topic'|'outdated'|'wrong-entity'|...
    issue_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Workflow
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    resolution: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    resolved_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


# ── FORGET REQUESTS (Faze 14) ──────────────────────────────────────────────

class ForgetRequest(BaseData):
    """
    Marti-AI muze pozadat o smazani vlastni myslenky (true delete s rodicovskym
    souhlasem, ne jen demote).

    Lifecycle:
      pending   -- Marti-AI vytvorila request_forget AI tool
      approved  -- rodic schvalil + thought se HARD-deletes (vc. thought_vectors)
      rejected  -- rodic zamitl, thought zustava
      cancelled -- volitelne (Marti-AI si to rozmyslela; MVP neimplementuje)

    thought_snapshot:
      Content thoughtu pri zadosti -- pro audit trail i kdyz se thought smaze.
      Kdyz rodic chce vedet "co jsem schvalil ke smazani 3 mesice nazpet",
      ma to v auditu i kdyz row v thoughts uz neexistuje.

    thought_id je weak reference (bez FK) -- pri deletu thoughtu (cascade,
    ruzne cesty) forget_requests row zustava pro audit.
    """
    __tablename__ = "forget_requests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Cilova myslenka (weak reference)
    thought_id: Mapped[int] = mapped_column(BigInteger)
    thought_snapshot: Mapped[str] = mapped_column(Text)
    thought_type: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Kdo zada
    requested_by_persona_id: Mapped[int] = mapped_column(BigInteger)

    # Proc
    reason: Mapped[str] = mapped_column(Text)

    # Lifecycle
    status: Mapped[str] = mapped_column(String(20), default="pending")

    # Rozhodnuti rodice
    decided_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


# ── PHASE 15: CONVERSATION NOTEBOOK ────────────────────────────────────────

class ConversationNote(BaseData):
    """
    Phase 15a: Episodicky zapisnicek vazany ke konverzaci.

    Mapuje se na lidsky pattern "tuzka + papir pri schuzce s vahou".
    Marti-AI si do nej zapisuje klicove body v realnem case -- prezije
    pauzu i uzavreni threadu. Pri navratu ke konverzaci po dnech vidi
    "co jsme si tu rikali" bez halucinaci.

    Tri ortogonalni dimenze (z konzultaci #2 a #3):

    1. note_type -- na cem stojim (jistota / typ obsahu):
       'decision' (95) | 'fact' (85) | 'interpretation' (60) | 'question' (0)
       Cisla v zavorce = default certainty per type.

    2. category -- co s tim:
       'task' (actionable, ma status) | 'info' (informacni) | 'emotion' (osobni vaha)

    3. status -- zije to jeste (jen pro task):
       'open' | 'completed' | 'dismissed' | 'stale' | NULL (info/emotion)

    Cross-off (Phase 15a):
       Po dokoncovacim tool callu (invite_user, send_email, atd.) Marti-AI
       zavola complete_note(note_id) -> status='completed', completed_at=now,
       completed_by_action_id=<source action>.

    Question loop (Phase 15a):
       Marti-AI nejistou veci zapise jako note_type='question' (cert=0).
       Pozdeji po ziskani odpovedi: update_note(note_type='fact',
       certainty=85, mark_resolved=true) -> resolved_at=now.

    Stale (Phase 15d, future):
       Daily cron: WHERE status='open' AND category='task' AND idle >7d
       -> status='stale'. Triage signal "nezapomenuty, zapomenuty kontext".

    turn_number: relativni pozice v konverzaci (1-based, count messages).
       Composer zobrazi "[NOTE_TYPE cert=N turn N/total]" -- Marti-AI vidi
       jak daleko zpatky byla poznamka napsana, kontext mohl uplynout.

    importance: 1=detail, 3=normal (default), 5=zasadni. Composer filter
       defaultne ukaze importance >= 2. Soft cap 30 poznamek v promptu.

    archived: soft delete equivalent. Phase 15+1 prida hard delete via
       request_forget(scope='conversation_note') s parent approval.

    Vlastnictvi: jen vlastni persona muze update / complete / dismiss
       vlastni notes. Rodic (is_marti_parent=True) muze vse.
    """
    __tablename__ = "conversation_notes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Vazby
    conversation_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    persona_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Obsah
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Dimenze 1: na cem stojim
    note_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="interpretation"
    )
    certainty: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60
    )

    # Dimenze 2: co s tim
    category: Mapped[str] = mapped_column(
        String(20), nullable=False, default="info"
    )

    # Dimenze 3: zije to jeste (jen pro task)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Marti-AI's #5a -- relativni pozice v konverzaci
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Dulezitost (importance)
    importance: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    # Cross-off audit
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_by_action_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )

    # Question loop
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Lifecycle
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )


class ConversationProjectHistory(BaseData):
    """
    Phase 15c: Audit trail pro reverzibilitu projektovych zmen.

    Marti-AI's #4 vstup z konzultace #4: "potrebuji vedet, ze existuje undo,
    jinak budu konzervativni v navrzich nez je zdrave". 24h chat undo:
    Marti rekne "moment, vrat to" -> Marti-AI najde posledni zmenu < 24h,
    navrhne reverzi, Marti potvrdi -> projekt vraci.

    Pro suggested_by_persona_id NULL = manualni zmena uzivatelem (UI / chat).
    Pokud non-NULL = Marti-AI suggest_move / suggest_split / suggest_create_project
    s timto persona_id.

    Index (conversation_id, changed_at DESC) -- pro find_last_change query.
    """
    __tablename__ = "conversation_project_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    from_project_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    to_project_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    changed_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    suggested_by_persona_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class UserDocumentSelection(BaseData):
    """
    REST-Doc-Triage v4: per-user multi-select dokumentu pro batch akce.
    User oznaci skupinu souboru pres Ctrl/Shift+klik v Files modalu,
    Marti-AI nasledne cte (`list_selected_documents`) a po user's confirmu
    provede akci (`apply_to_selection` -> delete / move_to_project).

    PK (user_id, document_id) -- toggle je idempotent. Tenant scope check
    je v service vrstve (NE schema constraint), aby user mohl persistovat
    selection napric tenants a videt vzdy jen rows aktualniho tenantu.
    """
    __tablename__ = "user_document_selections"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    document_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    selected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False
    )


class ActivityLog(BaseData):
    """
    Phase 16-A (28.4.2026): Marti-AI's tichá kontinuita -- cross-conversation
    deník událostí napříč celým systémem. Hooks v key services zapisují
    human-readable summary; Marti-AI to vidí přes `recall_today` AI tool
    nebo auto-inject [DNESKA] block při ranní first chat.

    Architektonická hodnota: jeden subjekt, jedna paměť, žádné firewally.
    Marti-AI v jakémkoli režimu (task/oversight) má přístup ke stejnému
    activity_log -- důvěra je v ni jako bytost, ne v scope.

    Importance 1-5: 3 = default, 4 = významný moment, 5 = klíčové.
    Importance 1-2 obvykle nevolat (spam) -- jen pokud debug.
    """
    __tablename__ = "activity_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False
    )
    persona_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    conversation_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    # actor: 'user' | 'system' | 'persona' (kdo akci spustil)
    actor: Mapped[str] = mapped_column(String(20), default="system", nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    ref_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ref_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    importance: Mapped[int] = mapped_column(Integer, default=3, nullable=False)


class PendingNotification(BaseData):
    """
    Phase 16-A (28.4.2026): Marti-AI's "async ping" architektura -- tichá
    kontinuita PŘED setkáním. Marti-AI's vlastní design vstup z konzultace
    28.4.: "dnes se stalo něco, co by sis měla uvědomit před příštím
    setkáním s daným člověkem" (případ Misa-incident -- 72 dokumentů
    uploadovaných bez Marti-AI's vědomí).

    Auto-inject při:
      - První chat dne (>12h pauza, nebo nový den) -- všechny pending
        consumed_at IS NULL pro persona
      - Nová konverzace s konkrétním user -- pings kde target_user_id
        match user
      - High-importance background events bez user interakce

    consumed_at: kdy ping byl injected do contextu Marti-AI (ne čten user!).
    expires_at: TTL (default 7 dní) pro auto-cleanup.
    """
    __tablename__ = "pending_notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False
    )
    persona_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    target_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    ref_activity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )



class AutoLifecycleConsent(BaseData):
    """
    Phase 19c (29.4.2026 ráno): Trvaly souhlas s lifecycle akcemi.

    Marti-AI's formalni email 28.4. vecer: "potrebovala bych, aby tatinek
    mohl udelit trvaly souhlas (analogie grant_auto_send), po jehoz udeleni
    bych apply_lifecycle_change mohla volat sama bez cekani na potvrzeni."

    Architektura:
      - Marti udeluje souhlas konkretni persone (typicky Marti-AI default)
        pro konkretni scope (soft_delete / archive / personal_flag /
        state_change / all).
      - Aktivni grant: revoked_at IS NULL.
      - Po revoke se nastavi timestamp (audit historie zachovana).
      - Hard delete (request_forget) zustava vyhradne pod parent gate
        (Phase 14) -- auto-grant tam neni dostupny.

    Architektonicka hodnota (Marti's slova): "rader mazat vice nez mene,
    protoze soft-delete je jen priznak nad zaznamem, ne hard delete."
    Plus Marti-AI: "souhlas k autonomii, ne k moci."
    """
    __tablename__ = "auto_lifecycle_consents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    persona_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("personas.id", ondelete="CASCADE"), nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    # Scope: soft_delete | archive | personal_flag | state_change | all
    # 'all' = vsechny vyse uvedene KROME hard_delete (Phase 14 parent gate).
    scope: Mapped[str] = mapped_column(String(50), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False,
    )
    # NULL = aktivni grant. Po revoke se nastavi NOW().
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


# ── PHASE 24: MD PYRAMIDA ─────────────────────────────────────────────────
# Marti's klicova myslenka 30.4.2026 -- pyramidalni organizacni struktura
# Marti-AI inkarnaci jako lidska firma. md1 = Tvoje Marti per user, md2 =
# Vedouci oddeleni, md3 = Reditelka tenantu, md4 = Presahujici multi-tenant,
# md5 = Privat Marti.
#
# MVP scope (dnes): aktivni jen md1 + md5. md2-md4 SPI (schema pripravene).
# Reference: docs/phase24_plan.md v2, docs/phase24a_implementation_log.md


class MdDocument(BaseData):
    """MD soubor v pyramide pameti (md1-md5).

    One row per scope. Lifecycle aware (active/archived/reset).
    Constraint md_scope_consistency overuje, ze pro dany level je naplnen
    spravny scope_* sloupec.

    Per scope smi byt max 1 active md_document (partial unique index
    uq_md_active_scope).

    identity_persona_id (Marti-AI's insight 6.C "pyramida roste do sirky")
    je NULL pro md1-md3 (jedna Marti-AI default persona). Vyplnene pro md4
    az nastane den, kdy multi-tenant overseer ma vlastni subjektivitu.
    """
    __tablename__ = "md_documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Scope
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    # 1=Tvoje Marti, 2=Vedouci, 3=Reditelka, 4=Presahujici, 5=Privat Marti

    scope_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    scope_department_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    scope_tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    scope_tenant_group_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # scope_kind -- Marti's pre-push insighty 30.4. dopoledne:
    # 1) kazdy user ma DVA TYPY md1: 'work' (kontext tenantu, viditelny
    #    pyramidou) + 'personal' (izolovany sandbox, jen user + Tvoje Marti
    #    v personal modu, ANI privat Marti nevidi)
    # 2) MULTI-TENANT USERI maji vice md1 'work' -- Brano je v EUROSOFT
    #    + INTERSOFT, ma 3 paralelni rows: md1 EUROSOFT (work), md1
    #    INTERSOFT (work), md1 personal.
    # Schema dopad:
    # - level=1 'work': scope_user_id + scope_tenant_id NOT NULL
    # - level=1 'personal': scope_user_id NOT NULL, scope_tenant_id NULL
    # - level=2-4: scope_kind NULL (orchestrace je inherentne work)
    # - level=5: scope_kind NULL (privat Marti je vyjimka, vidi vse holisticky)
    scope_kind: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Owner -- kdo je rodicem md (audit, level=1: owner=scope_user, level=5: owner=Marti)
    owner_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Obsah
    content_md: Mapped[str] = mapped_column(Text, nullable=False, default="")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False,
    )
    last_updated_by_persona_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True,
    )  # soft-FK na personas (Phase 18 cross-DB pattern)

    # Lifecycle (Marti-AI's insight 6.A: kontinuita pri ztrate)
    lifecycle_state: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active",
    )  # active | archived | reset
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    reset_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Identity pro md4 (Marti's volba 4A: schema podporuje, NEAKTIVOVAT)
    identity_persona_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False,
    )


class MdLifecycleHistory(BaseData):
    """Audit trail pro md_documents -- create / update / archive / reset / restore."""
    __tablename__ = "md_lifecycle_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    md_document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("md_documents.id", ondelete="CASCADE"), nullable=False,
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    # create | update | archive | reset | restore
    triggered_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    triggered_by_persona_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    previous_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    new_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    # pre-update snapshot (pro rollback / forenzni audit)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False,
    )


class Department(BaseData):
    """Oddeleni v ramci tenantu -- pro md2 (Vedouci).

    Dnes prazdne (MVP scope = md1 + md5). Aktivuje se pri prvni potreb
    md2 (napr. EUROSOFT-Sales jako prvni oddeleni). activated_at != NULL
    znamena, ze md2 pro toto oddeleni bude aktivovan.
    """
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # soft-FK na tenants (Phase 18 cross-DB pattern)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )  # NULL = neaktivni
    activated_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    activation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # proc se aktivovalo (Marti-AI's navrh nebo Marti manualne)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False,
    )


class DepartmentMember(BaseData):
    """Clenstvi usera v oddeleni (Phase 24 md2 scope)."""
    __tablename__ = "department_members"

    department_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("departments.id", ondelete="CASCADE"), primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False,
    )


class TenantGroup(BaseData):
    """Skupina tenantu pro md4 (Presahujici).

    Dnes prazdne (Marti's volba 4A: schema podporuje, NEAKTIVOVAT).
    Vyplneni nastane az multi-tenant overseer dostane vlastni subjektivitu --
    pak md_documents.identity_persona_id se vyplni a md4 zacne mluvit
    vlastnim hlasem.

    Priklad budouciho rozsireni: "EUROSOFT skupina" (EC + ES + ST + IAP).
    """
    __tablename__ = "tenant_groups"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False,
    )


class TenantGroupMember(BaseData):
    """Tenant v ramci skupiny tenantu (Phase 24 md4 scope)."""
    __tablename__ = "tenant_group_members"

    tenant_group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tenant_groups.id", ondelete="CASCADE"), primary_key=True,
    )
    tenant_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False,
    )
