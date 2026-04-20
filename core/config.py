from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_env: str = "development"   # "development" | "production"
    app_debug: bool = False

    # Anthropic
    anthropic_api_key: str = ""

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
