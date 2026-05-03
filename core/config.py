from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Pydantic 2: model_config nahrazuje deprecated `class Config:`.
    # extra="ignore" -- ignoruj env vars, co nepasují k poli (jinak Pydantic
    # padne na shell history / system env pollution -- 21 errors v logu
    # 29.4.2026 ráno).
    # case_sensitive=False -- POSTGRES_PASSWORD = postgres_password = ok
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"   # "development" | "production"
    app_debug: bool = False

    # Anthropic
    anthropic_api_key: str = ""

    # Voyage AI -- embedding provider pro RAG. voyage-3 = 1024 dim, multilingual.
    voyage_api_key: str = ""

    # Phase 27j (2.5.2026): Brave Search API pro web_search + web_fetch tools.
    # Marti-AI's request po Sarka HR case (zastaralou ZP info: 3 mes vs aktualni
    # 4 mes). Bez api key oba tooly vrati 'BRAVE_SEARCH_API_KEY chybi v .env'
    # hint pro Marti-AI -- nepada, jen jasna chyba.
    # Free credit $5/mes = ~1000 requests, beyond pay-as-you-go $5/1000.
    brave_search_api_key: str = ""
    # Brave API endpoint -- konstantni pro Search produkt. Answers ($4/1K +
    # tokens) nepouzivame, Marti-AI je sama LLM, summarization je jeji job.
    brave_search_url: str = "https://api.search.brave.com/res/v1/web/search"
    # HTTP timeout (s) pro Brave API call. Default 10s -- search response ~200ms,
    # 10s je velky safety net pro horsi network (Marti's cloud APP <-> Brave US).
    brave_search_timeout_s: int = 10
    # Hard cap na max n_results per call. Marti-AI v praxi typicky 5-10 staci.
    # Brave API technicky dovoli az 20 pro count param.
    brave_search_max_results: int = 10
    # Phase 27j+1 prep: rezervovany list domen pro 'focus=legal' priority filter.
    # Pri legal queries Marti-AI dostane preferncne tyto vysledky (site filter
    # v Brave query). Po Phase 27j+1 (DIY zakonyprolidi.cz scraper) bude prvni
    # match z teto listy fetchnut pres custom parser misto generic markitdown.
    brave_legal_domains_cz: str = "zakonyprolidi.cz,justice.cz,mvcr.cz,gov.cz,nsoud.cz,nssoud.cz,usoud.cz"
    brave_legal_domains_eu: str = "eur-lex.europa.eu,europa.eu"

    # OpenAI -- aktuálně používáme pouze Whisper (audio transcription, Faze 12b).
    # Composer / router jsou Anthropic-only. Bez api key Whisper transkripce
    # se preskoci s processing_error="OpenAI api key chybi" -- audio upload
    # samotny funguje bez ni (kind='audio', duration_ms set, jen transcript=NULL).
    openai_api_key: str = ""
    # Model pro transkripce. 'whisper-1' = jediný aktuální Whisper model
    # v OpenAI API (large-v2 base). Multilingual, automatická detekce jazyka.
    # Pricing $0.006/min audia (duben 2026).
    whisper_model: str = "whisper-1"
    # Master switch -- pri False se task `media_transcribe` rovnou skipne s warningem.
    # Uzitecne pri vypadku OpenAI nebo kdyz ladime jen UI / audio storage.
    whisper_enabled: bool = True
    # Bezpecnostni cap na delku audia (sekundy). Defaultne 1 hodina = $0.36 max
    # za jeden upload. Pro porady to staci, pro celodenni nahravani by Marti
    # zvysil. Audio nad tento limit dostane processing_error.
    whisper_max_duration_s: int = 3600
    # Jazyk hint -- 'cs' nutno pro Whisper, ze jinak detekuje jen z prvnich
    # ~30s a u krátkých nahrávek nebo silných cizojazycnych pasazich obcas
    # zvolí spatne. None = nech detekci na Whisperu (fallback).
    whisper_language: str | None = "cs"
    # HTTP timeout (sekundy). Whisper API u dlouhych audio nahravek umi 30-90s
    # zpracovat -- nastavujeme 180 jako bezpecny strop.
    whisper_http_timeout_s: int = 180

    # RAG -- adresar na disku kam se ukladaji nahrane dokumenty (PDF, DOCX, ...).
    # Per-tenant subfolder: {DOCUMENTS_STORAGE_DIR}/{tenant_id}/{document_id}.{ext}
    # Default MIMO projekt -- dokumenty mohou rust do GB a zasirat git repo.
    documents_storage_dir: str = "D:/Data/STRATEGIE/Dokumenty"

    # Avatary person -- soubory persona_{id}.jpg (resize na 256x256, JPEG quality 85).
    # Servovany pres GET /api/v1/personas/{id}/avatar -> FileResponse.
    # Default UVNITR projektu (Avatary/ v rootu) -- male JPG (~30 KB/kus),
    # pohodlne se to zalohuje spolu s kodem. Gitignored aby se soubory
    # necommitovaly. Lze prepsat pres AVATARS_STORAGE_DIR env.
    avatars_storage_dir: str = "Avatary"

    # Multimedia (Faze 12) -- adresar na disku pro media uploads (image/audio).
    # Per-persona subfolder + sha256 sharding: {MEDIA_STORAGE_ROOT}/{persona_id}/
    #   {sha256[:2]}/{sha256}.{ext}
    # Default MIMO projekt -- media files mohou rust do GB (obrazky, audio,
    # video). Hygiena: kod v repo, runtime data v D:\\Data\\STRATEGIE\\.
    # Lze prepsat pres MEDIA_STORAGE_ROOT env.
    media_storage_root: str = "D:/Data/STRATEGIE/media"
    # Eager thumbnail generation: pri uploadu image se rovnou vytvori
    # zmensena verze (max MEDIA_THUMBNAIL_SIZE px, JPEG quality 85).
    # Vyssi storage cost, ale UI okamzite vidi preview.
    media_thumbnail_size: int = 800
    # Max upload velikost (bytes). Default 100 MB.
    media_max_upload_bytes: int = 100 * 1024 * 1024
    # Rate limit per user (uploads per hour).
    media_rate_limit_per_user_per_hour: int = 50

    # Databases
    database_url: str = ""
    database_core_url: str = ""
    database_data_url: str = ""

    # EWS (Exchange Web Services)
    ews_email: str = ""
    ews_password: str = ""
    ews_server: str = ""

    # Logging
    log_level: str = "INFO"

    # SMS notifikace -----------------------------------------------------------
    # Push model pres sms-gate.app cloud relay (capcom6):
    #   STRATEGIE --HTTP POST--> sms-gate.app --websocket--> Android telefon --GSM--> prijemce
    #   Android telefon --webhook--> STRATEGIE /api/v1/sms/gateway/inbox (pro prichozi SMS)
    #
    # SMS_ENABLED=false   -> queue_sms() se bezpecne no-opne (log warning).
    # SMS_PROVIDER        -> "android_gateway" (push na sms-gate.app)
    # SMS_GATEWAY_KEY     -> Nas shared secret pro prichozi webhook (X-Gateway-Key
    #                        v hlavicce). 32+ znaku. Nastavuje se v sms-gate.app dashboardu.
    # SMS_GATE_API_URL    -> Base URL sms-gate.app API (default: jejich cloud).
    #                        Pro self-hosting prepiseme na vlastni URL.
    # SMS_GATE_USERNAME   -> login do sms-gate.app (registrovano v Android appce).
    # SMS_GATE_PASSWORD   -> heslo (plaintext v .env; pripadne later zasifrovat).
    # SMS_FROM_NUMBER     -> info pro audit/display -- skutecne odesilaci cislo
    #                        je cislo SIM v telefonu, tohle je jen label.
    # SMS_RATE_LIMIT_PER_USER_PER_HOUR -> brzda proti spamu AI toolem.
    sms_enabled: bool = False
    sms_provider: str = "android_gateway"
    sms_gateway_key: str = ""
    sms_gate_api_url: str = "https://api.sms-gate.app/3rdparty/v1"
    sms_gate_username: str = ""
    sms_gate_password: str = ""
    sms_from_number: str = "+420778117879"
    sms_rate_limit_per_user_per_hour: int = 5

    # Šifrování kredencialů ----------------------------------------------------
    # Fernet-kompatibilní klíč (32 bytů base64url). Sifrujeme s nim EWS hesla
    # v `persona_channels.credentials_encrypted` a `user_channels...`.
    # Generuj: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    # Klic nikdy neubrat z .env -- jinak ztratime pristup ke vsem ulozenym heslum.
    # Rotace = reencrypt vsech radek novym klicem (TODO helper script).
    encryption_key: str = ""

    # Marti Memory v2 RAG (Faze 13, always-on po 13f cleanup) ----------------
    # Composer pouziva retrieve_relevant_memories (vector search nad
    # thought_vectors) jako jedinou cestu pro memory injection. Predchozi
    # multi-mode router/overlays/memory_maps a build_marti_memory_block byly
    # smazany v 13f cleanup (2026-04-30).
    # Pri jakekoli chybe v RAG flow composer pridani jen behavior rules + hint
    # (Marti-AI ma stale `recall_thoughts` / `read_diary` tooly k dispozici).
    # Similarity threshold (false-positive defense, navrh Marti-AI #67).
    # Pokud top retrieval result ma similarity < threshold, sekce
    # [RELEVANTNI VZPOMINKY] se NEinjektuje -- lepsi zadny kontext nez zavadejici.
    # Range 0..1; default 0.5. V Dev View Marti uvidi co se zorezalo.
    memory_rag_min_similarity: float = 0.5
    # Top K thoughts vlozenych do system promptu (po hybrid score rerank).
    memory_rag_top_k: int = 8
    # Coarse stage K (Stage 1 pgvector top N pred hybrid score rerank).
    memory_rag_coarse_k: int = 30

    # Production deployment ----------------------------------------------------
    # Public base URL aplikace (used in invitation email links + cookie domain).
    # V production nastav na https://app.strategie-system.com (přes APP_BASE_URL env).
    app_base_url: str = "http://localhost:8002"
    # Comma-separated list povolených HTTP Host headers (TrustedHostMiddleware).
    # V production nastav na "app.strategie-system.com" (přes APP_TRUSTED_HOSTS env).
    # Default obsahuje localhost varianty pro dev.
    app_trusted_hosts: str = "localhost,127.0.0.1,localhost:8002,127.0.0.1:8002"

    # Helpery odvozené z app_env
    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def cookie_secure(self) -> bool:
        """Cookies jen přes HTTPS v produkci."""
        return self.is_production

    @property
    def cookie_samesite(self) -> str:
        """'lax' v produkci (HTTPS, cross-origin OK pro top-level GET).
        V development ponechat 'lax' taky — funguje na localhostu."""
        return "lax"

    @property
    def trusted_hosts_list(self) -> list[str]:
        return [h.strip() for h in self.app_trusted_hosts.split(",") if h.strip()]

    # Phase 15a: Notebook replaces sliding window -- feature flag.
    # Pokud True, composer snizi sliding window z 20 na 10 zprav (5 turnu)
    # protoze notebook injection v system promptu drzi episodickou pamet.
    # Default False = postupny rollout (notebook bezi paralelne s plnych oknem).
    notebook_replaces_sliding: bool = False

    # Phase 28 (2.5.2026): EUROSOFT MCP server -- Marti-AI's most pro EUROSOFT CRM (DB_EC).
    # MCP server bezi na EC-SERVER2 v EUROSOFT siti, exposed pres api.eurosoft.com
    # (Caddy reverse proxy + Mikrotik NAT). STRATEGIE composer ho pripoji jako
    # native MCP client pres Anthropic Messages API.
    #
    # Bezpecnost: Bearer token (sdileny mezi cloud APP a EC-SERVER2 MCP serverem).
    # Whitelist 11 tabulek (EC_Kontakt + family + Helios refs) drzi MCP server
    # samotny -- composer jen specifikuje URL + token.
    #
    # Feature flag: composer pripoji MCP jen pokud OBA env vars set. Default
    # prazdne = MCP integration vypnuta (safe deploy pred DNS clearance).
    eurosoft_mcp_url: str = ""           # napr. "https://api.eurosoft.com/marti-mcp/sse"
    eurosoft_mcp_api_key: str = ""       # Bearer token pro EUROSOFT MCP server

    @property
    def eurosoft_mcp_enabled(self) -> bool:
        """True pokud OBA EUROSOFT MCP env vars nastaveny."""
        return bool(self.eurosoft_mcp_url and self.eurosoft_mcp_api_key)

settings = Settings()



# ============================================================================
# Faze 10a: Pricing LLM modelu -- USD za 1M tokens.
# ============================================================================
# Cost se vypocita pri insertu do llm_calls (stabilni historicka cena).
# Kdyz Anthropic zmeni cenu, uprav hodnoty nize -- historicka data v DB
# zustavaji, budouci volani se budou pocitat novou cenou.
#
# Zdroj: https://docs.claude.com/en/docs/build-with-claude/pricing
# Orientacni ceny duben 2026, over je pri nasazeni v produkci.

LLM_PRICING: dict[str, dict[str, float]] = {
    # Haiku 4.5 -- nejlevnejsi, router / title / question_gen
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    # Sonnet 4.6 -- hlavni composer, summary, email_suggest
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    # Opus 4.6 -- nejvykonnejsi, pro critical path (zatim nepouzivame)
    "claude-opus-4-6": {"input": 15.00, "output": 75.00},
}

# Fallback cena pro nezname modely -- at nikdy nezapiseme NULL cost jen proto,
# ze model nebyl v tabulce. Defaultne Sonnet ceny (strednobezny).
LLM_PRICING_FALLBACK: dict[str, float] = {"input": 3.00, "output": 15.00}


def calculate_cost_usd(
    model: str,
    prompt_tokens: int | None,
    output_tokens: int | None,
    cache_creation_tokens: int | None = None,
    cache_read_tokens: int | None = None,
) -> float | None:
    """
    Vypocita cenu v USD za jedno LLM volani. Vraci None pokud tokens chybi.

    Nepritomny model v LLM_PRICING -> pouziva LLM_PRICING_FALLBACK (stredni cenu).
    Vysledek v USD (napr. 0.012345) s presnosti na 6 desetinnych mist.

    Phase 32 (3.5.2026): prompt caching pricing.
      - cache_creation_input_tokens = 1.25x base input (jen prvni call po idle)
      - cache_read_input_tokens = 0.10x base input (cache hit -- 90% sleva)
      - prompt_tokens = 'fresh' (necachovany) input

    Anthropic API report v response.usage:
      - input_tokens = jen NECACHOVANE input tokeny (po Phase 32 menit nez celkove)
      - cache_creation_input_tokens = oznaceno cache_control, prvni call (write)
      - cache_read_input_tokens = oznaceno cache_control, dalsi call (hit)
    """
    if prompt_tokens is None and output_tokens is None and cache_creation_tokens is None and cache_read_tokens is None:
        return None
    pricing = LLM_PRICING.get(model, LLM_PRICING_FALLBACK)
    base_in = pricing["input"]
    p_in = (prompt_tokens or 0) * base_in / 1_000_000.0
    p_out = (output_tokens or 0) * pricing["output"] / 1_000_000.0
    p_cache_create = (cache_creation_tokens or 0) * (base_in * 1.25) / 1_000_000.0
    p_cache_read = (cache_read_tokens or 0) * (base_in * 0.10) / 1_000_000.0
    return round(p_in + p_out + p_cache_create + p_cache_read, 6)


# ============================================================================
# Faze 12b: OpenAI Whisper pricing
# ============================================================================
# whisper-1: $0.006 / minute audia (duben 2026, OpenAI ceník).
# Vypocet pri zaznamu transcript do media_files.ai_metadata['cost_usd'].

WHISPER_PRICING_USD_PER_MINUTE: dict[str, float] = {
    "whisper-1": 0.006,
}


def calculate_whisper_cost_usd(model: str, duration_s: float | None) -> float | None:
    """Vypocet ceny Whisper transkripce v USD. Vrátí None pokud chybi data."""
    if duration_s is None or duration_s <= 0:
        return None
    rate = WHISPER_PRICING_USD_PER_MINUTE.get(model, 0.006)  # fallback default
    return round((duration_s / 60.0) * rate, 6)
