"""
User Model Module.
Defines user entity with Flask-Login integration, password security, role hierarchy, and soft-delete capabilities.
"""
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Role-based authorization: 'user', 'head', 'admin'
    role = db.Column(db.String(20), nullable=False, default='user')
    
    # Account status flags
    is_active = db.Column(db.Boolean, default=True, nullable=False) # False if suspended
    is_deleted = db.Column(db.Boolean, default=False, nullable=False) # True if soft-deleted
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    items = db.relationship('Item', backref='submitter', lazy=True, foreign_keys='Item.user_id')
    claims = db.relationship('ClaimRequest', backref='claimant', lazy=True, foreign_keys='ClaimRequest.user_id')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        """Hashes and stores password using Werkzeug security."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies candidate password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def is_head_or_admin(self):
        """Helper to check if user has elevated privileges."""
        return self.role in ['head', 'admin']

    def is_admin(self):
        """Helper to check if user is an Administrator."""
        return self.role == 'admin'

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
