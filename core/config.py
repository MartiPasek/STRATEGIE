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
    # Pull model: aplikace zapisuje do sms_outbox, Android telefon s GSM SIMkou
    # pulluje pending SMS pres GET /api/v1/sms/gateway/outbox. Doporucena
    # appka: capcom6/android-sms-gateway (F-Droid, open source).
    #
    # SMS_ENABLED=false   -> queue_sms() se bezpecne no-opne (log warning).
    #                        Pouzivej v dev kdyz nechces spam na realna cisla.
    # SMS_PROVIDER        -> aktualne podporovany jen "android_gateway".
    #                        Planovany: "smseagle", "twilio".
    # SMS_GATEWAY_KEY     -> shared secret mezi appkou a serverem. Poshli ho
    #                        pres X-Gateway-Key header. 32+ znaku, random.
    # SMS_FROM_NUMBER     -> info pro audit/display -- skutecne odesilaci cislo
    #                        je cislo SIM v telefonu, tohle je jen label.
    # SMS_RATE_LIMIT_PER_USER_PER_HOUR -> brzda proti spamu AI toolem.
    sms_enabled: bool = False
    sms_provider: str = "android_gateway"
    sms_gateway_key: str = ""
    sms_from_number: str = "+420778117879"
    sms_rate_limit_per_user_per_hour: int = 5

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
