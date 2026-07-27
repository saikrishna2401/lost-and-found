"""
Flask Application Factory Module.
Initializes extensions, registers blueprints, context processors, error handlers, and security headers.
"""
import os
from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, current_user

from config import Config
from models import db
from models.user import User
from models.notification import Notification

from routes.auth import auth_bp
from routes.main import main_bp
from routes.user import user_bp
from routes.head import head_bp
from routes.admin import admin_bp

from utils.helpers import get_item_image_url

def create_app(config_class=Config):
    """Factory function to initialize Flask application instance."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    CSRFProtect(app)

    # Auto-create database tables & auto-migrate missing columns on startup
    with app.app_context():
        try:
            db.create_all()
            # Lightweight schema auto-migration for newly added columns (e.g. phone_number)
            try:
                from sqlalchemy import text
                db_uri = str(app.config.get('SQLALCHEMY_DATABASE_URI', ''))
                if 'postgresql' in db_uri:
                    db.session.execute(text("ALTER TABLE items ADD COLUMN IF NOT EXISTS phone_number VARCHAR(30);"))
                else:
                    # SQLite auto-migration logic
                    try:
                        db.session.execute(text("ALTER TABLE items ADD COLUMN phone_number VARCHAR(30);"))
                    except Exception:
                        pass # Column already exists in SQLite
                db.session.commit()
            except Exception as migration_err:
                db.session.rollback()
                print(f"Schema Auto-Migration Note: {migration_err}")
        except Exception as e:
            print(f"Cloud Database Initialization Warning: {e}")

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            user = db.session.get(User, int(user_id))
            if user and not user.is_deleted and user.is_active:
                return user
        except Exception:
            db.session.rollback()
        return None

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(head_bp)
    app.register_blueprint(admin_bp)

    # Register Global Template Functions & Context Processors
    app.jinja_env.globals.update(get_item_image_url=get_item_image_url)

    @app.context_processor
    def inject_globals():
        """Inject unread notification count and global helpers into all Jinja templates."""
        unread_count = 0
        if current_user.is_authenticated:
            try:
                unread_count = Notification.query.filter_by(
                    user_id=current_user.id,
                    is_read=False
                ).count()
            except Exception:
                db.session.rollback()
        return dict(unread_notification_count=unread_count)

    # Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app

# WSGI entrypoint for Gunicorn and Flask CLI
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
