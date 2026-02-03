"""
Google Forms plugin (Phase 3 - placeholder).
"""
from typing import Optional
from playwright.sync_api import Page
from loguru import logger

from database.models import UserData, FieldMapping, FormProvider
from plugins.base import FormProviderPlugin


class GoogleFormsPlugin(FormProviderPlugin):
    """Google Forms handler (coming in Phase 3)."""
    
    @property
    def provider_name(self) -> FormProvider:
        return FormProvider.GOOGLE_FORMS
    
    def can_handle(self, url: str) -> bool:
        """Check if URL is Google Forms."""
        return 'docs.google.com/forms' in url.lower()
    
    async def analyze_form(self, page: Page) -> Optional[FieldMapping]:
        """Not yet implemented."""
        logger.warning("Google Forms plugin not yet implemented (Phase 3)")
        return None
    
    async def fill_form(
        self,
        page: Page,
        field_mapping: FieldMapping,
        user_data: UserData
    ) -> bool:
        """Not yet implemented."""
        return False
    
    async def submit_form(
        self,
        page: Page,
        field_mapping: FieldMapping
    ) -> bool:
        """Not yet implemented."""
        return False
    
    async def verify_submission(self, page: Page) -> bool:
        """Not yet implemented."""
        return False
