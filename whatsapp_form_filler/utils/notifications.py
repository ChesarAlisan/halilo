"""
Notification system for desktop and Telegram alerts.
"""
import os
from typing import Optional
from loguru import logger

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    logger.warning("plyer not installed - desktop notifications disabled")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not installed - Telegram notifications disabled")


class NotificationManager:
    """Handles desktop and Telegram notifications."""
    
    def __init__(
        self,
        enable_desktop: bool = True,
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None
    ):
        """
        Initialize notification manager.
        
        Args:
            enable_desktop: Enable desktop notifications
            telegram_bot_token: Telegram bot token (optional)
            telegram_chat_id: Telegram chat ID (optional)
        """
        self.enable_desktop = enable_desktop and PLYER_AVAILABLE
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.telegram_enabled = (
            REQUESTS_AVAILABLE and
            telegram_bot_token is not None and
            telegram_chat_id is not None
        )
    
    def send_desktop_notification(
        self,
        title: str,
        message: str,
        timeout: int = 10
    ) -> None:
        """
        Send desktop notification.
        
        Args:
            title: Notification title
            message: Notification message
            timeout: Notification display time in seconds
        """
        if not self.enable_desktop or not PLYER_AVAILABLE:
            return
        
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="WhatsApp Form Filler",
                timeout=timeout
            )
            logger.debug(f"Desktop notification sent: {title}")
        except Exception as e:
            logger.error(f"Failed to send desktop notification: {e}")
    
    def send_telegram_message(
        self,
        message: str,
        parse_mode: str = "HTML"
    ) -> bool:
        """
        Send Telegram message.
        
        Args:
            message: Message text (supports HTML formatting)
            parse_mode: 'HTML' or 'Markdown'
            
        Returns:
            True if sent successfully
        """
        if not self.telegram_enabled:
            return False
        
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        
        payload = {
            'chat_id': self.telegram_chat_id,
            'text': message,
            'parse_mode': parse_mode
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.debug("Telegram message sent successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def notify_success(
        self,
        form_url: str,
        student_name: str,
        processing_time: float
    ) -> None:
        """
        Send success notification.
        
        Args:
            form_url: Form URL that was submitted
            student_name: Student name
            processing_time: Time taken in seconds
        """
        title = "✅ Form Başarıyla Gönderildi"
        message = f"Öğrenci: {student_name}\nSüre: {processing_time:.1f}s"
        
        self.send_desktop_notification(title, message)
        
        if self.telegram_enabled:
            telegram_msg = f"""
✅ <b>Form Başarıyla Gönderildi</b>

👤 <b>Öğrenci:</b> {student_name}
🔗 <b>URL:</b> {form_url[:50]}...
⏱️ <b>Süre:</b> {processing_time:.1f} saniye
            """.strip()
            self.send_telegram_message(telegram_msg)
    
    def notify_error(
        self,
        error_type: str,
        form_url: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Send error notification.
        
        Args:
            error_type: Type of error
            form_url: Form URL (if applicable)
            error_message: Error details
        """
        title = f"❌ Hata: {error_type}"
        message = error_message[:200] if error_message else "Detaylar log dosyasında"
        
        self.send_desktop_notification(title, message, timeout=15)
        
        if self.telegram_enabled:
            telegram_msg = f"""
❌ <b>Hata Oluştu</b>

🔴 <b>Hata Tipi:</b> {error_type}
            """
            
            if form_url:
                telegram_msg += f"\n🔗 <b>URL:</b> {form_url[:50]}..."
            
            if error_message:
                telegram_msg += f"\n📝 <b>Detay:</b> {error_message[:200]}"
            
            self.send_telegram_message(telegram_msg)
    
    def notify_captcha(self, form_url: str) -> None:
        """
        Send CAPTCHA notification (urgent - needs manual intervention).
        
        Args:
            form_url: Form URL with CAPTCHA
        """
        title = "🔴 CAPTCHA Algılandı!"
        message = "Manuel müdahale gerekli"
        
        self.send_desktop_notification(title, message, timeout=60)
        
        if self.telegram_enabled:
            telegram_msg = f"""
🔴 <b>CAPTCHA ALGILANDI!</b>

⚠️ Manuel müdahale gerekli
🔗 <b>URL:</b> {form_url[:50]}...

Lütfen tarayıcıda CAPTCHA'yı çözün.
            """.strip()
            self.send_telegram_message(telegram_msg)
        
        # Also log loudly
        logger.critical(f"🔴 CAPTCHA DETECTED: {form_url}")
    
    def notify_whatsapp_message(self, message_text: str, form_count: int) -> None:
        """
        Send notification about new WhatsApp message with forms.
        
        Args:
            message_text: Message text
            form_count: Number of form links found
        """
        title = f"📱 Yeni Form Linki ({form_count})"
        message = message_text[:100]
        
        self.send_desktop_notification(title, message, timeout=8)
    
    def notify_daily_summary(
        self,
        total: int,
        successful: int,
        failed: int,
        captcha_count: int
    ) -> None:
        """
        Send daily summary notification.
        
        Args:
            total: Total forms processed
            successful: Successful submissions
            failed: Failed submissions
            captcha_count: CAPTCHA encounters
        """
        if self.telegram_enabled:
            success_rate = (successful / total * 100) if total > 0 else 0
            
            telegram_msg = f"""
📊 <b>Günlük Rapor</b>

📝 <b>Toplam Form:</b> {total}
✅ <b>Başarılı:</b> {successful} ({success_rate:.1f}%)
❌ <b>Başarısız:</b> {failed}
🔴 <b>CAPTCHA:</b> {captcha_count}
            """.strip()
            
            self.send_telegram_message(telegram_msg)
