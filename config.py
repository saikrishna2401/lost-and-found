import os
from datetime import timedelta
from urllib.parse import unquote, quote

# Load .env file automatically if present
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip("'").strip('"')
                if key and value and key not in os.environ:
                    os.environ[key] = value

class Config:
    """
    Application Configuration Class.
    Handles environment variables for development and production (e.g. Supabase, Render, PostgreSQL).
    """
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-secret-key-lost-and-found-2026')

    # Supabase Credentials
    SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://cvdmqgaauhnysytojwyh.supabase.co')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'sb_publishable_UAzzySBLlCA5LapdGh04fA_AYvvs6fc')

    # Base directory of the project
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Database configuration: supports SQLite locally and PostgreSQL on Supabase/Render
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # Normalize postgres:// to postgresql://
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)

        # Handle passwords containing special characters (like '@')
        if db_url.startswith('postgresql://') and '://' in db_url:
            scheme, body = db_url.split('://', 1)
            if '@' in body:
                # The last '@' separates user:password from host:port/dbname
                userpass, host_db = body.rsplit('@', 1)
                if ':' in userpass:
                    username, password = userpass.split(':', 1)
                    decoded_pass = unquote(password)
                    encoded_pass = quote(decoded_pass, safe='')
                    db_url = f"postgresql://{username}:{encoded_pass}@{host_db}"

        SQLALCHEMY_DATABASE_URI = db_url
    else:
        # Local SQLite database path inside instance folder
        instance_dir = os.path.join(BASE_DIR, 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(instance_dir, 'lost_and_found.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload configuration
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # Maximum file upload size: 5 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Security & Session Settings
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
