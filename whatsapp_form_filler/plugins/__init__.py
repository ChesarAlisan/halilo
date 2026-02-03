"""Plugins module initialization."""
from .base import FormProviderPlugin
from .microsoft_forms import MicrosoftFormsPlugin
from .google_forms import GoogleFormsPlugin
from .moodle import MoodlePlugin

# Registry of all available plugins
ALL_PLUGINS = [
    MicrosoftFormsPlugin(),
    GoogleFormsPlugin(),
    MoodlePlugin(),
]

__all__ = [
    "FormProviderPlugin",
    "MicrosoftFormsPlugin",
    "GoogleFormsPlugin",
    "MoodlePlugin",
    "ALL_PLUGINS",
]
