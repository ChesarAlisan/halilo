"""
Human behavior simulation for realistic browser interactions.
"""
import random
import time
from typing import Optional
from playwright.sync_api import Page, Locator


class HumanBehavior:
    """Simulates human-like behavior in browser automation."""
    
    @staticmethod
    def random_delay(min_ms: int = 500, max_ms: int = 2000) -> float:
        """
        Get random delay in seconds.
        
        Args:
            min_ms: Minimum delay in milliseconds
            max_ms: Maximum delay in milliseconds
            
        Returns:
            Delay in seconds
        """
        return random.randint(min_ms, max_ms) / 1000.0
    
    @staticmethod
    def typing_delay() -> int:
        """
        Get random typing delay per character.
        
        Returns:
            Delay in milliseconds
        """
        # Humans type at 40-80 WPM = 200-400ms per char
        # Add variation
        base_delay = random.randint(50, 150)
        
        # Occasionally slow down (thinking)
        if random.random() < 0.1:  # 10% chance
            base_delay += random.randint(200, 500)
        
        return base_delay
    
    @staticmethod
    def human_click(locator: Locator, page: Page) -> None:
        """
        Perform humanlike click with hover and delay.
        
        Args:
            locator: Element to click
            page: Playwright page instance
        """
        # Scroll into view if needed
        locator.scroll_into_view_if_needed()
        page.wait_for_timeout(HumanBehavior.random_delay(100, 300) * 1000)
        
        # Hover over element
        locator.hover()
        page.wait_for_timeout(HumanBehavior.random_delay(200, 500) * 1000)
        
        # Click
        locator.click()
        page.wait_for_timeout(HumanBehavior.random_delay(300, 800) * 1000)
    
    @staticmethod
    def human_type(locator: Locator, text: str, page: Page) -> None:
        """
        Type text with human-like delays.
        
        Args:
            locator: Input element to type into
            text: Text to type
            page: Playwright page instance
        """
        # Click the input field
        HumanBehavior.human_click(locator, page)
        
        # Clear existing content
        locator.clear()
        page.wait_for_timeout(HumanBehavior.random_delay(100, 300) * 1000)
        
        # Type character by character
        locator.type(text, delay=HumanBehavior.typing_delay())
        
        # Random pause after typing
        page.wait_for_timeout(HumanBehavior.random_delay(300, 700) * 1000)
    
    @staticmethod
    def human_scroll(page: Page, direction: str = "down", amount: int = 300) -> None:
        """
        Perform human-like scrolling.
        
        Args:
            page: Playwright page instance
            direction: 'down' or 'up'
            amount: Pixels to scroll
        """
        scroll_amount = amount if direction == "down" else -amount
        
        # Scroll in chunks (humans don't scroll in one motion)
        chunks = random.randint(3, 6)
        per_chunk = scroll_amount // chunks
        
        for _ in range(chunks):
            page.evaluate(f"window.scrollBy(0, {per_chunk})")
            page.wait_for_timeout(random.randint(50, 150))
        
        # Pause after scroll
        page.wait_for_timeout(HumanBehavior.random_delay(200, 500) * 1000)
    
    @staticmethod
    def random_mouse_movement(page: Page, num_movements: int = 3) -> None:
        """
        Move mouse randomly across the page.
        
        Args:
            page: Playwright page instance
            num_movements: Number of random movements
        """
        viewport = page.viewport_size
        
        for _ in range(num_movements):
            x = random.randint(100, viewport['width'] - 100)
            y = random.randint(100, viewport['height'] - 100)
            
            # Move mouse in steps (humans don't teleport)
            page.mouse.move(x, y, steps=random.randint(5, 15))
            page.wait_for_timeout(random.randint(100, 300))
    
    @staticmethod
    def reading_pause(page: Page, content_length: Optional[int] = None) -> None:
        """
        Pause as if reading content.
        
        Args:
            page: Playwright page instance
            content_length: Length of content to read (affects pause duration)
        """
        if content_length is None:
            # Default reading pause
            pause = HumanBehavior.random_delay(1000, 3000)
        else:
            # Estimate reading time (avg 200 words/min = 3.3 words/sec)
            # Assume 5 chars per word
            words = content_length / 5
            seconds = words / 3.3
            # Add randomness
            pause = seconds * random.uniform(0.7, 1.3)
        
        page.wait_for_timeout(int(pause * 1000))
    
    @staticmethod
    def occasional_mistake() -> bool:
        """
        Determine if a human-like mistake should occur.
        
        Returns:
            True if should make a mistake (5% chance)
        """
        return random.random() < 0.05
    
    @staticmethod
    def checkbox_with_verification(locator: Locator, page: Page) -> None:
        """
        Check a checkbox and verify it's checked (humans double-check).
        
        Args:
            locator: Checkbox element
            page: Playwright page instance
        """
        HumanBehavior.human_click(locator, page)
        
        # Verify it's checked
        is_checked = locator.is_checked()
        
        if not is_checked:
            # Try again if not checked (occasional click miss)
            page.wait_for_timeout(HumanBehavior.random_delay(500, 1000) * 1000)
            locator.check()
            page.wait_for_timeout(HumanBehavior.random_delay(300, 600) * 1000)


class ReadingPatterns:
    """Simulate realistic reading patterns."""
    
    @staticmethod
    def scan_form(page: Page) -> None:
        """
        Simulate scanning a form before filling.
        
        Args:
            page: Playwright page instance
        """
        # Scroll to top
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(HumanBehavior.random_delay(300, 600) * 1000)
        
        # Scroll through form
        HumanBehavior.human_scroll(page, "down", 200)
        HumanBehavior.reading_pause(page)
        
        # Maybe scroll back up
        if random.random() < 0.3:  # 30% chance
            HumanBehavior.human_scroll(page, "up", 100)
            page.wait_for_timeout(HumanBehavior.random_delay(200, 400) * 1000)
        
        # Scroll to top again
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(HumanBehavior.random_delay(200, 400) * 1000)
