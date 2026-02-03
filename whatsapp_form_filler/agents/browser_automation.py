"""
Browser Automation Agent - Creates and manages stealthy browser instances.
"""
import os
import json
from typing import Optional
from datetime import datetime
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from loguru import logger

from config import settings
from utils import (
    get_stealthy_browser_args,
    get_context_options,
    configure_stealth_context,
)


class BrowserAutomationAgent:
    """
    Manages browser automation with anti-detection features.
    """
    
    def __init__(self):
        """Initialize browser automation agent."""
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.session_file = os.path.join(settings.data_dir, "browser_session.json")
    
    def start(self) -> None:
        """
        Start browser with stealth configuration.
        Uses Chrome user data directory for persistent login.
        """
        logger.info("🚀 Starting browser automation agent...")
        
        self.playwright = sync_playwright().start()
        
        # IMPORTANT: Use Chrome profile directory for persistent authentication
        # This allows using the existing Chrome profile with logged-in Microsoft account
        chrome_profile = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data\\Default")
        
        # Check if Chrome profile exists
        use_chrome_profile = os.path.exists(chrome_profile)
        
        if use_chrome_profile:
            logger.info("🔐 Using Chrome Default profile for authentication...")
            
            # Launch with Chrome profile directory
            # NOTE: Must use channel='chrome' to use real Chrome (not Chromium)
            try:
                # Close any existing Chrome instances first
                logger.info("Ensuring Chrome is closed...")
                
                self.browser = self.playwright.chromium.launch_persistent_context(
                    user_data_dir=os.path.dirname(chrome_profile),  # User Data folder
                    headless=False,  # Persistent context doesn't support headless
                    channel='chrome',  # Use installed Chrome
                    args=get_stealthy_browser_args(),
                    slow_mo=50,
                    locale=settings.browser_locale,
                    timezone_id=settings.browser_timezone,
                    no_viewport=False,
                )
                
                # For persistent context, browser IS the context
                self.context = self.browser
                
                # Get or create first page
                if len(self.browser.pages) > 0:
                    self.page = self.browser.pages[0]
                else:
                    self.page = self.browser.new_page()
                
                logger.success("✅ Using Chrome profile - already logged in!")
                
            except Exception as e:
                logger.warning(f"Could not use Chrome profile: {e}")
                logger.info("Falling back to Chromium...")
                use_chrome_profile = False
        
        if not use_chrome_profile:
            # Fallback: Use regular Chromium with session file
            logger.info("Using Chromium with session file...")
            
            self.browser = self.playwright.chromium.launch(
                headless=settings.headless_mode,
                args=get_stealthy_browser_args(),
                slow_mo=50 if not settings.headless_mode else 0,
            )
            
            # Create context with stealth config
            context_opts = get_context_options(
                locale=settings.browser_locale,
                timezone=settings.browser_timezone
            )
            
            # Load saved session if exists
            if os.path.exists(self.session_file):
                logger.info("📂 Loading saved browser session...")
                try:
                    with open(self.session_file, 'r') as f:
                        session_data = json.load(f)
                    context_opts['storage_state'] = session_data
                except Exception as e:
                    logger.warning(f"Could not load session: {e}")
            
            # Create context
            self.context = self.browser.new_context(**context_opts)
            
            # Apply stealth measures
            configure_stealth_context(self.context)
            
            # Create page if not already created
            if not self.page:
                # Enable video recording if configured
                if settings.save_video_recording:
                    self.context = self.browser.new_context(
                        **context_opts,
                        record_video_dir=os.path.join(settings.logs_dir, "videos")
                    )
                    configure_stealth_context(self.context)
                
                self.page = self.context.new_page()
        
        logger.success("✅ Browser started successfully")
    
    def save_session(self) -> None:
        """
        Save browser session (cookies, localStorage, etc.)
        """
        if not self.context:
            return
        
        try:
            session_data = self.context.storage_state()
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            logger.debug("💾 Browser session saved")
        except Exception as e:
            logger.warning(f"Could not save session: {e}")
    
    def navigate_to(self, url: str, wait_for: str = 'networkidle') -> bool:
        """
        Navigate to URL with error handling.
        
        Args:
            url: URL to navigate to
            wait_for: Wait condition ('load', 'domcontentloaded', 'networkidle')
            
        Returns:
            True if navigation successful
        """
        if not self.page:
            logger.error("Browser not started")
            return False
        
        try:
            logger.info(f"🌐 Navigating to: {url}")
            self.page.goto(url, wait_until=wait_for, timeout=30000)
            logger.success("✅ Navigation complete")
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False
    
    def take_screenshot(self, name: str = "screenshot") -> str:
        """
        Take screenshot and save to logs.
        
        Args:
            name: Screenshot name (without extension)
            
        Returns:
            Path to saved screenshot
        """
        if not self.page:
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.png"
        filepath = os.path.join(settings.logs_dir, filename)
        
        try:
            os.makedirs(settings.logs_dir, exist_ok=True)
            self.page.screenshot(path=filepath, full_page=True)
            logger.debug(f"📸 Screenshot saved: {filename}")
            return filepath
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return ""
    
    def check_captcha(self) -> bool:
        """
        Check if CAPTCHA is present on current page.
        
        Returns:
            True if CAPTCHA detected
        """
        if not self.page:
            return False
        
        try:
            # Check for reCAPTCHA
            recaptcha = self.page.locator('iframe[src*="recaptcha"]').count()
            if recaptcha > 0:
                logger.warning("🔴 reCAPTCHA detected")
                return True
            
            # Check for other CAPTCHA indicators
            captcha_keywords = ['captcha', 'robot', 'verify you are human']
            page_text = self.page.inner_text('body').lower()
            
            for keyword in captcha_keywords:
                if keyword in page_text:
                    logger.warning(f"🔴 CAPTCHA detected (keyword: {keyword})")
                    return True
            
            return False
        except:
            return False
    
    def get_dom_snapshot(self) -> str:
        """
        Get HTML snapshot of current page.
        
        Returns:
            HTML content as string
        """
        if not self.page:
            return ""
        
        try:
            return self.page.content()
        except Exception as e:
            logger.error(f"Could not get DOM snapshot: {e}")
            return ""
    
    def close(self) -> None:
        """
        Close browser and save session.
        """
        logger.info("🛑 Closing browser...")
        
        self.save_session()
        
        if self.context:
            self.context.close()
        
        if self.browser:
            self.browser.close()
        
        if self.playwright:
            self.playwright.stop()
        
        logger.success("✅ Browser closed")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
