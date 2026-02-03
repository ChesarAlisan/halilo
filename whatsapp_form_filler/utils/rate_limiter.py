"""
Rate limiting to prevent WhatsApp bans and Microsoft Forms blocks.
"""
import time
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger


class RateLimiter:
    """
    Controls the rate of form submissions to avoid detection.
    """
    
    def __init__(
        self,
        min_delay_seconds: int = 60,
        max_per_hour: int = 10,
        break_after_n: int = 5,
        break_duration_seconds: int = 300
    ):
        """
        Initialize rate limiter.
        
        Args:
            min_delay_seconds: Minimum seconds between submissions
            max_per_hour: Maximum submissions per hour
            break_after_n: Take break after N consecutive submissions
            break_duration_seconds: Duration of break in seconds
        """
        self.min_delay_seconds = min_delay_seconds
        self.max_per_hour = max_per_hour
        self.break_after_n = break_after_n
        self.break_duration_seconds = break_duration_seconds
        
        self.last_submission: Optional[datetime] = None
        self.consecutive_count = 0
        self.hourly_submissions: list[datetime] = []
    
    def can_proceed(self) -> bool:
        """
        Check if we can proceed with next submission.
        
        Returns:
            True if can proceed, False if need to wait
        """
        now = datetime.now()
        
        # Check minimum delay
        if self.last_submission:
            elapsed = (now - self.last_submission).total_seconds()
            if elapsed < self.min_delay_seconds:
                logger.warning(
                    f"Rate limit: Need to wait {self.min_delay_seconds - elapsed:.1f}s more"
                )
                return False
        
        # Check hourly limit
        one_hour_ago = now - timedelta(hours=1)
        self.hourly_submissions = [
            ts for ts in self.hourly_submissions
            if ts > one_hour_ago
        ]
        
        if len(self.hourly_submissions) >= self.max_per_hour:
            oldest = min(self.hourly_submissions)
            wait_until = oldest + timedelta(hours=1)
            wait_seconds = (wait_until - now).total_seconds()
            logger.warning(
                f"Rate limit: Hourly limit reached. Wait {wait_seconds:.0f}s"
            )
            return False
        
        # Check if need break
        if self.consecutive_count >= self.break_after_n:
            logger.info(
                f"Taking mandatory break after {self.consecutive_count} submissions "
                f"for {self.break_duration_seconds}s"
            )
            return False
        
        return True
    
    def wait_if_needed(self) -> None:
        """
        Block until we can proceed (with logging).
        """
        while not self.can_proceed():
            # Check if need break
            if self.consecutive_count >= self.break_after_n:
                logger.info(f"🛑 BREAK TIME: {self.break_duration_seconds}s rest")
                time.sleep(self.break_duration_seconds)
                self.consecutive_count = 0
                logger.info("✅ Break complete, resuming...")
                continue
            
            # Check minimum delay
            if self.last_submission:
                now = datetime.now()
                elapsed = (now - self.last_submission).total_seconds()
                if elapsed < self.min_delay_seconds:
                    wait_time = self.min_delay_seconds - elapsed
                    logger.info(f"⏳ Waiting {wait_time:.1f}s before next submission...")
                    time.sleep(wait_time)
                    continue
            
            # Check hourly limit
            now = datetime.now()
            one_hour_ago = now - timedelta(hours=1)
            self.hourly_submissions = [
                ts for ts in self.hourly_submissions
                if ts > one_hour_ago
            ]
            
            if len(self.hourly_submissions) >= self.max_per_hour:
                oldest = min(self.hourly_submissions)
                wait_until = oldest + timedelta(hours=1)
                wait_seconds = (wait_until - now).total_seconds()
                logger.warning(
                    f"⏱️  Hourly limit reached. Waiting {wait_seconds/60:.1f} minutes..."
                )
                time.sleep(min(wait_seconds, 60))  # Check every minute
                continue
            
            break
    
    def record_submission(self) -> None:
        """
        Record that a submission occurred.
        """
        now = datetime.now()
        self.last_submission = now
        self.consecutive_count += 1
        self.hourly_submissions.append(now)
        
        logger.info(
            f"📊 Rate limiter stats: "
            f"consecutive={self.consecutive_count}, "
            f"hourly={len(self.hourly_submissions)}/{self.max_per_hour}"
        )
    
    def reset_consecutive(self) -> None:
        """
        Reset consecutive counter (e.g., after manual break).
        """
        self.consecutive_count = 0
        logger.info("🔄 Consecutive counter reset")
    
    def get_stats(self) -> dict:
        """
        Get current rate limiter statistics.
        
        Returns:
            Dictionary with stats
        """
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # Clean old submissions
        self.hourly_submissions = [
            ts for ts in self.hourly_submissions
            if ts > one_hour_ago
        ]
        
        time_since_last = None
        if self.last_submission:
            time_since_last = (now - self.last_submission).total_seconds()
        
        return {
            'consecutive_count': self.consecutive_count,
            'hourly_count': len(self.hourly_submissions),
            'max_per_hour': self.max_per_hour,
            'time_since_last_submission': time_since_last,
            'can_proceed': self.can_proceed(),
            'need_break': self.consecutive_count >= self.break_after_n,
        }
