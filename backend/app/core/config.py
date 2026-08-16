from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings loaded from environment variables."""

    APP_NAME: str = "EnterpriseAIMailOPs_MIPRO"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Database Configuration (PostgreSQL)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "mailops_db"
    DATABASE_URL: str | None = None

    # Authentication & Security Configuration
    SECRET_KEY: str = "dev_secret_key_change_in_production_min_64_bytes_secure_random_key_mailops"
    ENCRYPTION_KEY: str = "4xW8Z3vK9uF2mP7qR1tY6bV5cN8jL0kH4gF2dS6aQ1w="
    GOOGLE_CLIENT_ID: str = "your_google_client_id_here"
    GOOGLE_CLIENT_SECRET: str = "your_google_client_secret_here"
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    FRONTEND_URL: str = "http://localhost:5173"
    SESSION_EXPIRE_HOURS: int = 24

    @property
    def SESSION_COOKIE_NAME(self) -> str:
        """Use __Host- prefix in production for host-locking security."""
        return "__Host-mailops_session" if self.APP_ENV == "production" else "mailops_session"

    @property
    def SESSION_COOKIE_SECURE(self) -> bool:
        """Require Secure cookie attribute in production (HTTPS)."""
        return self.APP_ENV == "production"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Construct SQLAlchemy database connection URI."""
        if self.DATABASE_URL:
            # Normalize driver if user supplied standard postgresql://
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
            return self.DATABASE_URL
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
