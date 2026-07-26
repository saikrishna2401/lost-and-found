"""
Item Model Module.
Defines Lost and Found items, complete 7-stage status lifecycle, and soft-delete capabilities.
"""
from datetime import datetime, timezone
from models import db

class Item(db.Model):
    __tablename__ = 'items'

    # Valid status lifecycle values
    STATUS_PENDING = 'Pending'
    STATUS_UNDER_REVIEW = 'Under Review'
    STATUS_APPROVED = 'Approved'
    STATUS_REJECTED = 'Rejected'
    STATUS_CLAIMED = 'Claimed'
    STATUS_RETURNED = 'Returned'
    STATUS_ARCHIVED = 'Archived'

    STATUSES = [
        STATUS_PENDING,
        STATUS_UNDER_REVIEW,
        STATUS_APPROVED,
        STATUS_REJECTED,
        STATUS_CLAIMED,
        STATUS_RETURNED,
        STATUS_ARCHIVED
    ]

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, index=True)
    item_type = db.Column(db.String(10), nullable=False) # 'lost' or 'found'
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(150), nullable=False, index=True)
    date_event = db.Column(db.Date, nullable=False) # Date when item was lost or found
    image_filename = db.Column(db.String(255), nullable=True)

    # 7-stage lifecycle status
    status = db.Column(db.String(20), default=STATUS_PENDING, nullable=False, index=True)
    rejection_reason = db.Column(db.Text, nullable=True)

    # Foreign Keys & Flags
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    claims = db.relationship('ClaimRequest', backref='item', lazy=True, cascade="all, delete-orphan")

    @property
    def status_badge_class(self):
        """Returns Bootstrap CSS class for rendering status badges."""
        badge_map = {
            self.STATUS_PENDING: 'bg-warning text-dark',
            self.STATUS_UNDER_REVIEW: 'bg-info text-dark',
            self.STATUS_APPROVED: 'bg-success text-white',
            self.STATUS_REJECTED: 'bg-danger text-white',
            self.STATUS_CLAIMED: 'bg-primary text-white',
            self.STATUS_RETURNED: 'bg-teal text-white',
            self.STATUS_ARCHIVED: 'bg-secondary text-white'
        }
        return badge_map.get(self.status, 'bg-secondary text-white')

    def __repr__(self):
        return f"<Item {self.id}: {self.title} ({self.status})>"
