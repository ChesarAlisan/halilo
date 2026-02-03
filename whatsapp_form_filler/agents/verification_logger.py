"""
Verification & Logging Agent - Verifies submissions and maintains audit trail.
"""
import os
import sqlite3
from datetime import datetime
from typing import Optional
from playwright.sync_api import Page
from loguru import logger

from config import settings
from database.models import (
    FormSubmission,
    SubmissionStatus,
    DetectionMethod,
    FormProvider,
)
from utils import NotificationManager


class VerificationLoggerAgent:
    """
    Handles submission verification, logging, and notifications.
    """
    
    def __init__(self, notification_manager: NotificationManager):
        """
        Initialize verification logger agent.
        
        Args:
            notification_manager: Notification manager instance
        """
        self.notification_manager = notification_manager
        self.db_path = settings.database_path
        self._init_database()
        logger.info("📝 Verification & Logging Agent initialized")
    
    def _init_database(self) -> None:
        """Initialize SQLite database."""
        os.makedirs(settings.data_dir, exist_ok=True)
        
        # Read and execute schema if database is new
        if not os.path.exists(self.db_path):
            logger.info("Creating database...")
            schema_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "database",
                "schema.sql"
            )
            
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                
                conn = sqlite3.connect(self.db_path)
                conn.executescript(schema_sql)
                conn.close()
                logger.success("✅ Database created")
            else:
                logger.error(f"Schema file not found: {schema_path}")
    
    def create_log_directory(self) -> str:
        """
        Create timestamped log directory for current submission.
        
        Returns:
            Path to log directory
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_dir = os.path.join(settings.logs_dir, timestamp)
        os.makedirs(log_dir, exist_ok=True)
        return log_dir
    
    def verify_and_log(
        self,
        page: Page,
        form_url: str,
        provider: FormProvider,
        detection_method: DetectionMethod,
        student_name: str,
        student_id: str,
        confidence: float,
        screenshots: dict[str, str],
        processing_time: float,
        is_successful: bool,
        error_message: Optional[str] = None
    ) -> int:
        """
        Verify submission and log to database.
        
        Args:
            page: Playwright page
            form_url: Form URL
            provider: Form provider
            detection_method: How form was analyzed
            student_name: Student name submitted
            student_id: Student ID submitted
            confidence: Detection confidence
            screenshots: Dict of screenshot paths
            processing_time: Time taken in seconds
            is_successful: Whether submission was successful
            error_message: Error message if failed
            
        Returns:
            Submission ID from database
        """
        logger.info("🔍 Verifying submission...")
        
        # Determine status
        if is_successful:
            status = SubmissionStatus.SUCCESS
            logger.success("✅ Submission verified as successful")
        else:
            # Check if CAPTCHA
            page_text = page.inner_text('body')
            if 'captcha' in page_text.lower():
                status = SubmissionStatus.CAPTCHA
                logger.warning("🔴 CAPTCHA detected")
            else:
                status = SubmissionStatus.FAILED
                logger.error("❌ Submission failed")
        
        # Get DOM snapshot
        dom_snapshot = page.content()
        
        # Save DOM to file
        log_dir = self.create_log_directory()
        dom_path = os.path.join(log_dir, "dom_snapshot.html")
        with open(dom_path, 'w', encoding='utf-8') as f:
            f.write(dom_snapshot)
        
        # Create submission record
        submission = FormSubmission(
            form_url=form_url,
            form_provider=provider,
            detection_method=detection_method,
            confidence_score=confidence,
            student_name=student_name,
            student_id=student_id,
            status=status,
            error_message=error_message,
            screenshot_before=screenshots.get('before', ''),
            screenshot_filled=screenshots.get('filled', ''),
            screenshot_after=screenshots.get('after', ''),
            dom_snapshot=dom_path,
            processing_time_seconds=processing_time,
        )
        
        # Save to database
        submission_id = self._save_to_database(submission)
        
        # Send notifications
        if status == SubmissionStatus.SUCCESS:
            self.notification_manager.notify_success(
                form_url=form_url,
                student_name=student_name,
                processing_time=processing_time
            )
        elif status == SubmissionStatus.CAPTCHA:
            self.notification_manager.notify_captcha(form_url)
        else:
            self.notification_manager.notify_error(
                error_type="FormSubmissionFailed",
                form_url=form_url,
                error_message=error_message
            )
        
        logger.info(f"📝 Submission logged with ID: {submission_id}")
        return submission_id
    
    def _save_to_database(self, submission: FormSubmission) -> int:
        """
        Save submission to database.
        
        Args:
            submission: FormSubmission model
            
        Returns:
            Submission ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO form_submissions (
                timestamp, form_url, form_provider, detection_method,
                confidence_score, student_name, student_id, status,
                error_message, screenshot_before, screenshot_filled,
                screenshot_after, dom_snapshot, processing_time_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            submission.timestamp.isoformat(),
            submission.form_url,
            submission.form_provider.value,
            submission.detection_method.value,
            submission.confidence_score,
            submission.student_name,
            submission.student_id,
            submission.status.value,
            submission.error_message,
            submission.screenshot_before,
            submission.screenshot_filled,
            submission.screenshot_after,
            submission.dom_snapshot,
            submission.processing_time_seconds,
        ))
        
        submission_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return submission_id
    
    def get_daily_stats(self) -> dict:
        """
        Get statistics for today.
        
        Returns:
            Dictionary with stats
        """
        today = datetime.now().date().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'captcha' THEN 1 ELSE 0 END) as captcha,
                AVG(processing_time_seconds) as avg_time
            FROM form_submissions
            WHERE DATE(timestamp) = ?
        """, (today,))
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            'total': row[0] or 0,
            'successful': row[1] or 0,
            'failed': row[2] or 0,
            'captcha': row[3] or 0,
            'avg_processing_time': row[4] or 0.0,
        }
