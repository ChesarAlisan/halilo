"""
Stealth mode configuration for Playwright to avoid bot detection.
"""
from playwright.sync_api import Page, BrowserContext, Browser
import random


def configure_stealth_context(context: BrowserContext) -> None:
    """
    Configure browser context with anti-detection measures.
    
    Args:
        context: Playwright browser context to configure
    """
    # Add init script to hide webdriver
    context.add_init_script("""
        // Overwrite the `navigator.webdriver` property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Overwrite the `chrome` property
        window.chrome = {
            runtime: {},
        };
        
        // Overwrite the `permissions` property
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Overwrite the `plugins` property
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // Overwrite the `languages` property
        Object.defineProperty(navigator, 'languages', {
            get: () => ['tr-TR', 'tr', 'en-US', 'en'],
        });
    """)


def get_stealthy_browser_args() -> list[str]:
    """
    Get browser launch arguments that reduce detection.
    
    Returns:
        List of command-line arguments for Chromium
    """
    return [
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-infobars',
        '--window-position=0,0',
        '--ignore-certificate-errors',
        '--ignore-certificate-errors-spki-list',
        '--disable-blink-features',
        '--disable-features=IsolateOrigins,site-per-process',
    ]


def get_realistic_viewport() -> dict:
    """
    Get realistic viewport dimensions.
    
    Returns:
        Dictionary with width and height
    """
    # Common resolutions
    resolutions = [
        {'width': 1920, 'height': 1080},  # 1080p
        {'width': 1366, 'height': 768},   # Common laptop
        {'width': 1536, 'height': 864},   # Surface
        {'width': 1440, 'height': 900},   # MacBook
    ]
    return random.choice(resolutions)


def get_realistic_user_agent() -> str:
    """
    Get a realistic user agent string.
    
    Returns:
        User agent string
    """
    # Real user agents - Windows Chrome
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    ]
    return random.choice(user_agents)


async def add_mouse_jitter(page: Page) -> None:
    """
    Add subtle mouse movements to appear more human.
    
    Args:
        page: Playwright page instance
    """
    # Random small mouse movements
    for _ in range(random.randint(2, 5)):
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        await page.mouse.move(x, y)
        await page.wait_for_timeout(random.randint(50, 150))


def get_context_options(locale: str = "tr-TR", timezone: str = "Europe/Istanbul") -> dict:
    """
    Get browser context options with stealth configuration.
    
    Args:
        locale: Browser locale
        timezone: Browser timezone
        
    Returns:
        Dictionary of context options
    """
    viewport = get_realistic_viewport()
    
    return {
        'viewport': viewport,
        'user_agent': get_realistic_user_agent(),
        'locale': locale,
        'timezone_id': timezone,
        'geolocation': {'latitude': 41.0082, 'longitude': 28.9784},  # Istanbul
        'permissions': ['geolocation'],
        'color_scheme': 'light',
        'has_touch': False,
        'is_mobile': False,
        'java_script_enabled': True,
        'accept_downloads': True,
        'extra_http_headers': {
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    }
