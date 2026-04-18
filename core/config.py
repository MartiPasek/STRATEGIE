from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_env: str = "development"
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

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
