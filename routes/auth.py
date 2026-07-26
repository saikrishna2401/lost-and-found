"""
Authentication Routes Module.
Handles registration, login, logout, profile management, and password resets.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from models import db
from models.user import User
from forms import RegisterForm, LoginForm, ChangePasswordForm, ForgotPasswordForm, ResetPasswordForm
from services.audit_service import AuditService

auth_bp = Blueprint('auth', __name__)

def get_serializer():
    """Generates timed URL serializer for password reset tokens."""
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User Registration Route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            role='user'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        AuditService.log('USER_REGISTERED', target_type='User', target_id=user.id, details=f"Username: {user.username}", user=user)

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User Login Route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.username_or_email.data.strip()
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        if user and user.check_password(form.password.data):
            if user.is_deleted:
                flash('Your account has been deleted. Please contact an administrator.', 'danger')
                return render_template('auth/login.html', form=form)
            
            if not user.is_active:
                flash('Your account has been suspended. Please contact support.', 'warning')
                return render_template('auth/login.html', form=form)

            login_user(user, remember=form.remember.data)
            AuditService.log('USER_LOGIN', target_type='User', target_id=user.id, user=user)
            
            flash(f'Welcome back, {user.username}!', 'success')
            
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            elif user.is_head_or_admin():
                return redirect(url_for('head.dashboard'))
            else:
                return redirect(url_for('user.dashboard'))

        flash('Invalid username/email or password.', 'danger')

    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """User Logout Route."""
    AuditService.log('USER_LOGOUT', target_type='User', target_id=current_user.id)
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User Profile & Password Change."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()

            AuditService.log('USER_CHANGED_PASSWORD', target_type='User', target_id=current_user.id)
            flash('Your password has been updated successfully.', 'success')
            return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', form=form)

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request Password Reset Link."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        identifier = form.email_or_username.data.strip()
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        if user and not user.is_deleted and user.is_active:
            s = get_serializer()
            token = s.dumps(user.id, salt='password-reset-salt')
            reset_url = url_for('auth.reset_password', token=token, _external=True)

            AuditService.log('FORGOT_PASSWORD_REQUESTED', target_type='User', target_id=user.id, user=user)

            flash(f"Password reset link generated! In production, this link is emailed. Testing Reset Link: {reset_url}", 'info')
            return redirect(url_for('auth.login'))

        flash('If an active account exists for that email/username, a reset link was generated.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset Password via Secure Token."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    s = get_serializer()
    try:
        user_id = s.loads(token, salt='password-reset-salt', max_age=3600) # Valid for 1 hour
    except (SignatureExpired, BadSignature):
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    user = db.session.get(User, user_id)
    if not user or user.is_deleted or not user.is_active:
        flash('User account unavailable for password reset.', 'danger')
        return redirect(url_for('auth.login'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        db.session.commit()

        AuditService.log('PASSWORD_RESET_COMPLETED', target_type='User', target_id=user.id, user=user)
        flash('Your password has been reset successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form, token=token)
