# Lost and Found Web Application

A full-stack, enterprise-grade Lost and Found web application built using **Python Flask**, **SQLAlchemy**, **SQLite** (PostgreSQL-ready), **Bootstrap 5**, **Flask-WTF** (CSRF protection), and **Flask-Login**.

---

## Key Features

1. **Role-Based Access Control (RBAC)**:
   - **Normal User**: Register, report lost/found items with image uploads, edit *only* their own pending posts, view approved public posts, search/filter, submit ownership claims, receive in-app notifications.
   - **Head Reviewer**: Moderation queue, approve or reject pending items with mandatory rejection reasons, review ownership claims, update item lifecycle statuses (`Under Review`, `Approved`, `Rejected`, `Claimed`, `Returned`, `Archived`).
   - **Administrator**: Full system access, 10-metric analytics dashboard with category breakdown, user management (create, change role, suspend/activate, soft-delete, restore, reset any user password), soft-delete & restore posts, category manager, system-wide Audit Trail viewer.

2. **7-Stage Item Status Lifecycle**:
   - `Pending` ➔ `Under Review` ➔ `Approved` / `Rejected` ➔ `Claimed` ➔ `Returned` ➔ `Archived`.
   - Color-coded status badges for instant status visibility.

3. **Ownership Claim Workflow**:
   - Users submit a claim request with ownership proof (serial #, unique features, receipt info) and contact details.
   - Moderation heads review claims and transition items to `Claimed`, `Returned`, and `Archived`.

4. **Rule-Based Smart Matching Engine**:
   - Automatically cross-references new submissions with opposite item types (`lost` vs `found`) by Title keyword similarity, Category, and Location.
   - Dispatches in-app notifications to submitters when matches are detected.

5. **Soft Delete & Audit Logs**:
   - Soft-delete flags (`is_deleted`) preserve records for restoration.
   - Centralized `AuditLog` captures user registration, post submissions, approvals, rejections, role changes, and administrative actions.

6. **Security & Production Readiness**:
   - Password hashing with Werkzeug security (`generate_password_hash`).
   - CSRF protection across all forms (`Flask-WTF`).
   - File upload security with extensions check (`.png`, `.jpg`, `.jpeg`, `.webp`), secure filename generation, and 5MB size limit.
   - PostgreSQL URI converter (`postgres://` ➔ `postgresql://`).
   - Modular `StorageService` interface allowing seamless upgrade to Cloudinary/AWS S3.

---

## Directory Structure

```
lost_and_found/
├── app.py                      # Application Factory & Routing Setup
├── config.py                   # Config & DB URL Converter
├── seed.py                     # CLI Script to seed default accounts & categories
├── forms.py                    # Flask-WTF validation forms
├── requirements.txt            # Python dependencies
├── Procfile                    # Render WSGI launcher
├── render.yaml                 # Render Blueprint configuration
├── instance/                   # SQLite database location
├── models/                     # SQLAlchemy Models (User, Item, Category, Claim, AuditLog, Notification)
├── routes/                     # Flask Blueprints (auth, main, user, head, admin)
├── services/                   # Business Services (StorageService, MatchingService, NotificationService, AuditService)
├── utils/                      # Decorators & Helpers (@role_required)
├── static/                     # CSS, JS, Uploaded image files
└── templates/                  # Jinja2 Templates (HTML5 + Bootstrap 5)
```

---

## Local Development Setup

### 1. Prerequisites
- Python 3.9+
- `pip` (Python package manager)

### 2. Installation Steps

1. Clone or extract the project repository.
2. Navigate to the project root directory:
   ```bash
   cd "lost and found"
   ```
3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Initialize the database schema and seed default data:
   ```bash
   python seed.py
   ```
5. Start the local Flask development server:
   ```bash
   python app.py
   ```
6. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

---

## Default Login Credentials

Running `python seed.py` automatically generates three default accounts for testing:

| Role | Username | Email | Password |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin@example.com` | `Admin@123` |
| **Head Reviewer** | `head` | `head@example.com` | `Head@123` |
| **Normal User** | `john_doe` | `user@example.com` | `User@123` |
