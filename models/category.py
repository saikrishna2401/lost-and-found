"""
Category Model Module.
Defines item categories for lost and found posts.
"""
from models import db

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    items = db.relationship('Item', backref='category', lazy=True)

    def __repr__(self):
        return f"<Category {self.name}>"
