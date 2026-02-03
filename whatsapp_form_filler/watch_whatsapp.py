"""
WhatsApp Monitor - Watches WhatsApp Web for Microsoft Forms links

This script:
1. Connects to an already-running Chrome instance (debug mode)
2. Monitors WhatsApp Web for new messages
3. Detects Microsoft Forms links
4. Automatically fills and submits forms
5. Keeps Chrome open (only opens/closes tabs)

Usage:
  1. Start Chrome with: start_chrome.bat
  2. Open WhatsApp Web in Chrome
  3. Run: python watch_whatsapp.py
"""
import time
from playwright.sync_api import sync_playwright
from loguru import logger
import sys
import re
import random  # For human-like random delays

# Configuration
from config import settings
from database.models import UserData

# Student info
STUDENT_NAME = settings.student_name
STUDENT_ID = settings.student_id

# WhatsApp selectors (may need adjustment)
WHATSAPP_MESSAGE_SELECTOR = 'div[role="row"]'  # Message rows
WHATSAPP_LINK_SELECTOR = 'a[href*="forms.office.com"]'  # Forms links

import os
import subprocess

def launch_chrome_debug():
    """Launch Chrome in debug mode automatically."""
    logger.info("🔧 Attempting to launch Chrome automatically...")
    
    # Common Chrome paths
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]
    
    chrome_path = None
    for path in paths:
        if os.path.exists(path):
            chrome_path = path
            break
            
    if not chrome_path:
        logger.error("❌ Chrome executable not found!")
        return False

    if not chrome_path:
        logger.error("❌ Chrome executable not found!")
        return False

    try:
        # Use a specific folder for the bot to avoid conflicts with main Chrome
        # This means we don't need to kill existing Chrome instances!
        project_dir = os.path.dirname(os.path.abspath(__file__))
        user_data = os.path.join(project_dir, "chrome_data")
        
        # Ensure dir exists
        if not os.path.exists(user_data):
            os.makedirs(user_data)
        
        logger.info(f"📂 Using bot profile: {user_data}")
        
        # Launch Chrome with isolated profile
        cmd = [
            chrome_path,
            "--remote-debugging-port=9222",
            f"--user-data-dir={user_data}",
            "--no-first-run",             # Skip welcome
            "--no-default-browser-check"  # Skip default browser check
        ]
        
        subprocess.Popen(cmd)
        logger.success(f"🚀 Chrome launched!")
        logger.info("Waiting 5 seconds for Chrome to start...")
        time.sleep(5)
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to launch Chrome: {e}")
        return False


def extract_form_url(text):
    """Extract Microsoft Forms URL from text."""
    # Match forms.office.com URLs
    pattern = r'https?://forms\.office\.com/[^\s]+'
    matches = re.findall(pattern, text)
    # Return the LAST match (most recent message at the bottom)
    return matches[-1] if matches else None


def fill_form_in_new_tab(browser, form_url):
    """
    Open form in new tab, fill it, submit, close tab.
    
    Args:
        browser: Connected browser context
        form_url: Microsoft Forms URL
    
    Returns:
        True if successful
    """
    logger.info(f"📋 Processing form: {form_url}")
    
    # Create new page (tab)
    page = browser.new_page()
    
    try:
        # Navigate to form
        logger.info("🌐 Opening form...")
        page.goto(form_url, wait_until='networkidle', timeout=60000)
        
        # Wait for form to load with retries
        logger.info("⏳ Waiting for form to load...")
        
        form_loaded = False
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                # Wait for question items (main indicator form is loaded)
                page.wait_for_selector('[data-automation-id="questionItem"]', timeout=15000)
                form_loaded = True
                logger.success("✅ Form loaded!")
                break
            except:
                logger.warning(f"⚠️  Attempt {attempt + 1}/{max_attempts}: Form not loaded yet...")
                
                # Check if login page
                current_url = page.url
                if 'login.microsoftonline.com' in current_url or 'login.live.com' in current_url:
                    logger.warning("🔐 Login page detected! Waiting 30 seconds for manual login...")
                    logger.info("Please login in the Chrome window!")
                    time.sleep(30)
                else:
                    # Just wait longer
                    time.sleep(10)
        
        if not form_loaded:
            logger.error("❌ Form did not load after multiple attempts!")
            logger.error(f"Current URL: {page.url}")
            page.screenshot(path=f'logs/{time.strftime("%Y%m%d_%H%M%S")}_load_failed.png')
            return False
        
        # Random initial wait AFTER form loads (5-15 seconds) - humans take time to read
        initial_wait = random.uniform(5, 15)
        logger.info(f"📖 Reading form for {initial_wait:.1f} seconds...")
        time.sleep(initial_wait)
        
        # Take screenshot with random delay
        time.sleep(random.uniform(1, 3))
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        page.screenshot(path=f'logs/{timestamp}_before.png')
        logger.info(f"📸 Screenshot: logs/{timestamp}_before.png")
        
        # Random scroll/read delay (humans scroll through form first)
        logger.info("📜 Scrolling through form...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        time.sleep(random.uniform(2, 5))
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(random.uniform(1, 3))
        
        # Find and fill fields
        logger.info("🔍 Analyzing form...")
        questions = page.query_selector_all('[data-automation-id="questionItem"]')
        logger.info(f"Found {len(questions)} questions")
        
        if len(questions) == 0:
            logger.error("❌ No questions found in form!")
            page.screenshot(path=f'logs/{timestamp}_no_questions.png')
            return False
        
        for idx, question in enumerate(questions):
            try:
                title_elem = question.query_selector('[data-automation-id="questionTitle"]')
                if not title_elem:
                    logger.warning(f"Q{idx+1}: No title element found")
                    continue
                
                question_text = title_elem.inner_text().lower()
                logger.info(f"📋 Q{idx+1}: '{question_text}'")
                
                # Random thinking delay before filling each field (1-4 seconds)
                think_delay = random.uniform(1, 4)
                logger.info(f"🤔 Thinking for {think_delay:.1f}s...")
                time.sleep(think_delay)
                
                # Name field
                if any(keyword in question_text for keyword in ['ad', 'soyad', 'isim', 'name']):
                    logger.info(f"🎯 Target: Name Field ({STUDENT_NAME})")
                    
                    # Try to find any input or textarea in this question block
                    input_field = question.query_selector('input') or question.query_selector('textarea')
                    
                    if input_field:
                        logger.info(f"   found input field: {input_field}")
                        
                        # Focus first
                        try:
                            input_field.click(timeout=1000, force=True)
                        except:
                            pass
                            
                        # Force fill
                        input_field.fill(STUDENT_NAME)
                        time.sleep(0.5)
                        
                        # VERIFICATION 1: Check value property
                        val = input_field.input_value()
                        if val == STUDENT_NAME:
                            logger.success(f"   ✅ Verified: {val}")
                        else:
                            logger.warning(f"   ⚠️ Fill failed, trying type strategy...")
                            input_field.clear()
                            input_field.press("Control+A")
                            input_field.press("Backspace")
                            input_field.type(STUDENT_NAME, delay=100)
                            
                        time.sleep(1)
                    else:
                        logger.error("❌ Could not find input field for Name!")
                
                # Student ID field
                elif any(keyword in question_text for keyword in ['no', 'numara', 'öğrenci']):
                    logger.info(f"🎯 Target: ID Field ({STUDENT_ID})")
                    
                    input_field = question.query_selector('input') or question.query_selector('textarea')
                    
                    if input_field:
                        logger.info(f"   found input field: {input_field}")
                        
                        try:
                            input_field.click(timeout=1000, force=True)
                        except:
                            pass
                            
                        input_field.fill(STUDENT_ID)
                        time.sleep(0.5)
                        
                        # VERIFICATION
                        val = input_field.input_value()
                        if val == STUDENT_ID:
                            logger.success(f"   ✅ Verified: {val}")
                        else:
                            logger.warning(f"   ⚠️ Fill failed, trying type strategy...")
                            input_field.clear()
                            input_field.type(STUDENT_ID, delay=100)
                            
                        time.sleep(1)
                    else:
                        logger.error("❌ Could not find input field for ID!")
                
                # Attendance checkbox
                elif any(keyword in question_text for keyword in ['katılım', 'onay', 'ders', 'attendance']):
                    # Look for any clickable input, or the label wrapper
                    checkbox = question.query_selector('input[type="checkbox"]') or question.query_selector('input[type="radio"]')
                    
                    if not checkbox:
                        # Sometimes MS Forms uses divs/labels acting as checkboxes
                        checkbox = question.query_selector('[role="checkbox"]') or question.query_selector('[role="radio"]')
                    
                    if checkbox:
                        logger.info("✅ Checking attendance")
                        checkbox.hover()
                        checkbox.click(force=True)
                        time.sleep(1)
                    else:
                        # Last resort: try clicking the first label
                        lbl = question.query_selector('label')
                        if lbl:
                            lbl.click(force=True)
            
            except Exception as e:
                logger.warning(f"Could not process Q{idx+1}: {e}")
        
        # Random review delay before submitting (2-6 seconds)
        review_delay = random.uniform(2, 6)
        logger.info(f"👀 Reviewing answers for {review_delay:.1f}s...")
        time.sleep(review_delay)
        
        # Screenshot after filling
        page.screenshot(path=f'logs/{timestamp}_after.png')
        
        # Find and click submit
        logger.info("📤 Submitting form...")
        submit_btn = page.query_selector('button[data-automation-id="submitButton"]')
        
        if not submit_btn:
            buttons = page.query_selector_all('button')
            for btn in buttons:
                if 'gönder' in btn.inner_text().lower() or 'submit' in btn.inner_text().lower():
                    submit_btn = btn
                    break
        
        if submit_btn:
            # Scroll to submit button
            submit_btn.scroll_into_view_if_needed()
            time.sleep(random.uniform(0.5, 1.5))
            
            # Hover over button
            submit_btn.hover()
            time.sleep(random.uniform(0.5, 1.2))
            
            # Click submit
            submit_btn.click()
            logger.success("✅ Submit clicked!")
            
            # IMPORTANT: Wait longer for submission to process (8-15 seconds)
            submit_wait = random.uniform(8, 15)
            logger.info(f"⏳ Waiting {submit_wait:.1f}s for submission to process...")
            time.sleep(submit_wait)
            
            # Screenshot confirmation
            page.screenshot(path=f'logs/{timestamp}_submitted.png')
            
            # Check success
            page_text = page.inner_text('body').lower()
            if any(keyword in page_text for keyword in ['kaydedildi', 'teşekkür', 'recorded', 'thank']):
                logger.success("🎉 Form submitted successfully!")
                
                # Random delay before closing (2-5 seconds) - humans read confirmation
                final_delay = random.uniform(2, 5)
                logger.info(f"✅ Reading confirmation for {final_delay:.1f}s...")
                time.sleep(final_delay)
                
                return True
            else:
                logger.warning("⚠️  Submitted but no confirmation found")
                time.sleep(random.uniform(3, 6))
                return True
        else:
            logger.error("❌ Submit button not found")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        page.screenshot(path=f'logs/{timestamp}_error.png')
        return False
    
    finally:
        # Close the tab
        logger.info("🗙 Closing form tab...")
        page.close()
        time.sleep(1)


def watch_whatsapp():
    """Monitor WhatsApp Web for form links."""
    
    logger.info("=" * 70)
    logger.info("👁️  WhatsApp Monitor Started")
    logger.info("=" * 70)
    logger.info(f"Student: {STUDENT_NAME}")
    logger.info(f"ID: {STUDENT_ID}")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Connecting to Chrome (make sure it's running in debug mode)...")
    logger.info("")
    
    with sync_playwright() as p:
        try:
            # Connect to existing Chrome instance
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            logger.success("✅ Connected to Chrome!")
            
            # Get all contexts (browser windows)
            contexts = browser.contexts
            if not contexts:
                logger.error("❌ No browser context found. Open Chrome first!")
                return
            
            context = contexts[0]
            
            # Find WhatsApp page or create one
            whatsapp_page = None
            for page in context.pages:
                if 'web.whatsapp.com' in page.url:
                    whatsapp_page = page
                    logger.success(f"✅ Found WhatsApp tab: {page.url}")
                    break
            
            if not whatsapp_page:
                logger.warning("⚠️  WhatsApp Web not open. Opening it now...")
                whatsapp_page = context.new_page()
                whatsapp_page.goto('https://web.whatsapp.com')
                logger.info("📱 Please scan QR code to login to WhatsApp Web")
                time.sleep(10)
            
            logger.info("")
            logger.info("=" * 70)
            logger.info("🚀 Monitoring started!")
            logger.info("=" * 70)
            logger.info("Watching for Microsoft Forms links...")
            logger.info("Press Ctrl+C to stop")
            logger.info("")
            
            # Track processed URLs to avoid duplicates
            processed_forms = set()
            
            # Monitor loop
            while True:
                try:
                    # Get current page content
                    page_text = whatsapp_page.inner_text('body')
                    
                    # Look for forms.office.com links
                    form_url = extract_form_url(page_text)
                    
                    if form_url and form_url not in processed_forms:
                        logger.success(f"\n🔔 NEW FORM DETECTED!")
                        logger.info(f"URL: {form_url}\n")
                        
                        # Process the form
                        success = fill_form_in_new_tab(context, form_url)
                        
                        if success:
                            logger.success("✅ Form processed successfully!\n")
                        else:
                            logger.error("❌ Form processing failed!\n")
                        
                        # Mark as processed
                        processed_forms.add(form_url)
                        
                        logger.info("Continuing to monitor...\n")
                    
                    # Wait before next check
                    time.sleep(5)  # Check every 5 seconds
                
                except KeyboardInterrupt:
                    logger.info("\n\n👋 Stopping monitor...")
                    break
                except Exception as e:
                    logger.error(f"Error in monitor loop: {e}")
                    time.sleep(10)
        
        except Exception as e:
            logger.warning(f"⚠️  Could not connect to Chrome: {e}")
            logger.info("Trying to launch Chrome automatically...")
            
            if launch_chrome_debug():
                browser = None
                # Try connecting for 10 seconds
                for i in range(10):
                    try:
                        logger.info(f"  Attempt {i+1}/10: Connecting to Chrome...")
                        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                        logger.success("✅ Connected to Chrome!")
                        break
                    except Exception as connection_err:
                        time.sleep(1)
                
                if browser:
                    try:
                        # Continue with existing logic (copied from above to avoid refactoring entire function structure)
                        # Ideally this should be a loop or separate function, but keeping it simple for now
                        contexts = browser.contexts
                        if contexts:
                            context = contexts[0]
                            whatsapp_page = None
                            for page in context.pages:
                                if 'web.whatsapp.com' in page.url:
                                    whatsapp_page = page
                                    logger.success(f"✅ Found WhatsApp tab: {page.url}")
                                    break
                            
                            if not whatsapp_page:
                                whatsapp_page = context.new_page()
                                whatsapp_page.goto('https://web.whatsapp.com')
                            
                            # Start monitoring loop
                            logger.info("🚀 Monitoring started!")
                            processed_forms = set()
                            
                            while True:
                                try:
                                    page_text = whatsapp_page.inner_text('body')
                                    form_url = extract_form_url(page_text)
                                    if form_url and form_url not in processed_forms:
                                        logger.success(f"🔔 NEW FORM: {form_url}")
                                        fill_form_in_new_tab(context, form_url)
                                        processed_forms.add(form_url)
                                    time.sleep(5)
                                except KeyboardInterrupt:
                                    break
                                except Exception:
                                    time.sleep(5)
                                    
                    except Exception as e2:
                        logger.error(f"❌ Error during monitoring: {e2}")
                else:
                    logger.error("❌ Failed to connect to Chrome after launching. Maybe profile was not selected?")
            else:
                 logger.error("❌ Auto-launch failed.")
    
    logger.info("\n" + "=" * 70)
    logger.info("Monitor stopped")
    logger.info("=" * 70)


if __name__ == "__main__":
    try:
        watch_whatsapp()
    except KeyboardInterrupt:
        logger.info("\n👋 Goodbye!")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
