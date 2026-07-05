"""Notification Service for the Mosque Platform."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class NotificationProvider(ABC):
    """Abstract base class for all notification channels."""

    @abstractmethod
    def send_whatsapp(self, recipient: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        pass

    @abstractmethod
    def send_sms(self, recipient: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        pass

    @abstractmethod
    def send_email(self, recipient: str, subject: str, body: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        pass

    @abstractmethod
    def send_push(self, recipient_token: str, title: str, body: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        pass

    @abstractmethod
    def send_in_app(self, user_id: int, title: str, body: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        pass


class DummyNotificationProvider(NotificationProvider):
    """Dummy notification provider that logs actions to console for development."""

    def send_whatsapp(self, recipient: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        logger.info(f"DUMMY WHATSAPP to {recipient}: {message} (meta: {metadata})")
        return True

    def send_sms(self, recipient: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        print("\n" + "="*60)
        print("📱 DUMMY NOTIFICATION PROVIDER - SMS SENT")
        print("="*60)
        print(f"To:      {recipient}")
        print(f"Message: {message}")
        print("="*60 + "\n")
        logger.info(f"DUMMY SMS to {recipient}: {message} (meta: {metadata})")
        return True

    def send_email(self, recipient: str, subject: str, body: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        logger.info(f"DUMMY EMAIL to {recipient} | Subject: {subject} | Body: {body} (meta: {metadata})")
        return True

    def send_push(self, recipient_token: str, title: str, body: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        logger.info(f"DUMMY PUSH to token {recipient_token} | Title: {title} | Body: {body} (meta: {metadata})")
        return True

    def send_in_app(self, user_id: int, title: str, body: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        logger.info(f"DUMMY IN-APP to user {user_id} | Title: {title} | Body: {body} (meta: {metadata})")
        return True


class NotificationService:
    """
    Central service for sending notifications.
    Supports WhatsApp, SMS, Email, Push, and In-App channels.
    """

    def __init__(self, provider: Optional[NotificationProvider] = None):
        self.provider = provider or DummyNotificationProvider()

    def send_whatsapp(self, recipient: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        try:
            return self.provider.send_whatsapp(recipient, message, metadata)
        except Exception as e:
            logger.error(f"Failed to send WhatsApp to {recipient}: {str(e)}")
            return False

    def send_sms(self, recipient: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        try:
            # Maintain backward compatibility with older signature
            if hasattr(self.provider, "send_sms"):
                return self.provider.send_sms(recipient, message, metadata)
            return False
        except Exception as e:
            logger.error(f"Failed to send SMS to {recipient}: {str(e)}")
            return False

    def send_email(self, recipient: str, subject: str, body: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        try:
            # Maintain backward compatibility with older signature
            if hasattr(self.provider, "send_email"):
                return self.provider.send_email(recipient, subject, body, metadata)
            return False
        except Exception as e:
            logger.error(f"Failed to send Email to {recipient}: {str(e)}")
            return False

    def send_push(self, recipient_token: str, title: str, body: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        try:
            return self.provider.send_push(recipient_token, title, body, metadata)
        except Exception as e:
            logger.error(f"Failed to send Push to token {recipient_token}: {str(e)}")
            return False

    def send_in_app(self, user_id: int, title: str, body: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        try:
            return self.provider.send_in_app(user_id, title, body, metadata)
        except Exception as e:
            logger.error(f"Failed to send In-App to user {user_id}: {str(e)}")
            return False


# Global instance
notification_service = NotificationService()
