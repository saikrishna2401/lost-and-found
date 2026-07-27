"""
Found Report Model Module.
Tracks reports submitted by users who have found a reported Lost Item.
"""
from datetime import datetime, timezone
from models import db

class FoundReport(db.Model):
    __tablename__ = 'found_reports'

    STATUS_PENDING = 'Pending'
    STATUS_APPROVED = 'Approved'
    STATUS_REJECTED = 'Rejected'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # The finder
    
    image_filename = db.Column(db.String(255), nullable=False) # Recent photo of found item
    description = db.Column(db.Text, nullable=False) # Where & when found
    phone_number = db.Column(db.String(30), nullable=False) # Finder's phone
    email = db.Column(db.String(120), nullable=False) # Finder's email
    
    status = db.Column(db.String(20), default=STATUS_PENDING, nullable=False, index=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    finder = db.relationship('User', foreign_keys=[user_id])
    reviewer = db.relationship('User', foreign_keys=[reviewed_by_id])

    def can_view_contact(self, current_user):
        """
        Determines whether current_user is authorized to view the finder's contact details (phone, email, photo, description).
        Allowed users:
        1. Lost Item owner (current_user.id == self.item.user_id) AND status == 'Approved'
        2. Finder who submitted the report (current_user.id == self.user_id)
        3. Head Reviewers and Admins (current_user.role in ['admin', 'head'])
        """
        if not current_user or not hasattr(current_user, 'is_authenticated') or not current_user.is_authenticated:
            return False
        if current_user.id == self.user_id or (hasattr(current_user, 'role') and current_user.role in ['admin', 'head']):
            return True
        if self.item and current_user.id == self.item.user_id and self.status == self.STATUS_APPROVED:
            return True
        return False

    @property
    def status_badge_class(self):
        """Returns Bootstrap CSS class for rendering status badges."""
        badge_map = {
            self.STATUS_PENDING: 'bg-warning text-dark',
            self.STATUS_APPROVED: 'bg-success text-white',
            self.STATUS_REJECTED: 'bg-danger text-white'
        }
        return badge_map.get(self.status, 'bg-secondary text-white')

    def __repr__(self):
        return f"<FoundReport {self.id} for Item {self.item_id} by Finder {self.user_id}>"
