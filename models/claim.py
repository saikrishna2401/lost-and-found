"""
Claim Request Model Module.
Tracks ownership claim requests submitted by users for found items.
"""
from datetime import datetime, timezone
from models import db

class ClaimRequest(db.Model):
    __tablename__ = 'claim_requests'

    STATUS_PENDING = 'Pending'
    STATUS_APPROVED = 'Approved'
    STATUS_REJECTED = 'Rejected'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    reason = db.Column(db.Text, nullable=False)
    description_proof = db.Column(db.Text, nullable=False) # Proof of ownership
    contact_info = db.Column(db.String(150), nullable=False)
    
    status = db.Column(db.String(20), default=STATUS_PENDING, nullable=False)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Reviewer relationship
    reviewer = db.relationship('User', foreign_keys=[reviewed_by_id])

    @property
    def status_badge_class(self):
        """Returns Bootstrap CSS class for rendering claim status badges."""
        badge_map = {
            self.STATUS_PENDING: 'bg-warning text-dark',
            self.STATUS_APPROVED: 'bg-success text-white',
            self.STATUS_REJECTED: 'bg-danger text-white'
        }
        return badge_map.get(self.status, 'bg-secondary text-white')

    def __repr__(self):
        return f"<ClaimRequest {self.id} for Item {self.item_id} by User {self.user_id}>"
