"""
Authorization Decorators Module.
Provides custom role-based route guard decorators (@role_required).
"""
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def role_required(*roles):
    """
    Decorator to restrict route access to specific roles ('user', 'head', 'admin').
    If the current user's role is not in the allowed roles list, aborts with HTTP 403.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if not current_user.is_active or current_user.is_deleted:
                flash('Your account has been suspended or deactivated.', 'danger')
                return redirect(url_for('auth.logout'))

            if current_user.role not in roles:
                abort(403) # Forbidden

            return f(*args, **kwargs)
        return decorated_function
    return decorator
