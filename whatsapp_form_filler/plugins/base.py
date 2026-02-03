"""
Plugin base class for form providers.
"""
from abc import ABC, abstractmethod
from typing import Optional
from playwright.sync_api import Page
from database.models import UserData, FieldMapping, FormProvider


class FormProviderPlugin(ABC):
    """Abstract base class for form provider plugins."""
    
    @property
    @abstractmethod
    def provider_name(self) -> FormProvider:
        """Return the provider enum value."""
        pass
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """
        Check if this plugin can handle the given URL.
        
        Args:
            url: Form URL to check
            
        Returns:
            True if this plugin can handle the URL
        """
        pass
    
    @abstractmethod
    def analyze_form(self, page: Page) -> Optional[FieldMapping]:
        """
        Analyze the form and identify fields.
        
        Args:
            page: Playwright page with loaded form
            
        Returns:
            FieldMapping if successful, None otherwise
        """
        pass
    
    @abstractmethod
    def fill_form(
        self,
        page: Page,
        field_mapping: FieldMapping,
        user_data: UserData
    ) -> bool:
        """
        Fill the form with user data.
        
        Args:
            page: Playwright page with loaded form
            field_mapping: Identified field selectors
            user_data: User information to fill
            
        Returns:
            True if filling was successful
        """
        pass
    
    @abstractmethod
    def submit_form(
        self,
        page: Page,
        field_mapping: FieldMapping
    ) -> bool:
        """
        Submit the form.
        
        Args:
            page: Playwright page with filled form
            field_mapping: Field mapping with submit button
            
        Returns:
            True if submission was successful
        """
        pass
    
    @abstractmethod
    def verify_submission(self, page: Page) -> bool:
        """
        Verify that form was submitted successfully.
        
        Args:
            page: Playwright page after submission
            
        Returns:
            True if submission was verified as successful
        """
        pass
