"""
Form Intelligence Agent - Analyzes forms and identifies fields.
"""
from typing import Optional
from playwright.sync_api import Page
from loguru import logger

from database.models import FieldMapping, FormProvider
from plugins import ALL_PLUGINS
from plugins.base import FormProviderPlugin


class FormIntelligenceAgent:
    """
    Analyzes forms using plugin system (rule-based + AI fallback).
    """
    
    def __init__(self):
        """Initialize form intelligence agent."""
        self.plugins = ALL_PLUGINS
        logger.info(f"🧠 Form Intelligence Agent initialized with {len(self.plugins)} plugins")
    
    def identify_provider(self, url: str) -> Optional[FormProviderPlugin]:
        """
        Identify which plugin can handle the URL.
        
        Args:
            url: Form URL
            
        Returns:
            Plugin instance if found, None otherwise
        """
        for plugin in self.plugins:
            if plugin.can_handle(url):
                logger.info(f"✅ Provider identified: {plugin.provider_name.value}")
                return plugin
        
        logger.warning(f"⚠️  No plugin found for URL: {url}")
        return None
    
    def analyze_form(
        self,
        page: Page,
        url: str
    ) -> tuple[Optional[FormProviderPlugin], Optional[FieldMapping]]:
        """
        Analyze form and return field mapping.
        
        Args:
            page: Playwright page with loaded form
            url: Form URL
            
        Returns:
            Tuple of (plugin, field_mapping)
        """
        logger.info("🔍 Starting form analysis...")
        
        # Identify provider
        plugin = self.identify_provider(url)
        if not plugin:
            logger.error("Cannot analyze form - unknown provider")
            return None, None
        
        # Analyze with plugin
        field_mapping = plugin.analyze_form(page)
        
        if field_mapping and field_mapping.is_complete():
            logger.success(
                f"✅ Form analyzed successfully - "
                f"confidence: {field_mapping.confidence:.2f}"
            )
        elif field_mapping:
            missing = field_mapping.get_missing_fields()
            logger.warning(
                f"⚠️  Incomplete mapping - missing: {missing} - "
                f"confidence: {field_mapping.confidence:.2f}"
            )
        else:
            logger.error("❌ Form analysis failed")
        
        return plugin, field_mapping
