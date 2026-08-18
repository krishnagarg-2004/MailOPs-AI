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

    # Gmail Synchronization Configuration
    INITIAL_SYNC_LIMIT: int = 500
    ATTACHMENT_MAX_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB

    # AI Engine & Gemini Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    AI_PROVIDER_TYPE: str = "mock"  # Options: "gemini", "mock" (default to mock for offline/dev safety)
    AI_MAX_RETRIES: int = 3
    AI_TIMEOUT_SECONDS: float = 30.0
    AI_CONFIDENCE_THRESHOLD: float = 0.6

    # Document Intelligence & OCR Configuration
    DOC_MAX_EXTRACT_CHARS: int = 20000        # Character limit per document
    DOC_OCR_MIN_CHAR_THRESHOLD: int = 30      # Min chars/page before triggering OCR fallback
    DOC_MAX_PDF_PAGES: int = 20               # Max PDF pages to parse per file
    DOC_MAX_OCR_PAGES: int = 10               # Max pages to run through Tesseract OCR
    DOC_MAX_IMAGE_PIXELS: int = 25_000_000    # Max allowed image resolution (25 Megapixels)
    DOC_MAX_IMAGE_DIMENSION: int = 6000       # Max image dimension in pixels
    DOC_ZIP_MAX_UNCOMPRESSED_BYTES: int = 50 * 1024 * 1024  # 50 MB DOCX uncompressed limit
    DOC_ZIP_MAX_RATIO: float = 10.0           # Max ZIP compression ratio (ZIP bomb defense)
    OCR_TESSERACT_PATH: str | None = None     # Optional explicit path to tesseract binary
    # Semantic Search & RAG Configuration
    EMBEDDING_MODEL: str = "text-embedding-004"
    EMBEDDING_DIMENSION: int = 768            # Strict dimension verification invariant
    VECTOR_SEARCH_TOP_K: int = 5
    # Action Graph & Relationship Layer Configuration
    GRAPH_MAX_TRAVERSAL_DEPTH: int = 10       # Max BFS traversal depth for dependency resolution

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
