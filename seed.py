"""
Database Seed Script.
Populates SQLite / PostgreSQL database with initial tables, default categories, default user roles, and demo items.
"""
from datetime import date, timedelta
from app import app
from models import db
from models.user import User
from models.category import Category
from models.item import Item
from services.audit_service import AuditService

def seed_database():
    with app.app_context():
        print("Creating database schema...")
        db.create_all()

        # Seed Default Categories
        default_categories = [
            ("Electronics", "Phones, Laptops, Headphones, Chargers"),
            ("Keys & Locks", "House keys, Car keys, Keychains"),
            ("Wallets & Purses", "Wallets, Purses, Handbags, Money clips"),
            ("Documents & Cards", "ID Cards, Passports, Driver's licenses, Credit cards"),
            ("Clothing & Accessories", "Jackets, Hats, Scarves, Glasses"),
            ("Bags & Backpacks", "School backpacks, Luggage, Gym bags"),
            ("Books & Stationery", "Notebooks, Textbooks, Pens"),
            ("Jewelry & Watches", "Rings, Necklaces, Watches, Bracelets"),
            ("Pets & Animals", "Dogs, Cats, Collars, Leashes"),
            ("Others", "Miscellaneous items")
        ]

        print("Seeding categories...")
        cat_objects = {}
        for name, desc in default_categories:
            slug = name.lower().replace(' & ', '-').replace(' ', '-')
            cat = Category.query.filter_by(slug=slug).first()
            if not cat:
                cat = Category(name=name, slug=slug, description=desc)
                db.session.add(cat)
            cat_objects[name] = cat

        db.session.commit()

        # Seed Default Accounts
        print("Seeding default user accounts...")

        # 1. Admin Account
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', role='admin')
            admin.set_password('Admin@123')
            db.session.add(admin)

        # 2. Head Reviewer Account
        head = User.query.filter_by(username='head').first()
        if not head:
            head = User(username='head', email='head@example.com', role='head')
            head.set_password('Head@123')
            db.session.add(head)

        # 3. Normal User Account
        user = User.query.filter_by(username='john_doe').first()
        if not user:
            user = User(username='john_doe', email='user@example.com', role='user')
            user.set_password('User@123')
            db.session.add(user)

        db.session.commit()

        # Seed Demo Items if table is empty
        if Item.query.count() == 0:
            print("Seeding sample Lost & Found items...")
            
            item1 = Item(
                title="Black iPhone 15 Pro",
                item_type="found",
                category_id=cat_objects["Electronics"].id,
                description="Found a black iPhone 15 Pro in a clear silicone case near the library main staircase.",
                location="Central Library",
                date_event=date.today() - timedelta(days=2),
                status=Item.STATUS_APPROVED,
                user_id=user.id
            )

            item2 = Item(
                title="Toyota Car Key with Leather Fob",
                item_type="lost",
                category_id=cat_objects["Keys & Locks"].id,
                description="Lost my car key with a brown leather fob and house key attached.",
                location="Parking Lot B",
                date_event=date.today() - timedelta(days=1),
                status=Item.STATUS_APPROVED,
                user_id=user.id
            )

            item3 = Item(
                title="Brown Leather Wallet with Cards",
                item_type="found",
                category_id=cat_objects["Wallets & Purses"].id,
                description="Found brown leather wallet containing student ID and public transit card.",
                location="Student Cafeteria",
                date_event=date.today(),
                status=Item.STATUS_PENDING,
                user_id=user.id
            )

            db.session.add_all([item1, item2, item3])
            db.session.commit()

            # Audit log
            AuditService.log('SYSTEM_SEED_COMPLETED', details="Initial database seed executed successfully.", user=admin)

        print("\n==============================================")
        print("Database Seed Completed Successfully!")
        print("Default Accounts Created:")
        print(" - Admin: admin@example.com / Admin@123")
        print(" - Head Reviewer: head@example.com / Head@123")
        print(" - Normal User: user@example.com / User@123")
        print("==============================================\n")

if __name__ == '__main__':
    seed_database()
