from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_env: str = "development"
    app_debug: bool = False

    # Anthropic
    anthropic_api_key: str = ""

    # Database
    database_url: str = ""

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
