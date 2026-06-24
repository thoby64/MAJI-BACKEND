"""
Global Backend Configuration
Centralized environment and application settings
"""

import os
from typing import Any, List
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


RUNTIME_ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()
SETTINGS_ENV_FILE = None if RUNTIME_ENVIRONMENT == "production" else ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=SETTINGS_ENV_FILE,
        case_sensitive=False,
        extra="ignore",
    )
    
    # ===== Application Settings =====
    app_name: str = "Majiscope Backend"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")

    # ===== Database Settings =====
    database_url: str = Field(
        default="postgresql+psycopg://user:password@localhost:5432/majiscope",
        alias="DATABASE_URL",
    )

    # ===== Security Settings =====
    secret_key: str = Field(
        default="your-secret-key-change-in-production-12345",
        alias="SECRET_KEY",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # ===== Frontend Configuration =====
    # IMPORTANT: This is used for CORS and rendering frontend URLs
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")
    public_backend_url: str = Field(default="", alias="PUBLIC_BACKEND_URL")
    cors_origins_raw: str = Field(default="", alias="CORS_ORIGINS")
    cors_origin_regex: str = Field(
        default=r"^https:\/\/.*\.onrender\.com$",
        alias="CORS_ORIGIN_REGEX",
    )
    
    # ===== CORS Settings =====
    default_cors_origins: List[str] = [
        "http://localhost:3000",      # Development frontend
        "http://127.0.0.1:3000",      # Alternative localhost
        "http://192.168.1.2:8081",    # Expo development server
        "http://10.0.2.2:8081",       # Android emulator
        "exp://192.168.1.2:8081",     # Expo Go app
        "exp://10.0.2.2:8081",        # Expo Go on Android emulator
    ]
    cors_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]

    # ===== Invitation & Email Settings =====
    invite_token_expiry_hours: int = Field(default=72, alias="INVITE_TOKEN_EXPIRY_HOURS")
    password_reset_token_expiry_hours: int = Field(default=2, alias="PASSWORD_RESET_TOKEN_EXPIRY_HOURS")
    resend_api_key: str = Field(default="", alias="RESEND_API_KEY")
    resend_from_email: str = Field(default="", alias="RESEND_FROM_EMAIL")
    resend_from_name: str = Field(default="Majiscope", alias="RESEND_FROM_NAME")
    smtp_host: str = Field(default="", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str = Field(default="", alias="SMTP_USERNAME")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(default="", alias="SMTP_FROM_EMAIL")
    smtp_from_name: str = Field(default="Majiscope", alias="SMTP_FROM_NAME")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")

    # ===== Password Hashing =====
    password_hash_algorithm: str = "bcrypt"
    password_bcrypt_rounds: int = 12

    # ===== API Settings =====
    api_prefix: str = "/api"
    
    # ===== Server Settings =====
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # ===== Runtime database startup behavior =====
    run_startup_migrations: bool = Field(default=True, alias="RUN_STARTUP_MIGRATIONS")
    run_startup_schema_sync: bool = Field(default=True, alias="RUN_STARTUP_SCHEMA_SYNC")

    # ===== Optional startup import =====
    legacy_duwasa_import_on_startup: bool = Field(default=False, alias="LEGACY_DUWASA_IMPORT_ON_STARTUP")
    legacy_duwasa_import_csv_path: str = Field(default="", alias="LEGACY_DUWASA_IMPORT_CSV_PATH")
    legacy_duwasa_import_strict: bool = Field(default=False, alias="LEGACY_DUWASA_IMPORT_STRICT")
    legacy_duwasa_import_limit: int | None = Field(default=None, alias="LEGACY_DUWASA_IMPORT_LIMIT")

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_value(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "production"}:
                return False
        return bool(value)

    @field_validator(
        "smtp_use_tls",
        "run_startup_migrations",
        "run_startup_schema_sync",
        "legacy_duwasa_import_on_startup",
        "legacy_duwasa_import_strict",
        mode="before",
    )
    @classmethod
    def parse_boolean_values(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    @model_validator(mode="after")
    def normalize_runtime_fields(self) -> "Settings":
        self.environment = self.environment.strip().lower()
        self.public_backend_url = self.public_backend_url.rstrip("/")
        if self.environment == "production" and "frontend_url" not in self.__pydantic_fields_set__:
            self.frontend_url = ""
        if "debug" not in self.__pydantic_fields_set__:
            self.debug = self.environment == "development"
        if "run_startup_migrations" not in self.__pydantic_fields_set__:
            self.run_startup_migrations = self.environment != "production"
        if "run_startup_schema_sync" not in self.__pydantic_fields_set__:
            self.run_startup_schema_sync = self.environment != "production"
        return self

    def get_cors_origins(self) -> List[str]:
        """
        Get all CORS origins including frontend_url
        Ensures frontend is always allowed
        """
        configured_origins = [
            origin.strip()
            for origin in self.cors_origins_raw.split(",")
            if origin.strip()
        ]

        origins = list(self.default_cors_origins) if self.environment != "production" else []
        for origin in configured_origins:
            if origin not in origins:
                origins.append(origin)

        if self.frontend_url and self.frontend_url not in origins:
            origins.insert(0, self.frontend_url)

        deduped_origins: List[str] = []
        for origin in origins:
            if origin and origin not in deduped_origins:
                deduped_origins.append(origin)

        return deduped_origins


# Create global settings instance
settings = Settings()
