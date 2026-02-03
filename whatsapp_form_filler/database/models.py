"""
Database models using Pydantic for type safety and validation.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class FormProvider(str, Enum):
    """Supported form providers."""
    MICROSOFT_FORMS = "microsoft_forms"
    GOOGLE_FORMS = "google_forms"
    MOODLE = "moodle"
    UNKNOWN = "unknown"


class DetectionMethod(str, Enum):
    """How the form was analyzed."""
    RULE_BASED = "rule_based"
    AI_ASSISTED = "ai_assisted"
    LEARNED_PATTERN = "learned_pattern"


class SubmissionStatus(str, Enum):
    """Form submission result status."""
    SUCCESS = "success"
    FAILED = "failed"
    CAPTCHA = "captcha"
    SKIPPED = "skipped"


class QueueStatus(str, Enum):
    """Message queue processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FormSubmission(BaseModel):
    """Log entry for a form submission attempt."""
    id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Form Details
    form_url: str
    form_provider: FormProvider
    form_signature: Optional[str] = None
    
    # Processing Details
    detection_method: DetectionMethod
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # User Data Submitted
    student_name: str
    student_id: str
    
    # Submission Result
    status: SubmissionStatus
    error_message: Optional[str] = None
    
    # Screenshots & Evidence
    screenshot_before: Optional[str] = None
    screenshot_filled: Optional[str] = None
    screenshot_after: Optional[str] = None
    dom_snapshot: Optional[str] = None
    
    # Timing
    processing_time_seconds: Optional[float] = None
    
    # Metadata
    whatsapp_message: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        use_enum_values = True


class FieldPattern(BaseModel):
    """Learned field mapping pattern for a specific form structure."""
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Form Identification
    form_signature: str
    form_provider: FormProvider
    
    # Field Mappings (dict of field_name -> selector)
    field_mappings: Dict[str, str]
    
    # Success Tracking
    success_count: int = 0
    failure_count: int = 0
    last_used_at: Optional[datetime] = None
    
    # Confidence
    pattern_confidence: float = Field(0.0, ge=0.0, le=1.0)

    class Config:
        use_enum_values = True


class ErrorLog(BaseModel):
    """Error tracking and debugging information."""
    id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Error Details
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    
    # Context
    form_url: Optional[str] = None
    agent_name: Optional[str] = None
    
    # Recovery
    recovery_attempted: bool = False
    recovery_successful: bool = False
    
    # Screenshot
    screenshot_path: Optional[str] = None


class WhatsAppSession(BaseModel):
    """WhatsApp Web session management."""
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_active_at: datetime = Field(default_factory=datetime.now)
    
    # Session Data (serialized)
    session_data: Optional[str] = None
    phone_number: Optional[str] = None
    
    # Status
    is_active: bool = True
    qr_scan_required: bool = False


class MessageQueueItem(BaseModel):
    """Queued message for processing."""
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    
    # Message Details
    message_text: str
    form_url: str
    group_name: Optional[str] = None
    
    # Processing Status
    status: QueueStatus = QueueStatus.PENDING
    attempts: int = 0
    
    # Result
    submission_id: Optional[int] = None

    class Config:
        use_enum_values = True


class SystemStats(BaseModel):
    """Daily system statistics."""
    id: Optional[int] = None
    date: datetime = Field(default_factory=lambda: datetime.now().date())
    
    # Daily Counts
    total_forms_processed: int = 0
    successful_submissions: int = 0
    failed_submissions: int = 0
    captcha_triggered: int = 0
    
    # Performance
    avg_processing_time_seconds: float = 0.0
    
    # AI Usage
    ai_fallback_used: int = 0
    rule_based_success: int = 0


class UserData(BaseModel):
    """User information for form filling."""
    student_name: str
    student_id: str
    
    @field_validator('student_name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Student name cannot be empty")
        return v.strip()
    
    @field_validator('student_id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Student ID cannot be empty")
        return v.strip()


class FieldMapping(BaseModel):
    """Identified form fields with selectors."""
    name_field: Optional[str] = None
    student_id_field: Optional[str] = None
    attendance_checkbox: Optional[str] = None
    submit_button: Optional[str] = None
    
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    
    def is_complete(self) -> bool:
        """Check if all required fields are mapped."""
        return all([
            self.name_field,
            self.student_id_field,
            self.attendance_checkbox,
            self.submit_button
        ])
    
    def get_missing_fields(self) -> list[str]:
        """Return list of missing field names."""
        missing = []
        if not self.name_field:
            missing.append("name_field")
        if not self.student_id_field:
            missing.append("student_id_field")
        if not self.attendance_checkbox:
            missing.append("attendance_checkbox")
        if not self.submit_button:
            missing.append("submit_button")
        return missing
