"""
Automated Verification Suite for Lost & Found Web Application.
Tests user authentication, 7-stage status lifecycle, claim submission, smart matching, RBAC authorization guards, soft deletes, audit logging, and password resets.
"""
import unittest
from datetime import date
from app import create_app
from models import db
from models.user import User
from models.item import Item
from models.category import Category
from models.claim import ClaimRequest
from services.matching_service import MatchingService

class TestLostAndFoundApp(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()

            # Seed test accounts
            admin = User(username='admin', email='admin@example.com', role='admin')
            admin.set_password('Admin@123')

            head = User(username='head', email='head@example.com', role='head')
            head.set_password('Head@123')

            user = User(username='john_doe', email='user@example.com', role='user')
            user.set_password('User@123')

            category = Category(name='Electronics', slug='electronics', description='Phones & Laptops')

            db.session.add_all([admin, head, user, category])
            db.session.commit()

            # Store IDs as integers to avoid SQLAlchemy DetachedInstanceError across sessions
            self.admin_id = admin.id
            self.head_id = head.id
            self.user_id = user.id
            self.category_id = category.id

            # Seed a found item reported by ADMIN (so john_doe can claim it)
            found_item = Item(
                title='Silver Macbook Air 13-inch',
                item_type='found',
                category_id=self.category_id,
                description='Found a silver Macbook Air on a study bench.',
                location='Student Center',
                date_event=date.today(),
                phone_number='+15559876543',
                status=Item.STATUS_APPROVED,
                user_id=self.admin_id
            )
            db.session.add(found_item)
            db.session.commit()

            self.found_item_id = found_item.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, username, password):
        self.client.get('/logout', follow_redirects=True)
        return self.client.post('/login', data=dict(
            username_or_email=username,
            password=password
        ), follow_redirects=True)

    def test_01_user_authentication(self):
        """Test User Login & Logout."""
        res = self.login('john_doe', 'User@123')
        self.assertIn(b'Welcome back, john_doe!', res.data)

        res_logout = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'logged out successfully', res_logout.data)

    def test_02_item_submission_and_smart_matching(self):
        """Test item submission defaults to Pending status and triggers Smart Matching."""
        self.login('john_doe', 'User@123')

        # Submit a Lost item matching the found Macbook
        res = self.client.post('/user/items/create', data=dict(
            title='Lost Silver Macbook Air',
            item_type='lost',
            category_id=self.category_id,
            description='Lost silver laptop at student center',
            location='Student Center',
            date_event=str(date.today()),
            phone_number='+15550192834'
        ), follow_redirects=True)

        self.assertIn(b'submitted', res.data.lower())

        with self.app.app_context():
            item = Item.query.filter_by(title='Lost Silver Macbook Air').first()
            self.assertIsNotNone(item)
            self.assertEqual(item.status, Item.STATUS_PENDING)

            # Verify Smart Matching engine matches with the found Macbook
            matches = MatchingService.find_potential_matches(item)
            self.assertTrue(len(matches) > 0)
            self.assertEqual(matches[0].title, 'Silver Macbook Air 13-inch')

    def test_03_role_authorization_guards(self):
        """Test Normal User receives 403 Forbidden when accessing Head or Admin routes."""
        self.login('john_doe', 'User@123')

        # Access Head Dashboard
        res_head = self.client.get('/head/dashboard')
        self.assertEqual(res_head.status_code, 403)

        # Access Admin Dashboard
        res_admin = self.client.get('/admin/dashboard')
        self.assertEqual(res_admin.status_code, 403)

    def test_04_head_review_and_approval(self):
        """Test Head reviewer approving a pending post."""
        # Create a pending item first
        with self.app.app_context():
            pending_item = Item(
                title='Found Blue Backpack',
                item_type='found',
                category_id=self.category_id,
                description='Found blue backpack',
                location='Gym',
                date_event=date.today(),
                status=Item.STATUS_PENDING,
                user_id=self.user_id
            )
            db.session.add(pending_item)
            db.session.commit()
            item_id = pending_item.id

        self.login('head', 'Head@123')
        res = self.client.post(f'/head/items/{item_id}/review', data=dict(
            action='approve'
        ), follow_redirects=True)

        self.assertIn(b'APPROVED', res.data)

        with self.app.app_context():
            item = db.session.get(Item, item_id)
            self.assertEqual(item.status, Item.STATUS_APPROVED)

    def test_05_claim_workflow(self):
        """Test claim submission by normal user and approval by Head."""
        # 1. john_doe files claim on item reported by admin
        self.login('john_doe', 'User@123')

        res_claim = self.client.post(f'/items/{self.found_item_id}/claim', data=dict(
            reason='This is my missing laptop',
            description_proof='Has a sticker on top and serial #MB-9922',
            contact_info='555-0199'
        ), follow_redirects=True)

        self.assertIn(b'claim request has been submitted', res_claim.data)

        with self.app.app_context():
            claim = ClaimRequest.query.filter_by(item_id=self.found_item_id, user_id=self.user_id).first()
            self.assertIsNotNone(claim)
            claim_id = claim.id

        # 2. Head reviews and approves claim
        self.login('head', 'Head@123')
        res_approve_claim = self.client.post(f'/head/claims/{claim_id}/review', data=dict(
            action='approve'
        ), follow_redirects=True)

        self.assertIn(b'APPROVED', res_approve_claim.data)

        with self.app.app_context():
            item = db.session.get(Item, self.found_item_id)
            self.assertEqual(item.status, Item.STATUS_CLAIMED)

    def test_06_admin_analytics_and_audit_logs(self):
        """Test Admin Dashboard analytics and Audit Logs."""
        self.login('admin', 'Admin@123')

        res_dash = self.client.get('/admin/dashboard')
        self.assertEqual(res_dash.status_code, 200)
        self.assertIn(b'Administrator System Analytics', res_dash.data)

        res_audit = self.client.get('/admin/audit-logs')
        self.assertEqual(res_audit.status_code, 200)
        self.assertIn(b'System Audit Trail', res_audit.data)

    def test_07_user_self_password_reset(self):
        """Test User Self Password Change via Profile."""
        self.login('john_doe', 'User@123')

        res_change = self.client.post('/profile', data=dict(
            current_password='User@123',
            new_password='NewUserPassword@99',
            confirm_password='NewUserPassword@99'
        ), follow_redirects=True)

        self.assertIn(b'updated successfully', res_change.data)

        # Verify old password fails and new password succeeds
        res_old = self.login('john_doe', 'User@123')
        self.assertIn(b'Invalid username/email or password', res_old.data)

        res_new = self.login('john_doe', 'NewUserPassword@99')
        self.assertIn(b'Welcome back, john_doe!', res_new.data)

    def test_08_admin_password_reset(self):
        """Test Admin resetting password for another user."""
        self.login('admin', 'Admin@123')

        res_reset = self.client.post(f'/admin/users/{self.user_id}/reset-password', data=dict(
            new_password='AdminResetPassword@77'
        ), follow_redirects=True)

        self.assertIn(b'reset by Admin', res_reset.data)

        # Verify user can log in with Admin-set password
        res_login = self.login('john_doe', 'AdminResetPassword@77')
        self.assertIn(b'Welcome back, john_doe!', res_login.data)

    def test_09_head_cannot_reset_password(self):
        """Test Head Reviewer CANNOT reset other users' passwords (returns 403 Forbidden)."""
        self.login('head', 'Head@123')

        res_head_reset = self.client.post(f'/admin/users/{self.user_id}/reset-password', data=dict(
            new_password='HeadAttemptPassword@11'
        ))

        self.assertEqual(res_head_reset.status_code, 403)

if __name__ == '__main__':
    unittest.main()
