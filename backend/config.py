# config.py - Central configuration for the application
# Uses pydantic-settings for environment variable management

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # ─── Application ───────────────────────────────────────────
    APP_NAME: str = "Smart School Dropout Early Warning System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ─── Database ──────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./dropout_system.db"

    # ─── JWT Authentication ─────────────────────────────────────
    SECRET_KEY: str = "super-secret-key-change-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # ─── ML Model ──────────────────────────────────────────────
    MODEL_PATH: str = "./ml/saved_models/dropout_model.joblib"
    SCALER_PATH: str = "./ml/saved_models/scaler.joblib"
    KNN_PATH: str = "./ml/saved_models/knn_model.joblib"
    FEATURE_NAMES_PATH: str = "./ml/saved_models/feature_names.joblib"

    # ─── Risk Thresholds ───────────────────────────────────────
    LOW_RISK_THRESHOLD: int = 40
    MEDIUM_RISK_THRESHOLD: int = 70

    # ─── File Upload ───────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50

    # ─── Alerts ────────────────────────────────────────────────
    ALERT_EMAIL_ENABLED: bool = False  # Set True with SMTP config
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton instance
settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs("./ml/saved_models", exist_ok=True)
