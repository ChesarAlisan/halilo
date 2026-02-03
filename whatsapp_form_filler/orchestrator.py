"""
Orchestrator - Coordinates all agents for end-to-end form filling.
"""
import time
from datetime import datetime
from typing import Optional
from loguru import logger

from config import settings, get_user_data
from database.models import DetectionMethod
from agents import (
    BrowserAutomationAgent,
    FormIntelligenceAgent,
    VerificationLoggerAgent,
)
from utils import NotificationManager, RateLimiter


class FormFillingOrchestrator:
    """
    Coordinates the entire form filling workflow.
    """
    
    def __init__(self):
        """Initialize orchestrator and all agents."""
        logger.info("🎭 Initializing Form Filling Orchestrator...")
        
        # Initialize notification manager
        self.notification_manager = NotificationManager(
            enable_desktop=settings.enable_desktop_notifications,
            telegram_bot_token=settings.telegram_bot_token if settings.has_telegram else None,
            telegram_chat_id=settings.telegram_chat_id if settings.has_telegram else None,
        )
        
        # Initialize agents
        self.browser_agent = BrowserAutomationAgent()
        self.intelligence_agent = FormIntelligenceAgent()
        self.verification_agent = VerificationLoggerAgent(self.notification_manager)
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            min_delay_seconds=settings.min_delay_between_forms,
            max_per_hour=settings.max_forms_per_hour,
            break_after_n=settings.break_after_n_forms,
            break_duration_seconds=settings.break_duration_seconds,
        )
        
        # Get user data
        self.user_data = get_user_data()
        
        logger.success("✅ Orchestrator initialized")
    
    def process_form(self, form_url: str) -> bool:
        """
        Process a single form from start to finish.
        
        Args:
            form_url: URL of form to fill
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 Processing form: {form_url}")
        logger.info(f"{'='*60}\n")
        
        # Check rate limiting
        logger.info("⏳ Checking rate limits...")
        self.rate_limiter.wait_if_needed()
        
        screenshots = {}
        plugin = None
        field_mapping = None
        
        try:
            # Step 1: Navigate to form
            logger.info("Step 1/6: Opening form...")
            if not self.browser_agent.navigate_to(form_url):
                raise Exception("Failed to navigate to form")
            
            # Check for CAPTCHA immediately
            if self.browser_agent.check_captcha():
                logger.critical("🔴 CAPTCHA detected immediately!")
                self.notification_manager.notify_captcha(form_url)
                
                # Give user time to solve
                logger.info("⏸️  Pausing for 2 minutes to allow manual CAPTCHA solving...")
                time.sleep(120)
                
                # Check again
                if self.browser_agent.check_captcha():
                    raise Exception("CAPTCHA not solved - skipping form")
            
            # Take initial screenshot
            if settings.screenshot_on_success or settings.screenshot_on_error:
                screenshots['before'] = self.browser_agent.take_screenshot("01_initial")
            
            # Step 2: Analyze form
            logger.info("Step 2/6: Analyzing form structure...")
            plugin, field_mapping = self.intelligence_agent.analyze_form(
                self.browser_agent.page,
                form_url
            )
            
            if not plugin or not field_mapping:
                raise Exception("Form analysis failed")
            
            if not field_mapping.is_complete():
                logger.warning(
                    f"⚠️  Incomplete field mapping - confidence: {field_mapping.confidence}"
                )
                if field_mapping.confidence < settings.ai_confidence_threshold:
                    # In Phase 2, we would call AI fallback here
                    logger.error("Confidence too low and AI fallback not yet implemented")
                    raise Exception("Incomplete field mapping")
            
            # Step 3: Fill form
            logger.info("Step 3/6: Filling form fields...")
            success = plugin.fill_form(
                self.browser_agent.page,
                field_mapping,
                self.user_data
            )
            
            if not success:
                raise Exception("Form filling failed")
            
            # Screenshot after filling
            if settings.screenshot_on_success:
                screenshots['filled'] = self.browser_agent.take_screenshot("02_filled")
            
            # Step 4: Submit form
            logger.info("Step 4/6: Submitting form...")
            success = plugin.submit_form(
                self.browser_agent.page,
                field_mapping
            )
            
            if not success:
                raise Exception("Form submission failed")
            
            # Step 5: Verify submission
            logger.info("Step 5/6: Verifying submission...")
            verified = plugin.verify_submission(self.browser_agent.page)
            
            # Screenshot after submission
            screenshots['after'] = self.browser_agent.take_screenshot("03_submitted")
            
            # Step 6: Log results
            logger.info("Step 6/6: Logging results...")
            processing_time = time.time() - start_time
            
            self.verification_agent.verify_and_log(
                page=self.browser_agent.page,
                form_url=form_url,
                provider=plugin.provider_name,
                detection_method=DetectionMethod.RULE_BASED,
                student_name=self.user_data.student_name,
                student_id=self.user_data.student_id,
                confidence=field_mapping.confidence,
                screenshots=screenshots,
                processing_time=processing_time,
                is_successful=verified,
            )
            
            # Record submission for rate limiting
            self.rate_limiter.record_submission()
            
            if verified:
                logger.success(f"\n🎉 SUCCESS! Form completed in {processing_time:.1f}s\n")
                return True
            else:
                logger.warning(f"\n⚠️  Form submitted but verification uncertain\n")
                return True  # Still count as success
        
        except Exception as e:
            logger.error(f"\n❌ FAILED: {str(e)}\n")
            
            # Log error
            processing_time = time.time() - start_time
            
            if settings.screenshot_on_error:
                screenshots['error'] = self.browser_agent.take_screenshot("99_error")
            
            # Log to database even if failed
            try:
                provider = plugin.provider_name if plugin else self.intelligence_agent.identify_provider(form_url).provider_name
            except:
                from database.models import FormProvider
                provider = FormProvider.UNKNOWN
            
            self.verification_agent.verify_and_log(
                page=self.browser_agent.page if self.browser_agent.page else None,
                form_url=form_url,
                provider=provider,
                detection_method=DetectionMethod.RULE_BASED,
                student_name=self.user_data.student_name,
                student_id=self.user_data.student_id,
                confidence=field_mapping.confidence if field_mapping else 0.0,
                screenshots=screenshots,
                processing_time=processing_time,
                is_successful=False,
                error_message=str(e),
            )
            
            return False
    
    def get_stats(self) -> dict:
        """
        Get current statistics.
        
        Returns:
            Dictionary with stats from verification agent and rate limiter
        """
        return {
            'daily': self.verification_agent.get_daily_stats(),
            'rate_limiter': self.rate_limiter.get_stats(),
        }
    
    def start(self) -> None:
        """Start the orchestrator (initializes browser)."""
        logger.info("🚀 Starting orchestrator...")
        self.browser_agent.start()
    
    def stop(self) -> None:
        """Stop the orchestrator (closes browser)."""
        logger.info("🛑 Stopping orchestrator...")
        self.browser_agent.close()
        
        # Print final stats
        stats = self.get_stats()
        logger.info(f"\n📊 Daily Stats: {stats['daily']}\n")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
