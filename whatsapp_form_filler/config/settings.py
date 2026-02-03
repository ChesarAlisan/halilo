"""
Configuration management using Pydantic Settings.
Loads from environment variables and .env file.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ============================================
    # USER INFORMATION
    # ============================================
    student_name: str = Field(..., description="Student full name")
    student_id: str = Field(..., description="Student ID number")
    
    # ============================================
    # WHATSAPP CONFIGURATION
    # ============================================
    whatsapp_group_name: str = Field("Ders Linkleri", description="WhatsApp group to monitor")
    whatsapp_phone: Optional[str] = Field(None, description="WhatsApp phone number")
    
    # ============================================
    # AI CONFIGURATION
    # ============================================
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key for fallback")
    use_ai_fallback: bool = Field(True, description="Use AI when rule-based fails")
    ai_confidence_threshold: float = Field(0.85, ge=0.0, le=1.0, description="Threshold to trigger AI")
    
    # ============================================
    # BROWSER CONFIGURATION
    # ============================================
    headless_mode: bool = Field(False, description="Run browser in headless mode")
    screenshot_on_success: bool = Field(True, description="Take screenshot on success")
    screenshot_on_error: bool = Field(True, description="Take screenshot on error")
    save_video_recording: bool = Field(False, description="Save video recordings")
    browser_locale: str = Field("tr-TR", description="Browser locale")
    browser_timezone: str = Field("Europe/Istanbul", description="Browser timezone")
    
    # ============================================
    # RATE LIMITING
    # ============================================
    min_delay_between_forms: int = Field(60, ge=10, description="Min seconds between forms")
    max_forms_per_hour: int = Field(10, ge=1, description="Max forms per hour")
    break_after_n_forms: int = Field(5, ge=1, description="Forms before break")
    break_duration_seconds: int = Field(300, ge=60, description="Break duration")
    
    # ============================================
    # NOTIFICATION SETTINGS
    # ============================================
    enable_desktop_notifications: bool = Field(True, description="Show desktop notifications")
    telegram_bot_token: Optional[str] = Field(None, description="Telegram bot token")
    telegram_chat_id: Optional[str] = Field(None, description="Telegram chat ID")
    
    # ============================================
    # LOGGING
    # ============================================
    log_level: str = Field("INFO", description="Logging level")
    log_to_file: bool = Field(True, description="Enable file logging")
    log_retention_days: int = Field(30, ge=1, description="Days to keep logs")
    
    # ============================================
    # ADVANCED SETTINGS
    # ============================================
    enable_pattern_learning: bool = Field(True, description="Learn from success")
    max_retry_attempts: int = Field(3, ge=1, description="Max retries for failed submissions")
    retry_delay_seconds: int = Field(10, ge=5, description="Delay between retries")
    
    # Paths
    project_root: str = Field(default_factory=lambda: os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    model_config = SettingsConfigDict(
        env_file="../.env",  # Look in parent directory
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v_upper
    
    @property
    def logs_dir(self) -> str:
        """Directory for log files."""
        path = os.path.join(self.project_root, "logs")
        os.makedirs(path, exist_ok=True)
        return path
    
    @property
    def data_dir(self) -> str:
        """Directory for data files."""
        path = os.path.join(self.project_root, "data")
        os.makedirs(path, exist_ok=True)
        return path
    
    @property
    def database_path(self) -> str:
        """Path to SQLite database."""
        return os.path.join(self.data_dir, "whatsapp_form_filler.db")
    
    @property
    def has_telegram(self) -> bool:
        """Check if Telegram notifications are configured."""
        return bool(self.telegram_bot_token and self.telegram_chat_id)
    
    @property
    def has_openai(self) -> bool:
        """Check if OpenAI is configured."""
        return bool(self.openai_api_key and self.openai_api_key != "your_openai_api_key_here")


# Global settings instance
settings = Settings()
