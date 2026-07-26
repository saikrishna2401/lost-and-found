"""
Audit Service Module.
Centralized logging interface for recording system activity and user audit trails.
"""
from flask_login import current_user
from models import db
from models.audit_log import AuditLog

class AuditService:

    @staticmethod
    def log(action, target_type=None, target_id=None, details=None, user=None):
        """
        Logs an event into the audit trail.
        Uses provided user or falls back to current_user.
        """
        actor = user or (current_user if current_user.is_authenticated else None)
        
        user_id = actor.id if actor else None
        username = actor.username if actor else 'SYSTEM'
        role = actor.role if actor else 'system'

        log_entry = AuditLog(
            user_id=user_id,
            username=username,
            role=role,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
