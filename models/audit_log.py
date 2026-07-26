"""
Audit Log Model Module.
Stores system-wide administrative, moderation, and user actions for auditing.
"""
from datetime import datetime, timezone
from models import db

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    username = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    
    action = db.Column(db.String(100), nullable=False, index=True) # e.g. "USER_SUBMITTED_ITEM", "HEAD_APPROVED_POST"
    target_type = db.Column(db.String(50), nullable=True) # e.g. "Item", "User", "ClaimRequest"
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def __repr__(self):
        return f"<AuditLog {self.id}: {self.username} performed {self.action}>"
