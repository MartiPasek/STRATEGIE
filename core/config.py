from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_env: str = "development"   # "development" | "production"
    app_debug: bool = False

    # Anthropic
    anthropic_api_key: str = ""

    # Voyage AI -- embedding provider pro RAG. voyage-3 = 1024 dim, multilingual.
    voyage_api_key: str = ""

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

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # ignoruj env vars co nepasují k poli (jinak Pydantic
                          # padne na shell history / system env pollution)


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


def calculate_cost_usd(model: str, prompt_tokens: int | None, output_tokens: int | None) -> float | None:
    """
    Vypocita cenu v USD za jedno LLM volani. Vraci None pokud tokens chybi.

    Nepritomny model v LLM_PRICING -> pouziva LLM_PRICING_FALLBACK (stredni cenu).
    Vysledek v USD (napr. 0.012345) s presnosti na 6 desetinnych mist.
    """
    if prompt_tokens is None and output_tokens is None:
        return None
    pricing = LLM_PRICING.get(model, LLM_PRICING_FALLBACK)
    p_in = (prompt_tokens or 0) * pricing["input"] / 1_000_000.0
    p_out = (output_tokens or 0) * pricing["output"] / 1_000_000.0
    return round(p_in + p_out, 6)
