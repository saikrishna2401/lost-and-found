"""
Notification Service Module.
Handles in-app notification dispatching and provides hooks for email integration.
"""
from models import db
from models.notification import Notification

class NotificationService:

    @staticmethod
    def send_notification(user_id, title, message, link=None):
        """
        Creates an in-app notification for the target user.
        Also acts as a hook for future email notifications (SendGrid/SMTP).
        """
        if not user_id:
            return None

        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            link=link
        )
        db.session.add(notification)
        db.session.commit()

        # Future Extension Hook: Send Email Notification
        NotificationService._send_email_hook(user_id, title, message)

        return notification

    @staticmethod
    def _send_email_hook(user_id, title, message):
        """
        Placeholder hook for sending external email notifications.
        Can be integrated with Flask-Mail or SendGrid API in future releases.
        """
        # Intentional pass for local dev & pluggable architecture
        pass
