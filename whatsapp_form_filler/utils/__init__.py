"""Utils module initialization."""
from .stealth import (
    configure_stealth_context,
    get_stealthy_browser_args,
    get_realistic_viewport,
    get_realistic_user_agent,
    get_context_options,
    add_mouse_jitter,
)
from .human_behavior import HumanBehavior, ReadingPatterns
from .rate_limiter import RateLimiter
from .notifications import NotificationManager

__all__ = [
    "configure_stealth_context",
    "get_stealthy_browser_args",
    "get_realistic_viewport",
    "get_realistic_user_agent",
    "get_context_options",
    "add_mouse_jitter",
    "HumanBehavior",
    "ReadingPatterns",
    "RateLimiter",
    "NotificationManager",
]
