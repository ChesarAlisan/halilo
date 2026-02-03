"""
Simple test script to fill a Microsoft Form.
Just run: python test_form.py
"""
from playwright.sync_api import sync_playwright
from loguru import logger
import time
import os

# ============================================================
# CONFIGURATION - Edit these
# ============================================================
FORM_URL = "https://forms.office.com/Pages/ResponsePage.aspx?id=gCO8a9-CREaDOE-no4zyBZ_AEcdYFppHgDZ0tyK76ldUNzUwUjdPR0YxWEhFQ1IyMlBFRDdGN0w5Ry4u"
STUDENT_NAME = "Halil Eren Kepiç"
STUDENT_ID = "2306002093"
# ============================================================

def fill_form():
    """Fill the Microsoft Form using Chrome profile."""
    
    logger.info("🚀 Starting Chrome...")
    
    # Chrome profile path
    chrome_profile = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")
    
    if not os.path.exists(chrome_profile):
        logger.error("❌ Chrome profile not found!")
        logger.error(f"Expected path: {chrome_profile}")
        return
    
    logger.info(f"🔐 Using Chrome profile: {chrome_profile}")
    
    with sync_playwright() as p:
        # Launch Chrome with persistent context (uses your logged-in profile)
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=chrome_profile,
                headless=False,
                channel='chrome',  # MUST use Chrome (not Chromium)
                slow_mo=100,  # Slow down a bit so you can see
            )
        except Exception as e:
            logger.error(f"❌ Could not launch Chrome: {e}")
            logger.error("Make sure Chrome is CLOSED before running this script!")
            return
        
        # Get first page or create new one
        if len(context.pages) > 0:
            page = context.pages[0]
        else:
            page = context.new_page()
        
        try:
            # Go to form
            logger.info(f"📋 Opening form: {FORM_URL}")
            page.goto(FORM_URL, wait_until='networkidle', timeout=60000)
            
            # Wait a bit for any redirects (like Microsoft login)
            logger.info("⏳ Waiting for form to load (30 seconds)...")
            time.sleep(5)
            
            # Try to wait for form questions
            try:
                page.wait_for_selector('[data-automation-id="questionItem"]', timeout=25000)
                logger.success("✅ Form loaded!")
            except:
                logger.warning("⚠️  Form may need login - waiting longer...")
                logger.info("👉 If you see login screen, please login manually now!")
                logger.info("⏰ Waiting 60 seconds for you to login...")
                time.sleep(60)
            
            # Take screenshot before filling
            page.screenshot(path='before_fill.png')
            logger.info("📸 Screenshot: before_fill.png")
            
            # Find all input fields
            logger.info("🔍 Looking for form fields...")
            
            # Get all questions
            questions = page.query_selector_all('[data-automation-id="questionItem"]')
            logger.info(f"Found {len(questions)} questions")
            
            for idx, question in enumerate(questions):
                try:
                    # Get question text
                    title_elem = question.query_selector('[data-automation-id="questionTitle"]')
                    if not title_elem:
                        continue
                    
                    question_text = title_elem.inner_text().lower()
                    logger.info(f"Question {idx+1}: {question_text}")
                    
                    # Check what type of field
                    if 'ad' in question_text or 'soyad' in question_text or 'isim' in question_text:
                        # Name field
                        input_field = question.query_selector('input[type="text"]')
                        if input_field:
                            logger.info(f"✍️  Filling name: {STUDENT_NAME}")
                            input_field.click()
                            time.sleep(0.5)
                            input_field.fill(STUDENT_NAME)
                            time.sleep(1)
                    
                    elif 'no' in question_text or 'numara' in question_text:
                        # Student ID field
                        input_field = question.query_selector('input[type="text"]')
                        if input_field:
                            logger.info(f"✍️  Filling student ID: {STUDENT_ID}")
                            input_field.click()
                            time.sleep(0.5)
                            input_field.fill(STUDENT_ID)
                            time.sleep(1)
                    
                    elif 'katılım' in question_text or 'onay' in question_text or 'ders' in question_text:
                        # Attendance checkbox
                        checkbox = question.query_selector('input[type="checkbox"]')
                        if checkbox:
                            logger.info("✅ Checking attendance box")
                            checkbox.check()
                            time.sleep(1)
                
                except Exception as e:
                    logger.warning(f"Could not process question {idx+1}: {e}")
            
            # Take screenshot after filling
            page.screenshot(path='after_fill.png')
            logger.info("📸 Screenshot: after_fill.png")
            
            # Find and click submit button
            logger.info("🔍 Looking for submit button...")
            
            # Try standard submit button
            submit_btn = page.query_selector('button[data-automation-id="submitButton"]')
            
            if not submit_btn:
                # Try to find by text
                buttons = page.query_selector_all('button')
                for btn in buttons:
                    btn_text = btn.inner_text().lower()
                    if 'gönder' in btn_text or 'submit' in btn_text:
                        submit_btn = btn
                        break
            
            if submit_btn:
                logger.info("📤 Clicking submit button...")
                submit_btn.click()
                time.sleep(5)
                
                # Take screenshot after submission
                page.screenshot(path='after_submit.png')
                logger.info("📸 Screenshot: after_submit.png")
                
                # Check for success message
                page_text = page.inner_text('body').lower()
                
                if 'kaydedildi' in page_text or 'teşekkür' in page_text or 'recorded' in page_text:
                    logger.success("🎉 SUCCESS! Form submitted!")
                else:
                    logger.warning("⚠️  Form submitted but no confirmation message found")
            else:
                logger.error("❌ Could not find submit button")
            
            # Wait a bit so you can see the result
            logger.info("⏳ Waiting 5 seconds before closing...")
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            page.screenshot(path='error.png')
            logger.info("📸 Error screenshot: error.png")
        
        finally:
            context.close()
            logger.info("✅ Chrome closed")


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("📝 Microsoft Forms Auto-Fill Test")
    logger.info("=" * 70)
    logger.info(f"Form: {FORM_URL}")
    logger.info(f"Student: {STUDENT_NAME}")
    logger.info(f"ID: {STUDENT_ID}")
    logger.info("=" * 70)
    logger.info("")
    
    fill_form()
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("Done! Check the screenshots:")
    logger.info("  - before_fill.png")
    logger.info("  - after_fill.png")
    logger.info("  - after_submit.png")
    logger.info("=" * 70)
