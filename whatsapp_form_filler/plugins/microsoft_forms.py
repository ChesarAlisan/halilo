"""
Microsoft Forms plugin - optimized for Turkish educational forms.
"""
import re
from typing import Optional
from playwright.sync_api import Page, Locator
from loguru import logger

from database.models import UserData, FieldMapping, FormProvider
from plugins.base import FormProviderPlugin
from utils import HumanBehavior, ReadingPatterns


class MicrosoftFormsPlugin(FormProviderPlugin):
    """Microsoft Forms (forms.office.com) handler."""
    
    @property
    def provider_name(self) -> FormProvider:
        return FormProvider.MICROSOFT_FORMS
    
    def can_handle(self, url: str) -> bool:
        """Check if URL is Microsoft Forms."""
        return 'forms.office.com' in url.lower() or 'forms.microsoft.com' in url.lower()
    
    def analyze_form(self, page: Page) -> Optional[FieldMapping]:
        """
        Analyze Microsoft Forms using rule-based Turkish NLP.
        
        Args:
            page: Playwright page with loaded form
            
        Returns:
            FieldMapping if successful
        """
        logger.info("🔍 Analyzing Microsoft Forms structure...")
        
        # Wait for form to load (increased timeout for login redirects)
        try:
            page.wait_for_selector('[data-automation-id="questionItem"]', timeout=30000)
        except Exception as e:
            logger.error(f"Form did not load properly: {e}")
            return None
        
        # Scan the form like a human would
        ReadingPatterns.scan_form(page)
        
        mapping = FieldMapping()
        
        # Find all question items
        questions = page.query_selector_all('[data-automation-id="questionItem"]')
        logger.info(f"Found {len(questions)} questions")
        
        for idx, question in enumerate(questions):
            try:
                # Get question text
                title_element = question.query_selector('[data-automation-id="questionTitle"]')
                if not title_element:
                    continue
                
                question_text = (title_element.inner_text()).lower().strip()
                logger.debug(f"Question {idx + 1}: {question_text}")
                
                # PATTERN MATCHING for Turkish forms
                
                # 1. NAME FIELD
                if self._is_name_field(question_text):
                    input_field = question.query_selector('input[type="text"]')
                    if input_field:
                        selector = self._get_stable_selector(input_field)
                        mapping.name_field = selector
                        logger.info(f"✅ Found name field: {question_text}")
                
                # 2. STUDENT ID FIELD
                elif self._is_student_id_field(question_text):
                    input_field = question.query_selector('input[type="text"]')
                    if input_field:
                        selector = self._get_stable_selector(input_field)
                        mapping.student_id_field = selector
                        logger.info(f"✅ Found student ID field: {question_text}")
                
                # 3. ATTENDANCE CHECKBOX
                elif self._is_attendance_checkbox(question_text):
                    # Look for checkbox
                    checkbox = question.query_selector('input[type="checkbox"]')
                    if checkbox:
                        selector = self._get_stable_selector(checkbox)
                        mapping.attendance_checkbox = selector
                        logger.info(f"✅ Found attendance checkbox: {question_text}")
                    else:
                        # Maybe it's a radio button or choice
                        choice = question.query_selector('[data-automation-id="choiceItem"]')
                        if choice:
                            selector = self._get_stable_selector(choice)
                            mapping.attendance_checkbox = selector
                            logger.info(f"✅ Found attendance choice: {question_text}")
            
            except Exception as e:
                logger.warning(f"Error analyzing question {idx + 1}: {e}")
                continue
        
        # Find submit button
        submit_btn = page.query_selector('button[data-automation-id="submitButton"]')
        if not submit_btn:
            # Fallback: look for "Gönder" text
            buttons = page.query_selector_all('button')
            for btn in buttons:
                btn_text = (btn.inner_text()).lower()
                if 'gönder' in btn_text or 'submit' in btn_text:
                    submit_btn = btn
                    break
        
        if submit_btn:
            mapping.submit_button = self._get_stable_selector(submit_btn)
            logger.info("✅ Found submit button")
        
        # Calculate confidence
        if mapping.is_complete():
            mapping.confidence = 1.0
            logger.success(f"🎯 Form analysis complete - confidence: {mapping.confidence}")
        else:
            missing = mapping.get_missing_fields()
            mapping.confidence = (4 - len(missing)) / 4.0
            logger.warning(f"⚠️  Missing fields: {missing} - confidence: {mapping.confidence}")
        
        return mapping
    
    def _is_name_field(self, text: str) -> bool:
        """Check if text indicates name field."""
        patterns = [
            r'(ad|isim|name).*soyad',
            r'ad\s*(ve|-)?\s*soyad',
            r'tam\s*ad',
            r'öğrenci\s*ad',
            r'student\s*name',
            r'full\s*name',
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _is_student_id_field(self, text: str) -> bool:
        """Check if text indicates student ID field."""
        patterns = [
            r'öğrenci\s*no',
            r'öğrenci\s*numara',
            r'student\s*id',
            r'student\s*number',
            r'numara',
            r'\bno\b',  # Just "no" with word boundaries
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _is_attendance_checkbox(self, text: str) -> bool:
        """Check if text indicates attendance checkbox."""
        patterns = [
            r'katılım',
            r'onay',
            r'attendance',
            r'ders.*onay',
            r'e-onay',
            r'confirm',
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _get_stable_selector(self, element: Locator) -> str:
        """
        Get a stable selector for an element.
        
        Args:
            element: Playwright locator
            
        Returns:
            CSS selector string
        """
        # Try to get data-automation-id first (most stable)
        automation_id = element.get_attribute('data-automation-id')
        if automation_id:
            return f'[data-automation-id="{automation_id}"]'
        
        # Fallback to ID
        elem_id = element.get_attribute('id')
        if elem_id:
            return f'#{elem_id}'
        
        # Last resort: name attribute
        name = element.get_attribute('name')
        if name:
            return f'[name="{name}"]'
        
        # Very last resort: create xpath
        return 'body'  # Simplified fallback
    
    def fill_form(
        self,
        page: Page,
        field_mapping: FieldMapping,
        user_data: UserData
    ) -> bool:
        """
        Fill Microsoft Forms with human-like behavior.
        
        Args:
            page: Playwright page
            field_mapping: Field selectors
            user_data: User data to fill
            
        Returns:
            True if successful
        """
        logger.info("✍️  Filling form...")
        
        try:
            # Fill name field
            if field_mapping.name_field:
                logger.debug(f"Filling name: {user_data.student_name}")
                name_input = page.locator(field_mapping.name_field)
                HumanBehavior.human_type(name_input, user_data.student_name, page)
            
            # Fill student ID
            if field_mapping.student_id_field:
                logger.debug(f"Filling student ID: {user_data.student_id}")
                id_input = page.locator(field_mapping.student_id_field)
                HumanBehavior.human_type(id_input, user_data.student_id, page)
            
            # Check attendance checkbox
            if field_mapping.attendance_checkbox:
                logger.debug("Checking attendance checkbox")
                checkbox = page.locator(field_mapping.attendance_checkbox)
                HumanBehavior.checkbox_with_verification(checkbox, page)
            
            logger.success("✅ Form filled successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error filling form: {e}")
            return False
    
    def submit_form(
        self,
        page: Page,
        field_mapping: FieldMapping
    ) -> bool:
        """
        Submit the form.
        
        Args:
            page: Playwright page
            field_mapping: Field mapping with submit button
            
        Returns:
            True if successful
        """
        if not field_mapping.submit_button:
            logger.error("No submit button found")
            return False
        
        try:
            logger.info("📤 Submitting form...")
            submit_btn = page.locator(field_mapping.submit_button)
            
            # Human-like click
            HumanBehavior.human_click(submit_btn, page)
            
            # Wait for navigation or confirmation
            try:
                page.wait_for_load_state('networkidle', timeout=10000)
            except:
                # Sometimes forms don't trigger full reload
                page.wait_for_timeout(3000)
            
            logger.success("✅ Form submitted")
            return True
        
        except Exception as e:
            logger.error(f"Error submitting form: {e}")
            return False
    
    def verify_submission(self, page: Page) -> bool:
        """
        Verify Microsoft Forms submission success.
        
        Args:
            page: Playwright page after submission
            
        Returns:
            True if verified successful
        """
        logger.info("🔍 Verifying submission...")
        
        # Success indicators in Turkish and English
        success_indicators = [
            "yanıtınız kaydedildi",
            "teşekkürler",
            "gönderildi",
            "your response has been recorded",
            "thank you",
            "response recorded",
            "başarıyla gönderildi",
        ]
        
        try:
            # Get page text
            page_text = (page.inner_text('body')).lower()
            
            # Check for success indicators
            for indicator in success_indicators:
                if indicator in page_text:
                    logger.success(f"✅ Submission verified: Found '{indicator}'")
                    return True
            
            # Check for success message element
            success_elem = page.query_selector('[data-automation-id="thankYouMessage"]')
            if success_elem:
                logger.success("✅ Submission verified: Found thank you message element")
                return True
            
            logger.warning("⚠️  Could not verify submission - no success indicators found")
            logger.debug(f"Page text preview: {page_text[:200]}")
            return False
        
        except Exception as e:
            logger.error(f"Error verifying submission: {e}")
            return False
