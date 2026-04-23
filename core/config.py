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

    # Multi-mode Marti-AI routing (Fáze 9) -------------------------------------
    # Když True, chat flow prochází routerem -> classifikuje módu (personal /
    # project / work / system) a podle toho vybere overlay + memory map místo
    # dnešního build_marti_memory_block + build_marti_diary_block.
    # Default False = dnešní chování (safe, base-marti-2026-04-24).
    # Rollout: `MARTI_MULTI_MODE_ENABLED=true` v .env a restart STRATEGIE-API.
    # Při jakékoli chybě v multi-mode flow composer spadne na existující
    # behavior -- Marti zůstane funkční.
    marti_multi_mode_enabled: bool = False

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
