"""
Admin Routes Module.
Provides full system management: Analytics Dashboard, User Management, Password Resets, Soft-Delete Restorations, Category Management, Post Control, and Audit Trail.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import db
from models.user import User
from models.item import Item
from models.category import Category
from models.claim import ClaimRequest
from models.audit_log import AuditLog
from forms import UserManageForm, CategoryForm, AdminResetPasswordForm
from utils.decorators import role_required
from services.audit_service import AuditService

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    """Admin Analytics Dashboard: Display metric cards and chart placeholders."""
    total_users = User.query.filter_by(is_deleted=False).count()
    active_users = User.query.filter_by(is_deleted=False, is_active=True).count()
    total_claims = ClaimRequest.query.count()

    total_lost = Item.query.filter_by(is_deleted=False, item_type='lost').count()
    total_found = Item.query.filter_by(is_deleted=False, item_type='found').count()

    status_counts = {}
    for status in Item.STATUSES:
        status_counts[status] = Item.query.filter_by(is_deleted=False, status=status).count()

    pending_reviews = status_counts.get(Item.STATUS_PENDING, 0) + status_counts.get(Item.STATUS_UNDER_REVIEW, 0)

    categories = Category.query.filter_by(is_deleted=False).all()
    category_data = []
    for cat in categories:
        count = Item.query.filter_by(category_id=cat.id, is_deleted=False).count()
        category_data.append({'name': cat.name, 'count': count})

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        active_users=active_users,
        total_claims=total_claims,
        total_lost=total_lost,
        total_found=total_found,
        status_counts=status_counts,
        pending_reviews=pending_reviews,
        category_data=category_data
    )

@admin_bp.route('/users', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_users():
    """User Management: Create, edit roles, suspend, soft-delete, and restore users."""
    form = UserManageForm()
    
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()

        existing = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing:
            flash('A user with that username or email already exists.', 'danger')
        else:
            new_user = User(
                username=username,
                email=email,
                role=form.role.data
            )
            if form.password.data:
                new_user.set_password(form.password.data)
            else:
                new_user.set_password('Password@123')

            db.session.add(new_user)
            db.session.commit()

            AuditService.log('ADMIN_CREATED_USER', target_type='User', target_id=new_user.id, details=f"Role: {new_user.role}")
            flash(f"User '{new_user.username}' created with role '{new_user.role}'.", 'success')
            return redirect(url_for('admin.manage_users'))

    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', form=form, users=users)

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@role_required('admin')
def admin_reset_user_password(user_id):
    """Admin resets password for any user."""
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password', '').strip()

    if not new_password or len(new_password) < 6:
        flash('Password must be at least 6 characters long.', 'danger')
        return redirect(url_for('admin.manage_users'))

    user.set_password(new_password)
    db.session.commit()

    AuditService.log('ADMIN_RESET_USER_PASSWORD', target_type='User', target_id=user.id, details=f"Reset password for {user.username}")
    flash(f"Password for user '{user.username}' has been reset by Admin.", 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@role_required('admin')
def toggle_user_status(user_id):
    """Suspend or activate user account."""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot suspend your own admin account.', 'danger')
        return redirect(url_for('admin.manage_users'))

    user.is_active = not user.is_active
    db.session.commit()

    action = 'ACTIVATED' if user.is_active else 'SUSPENDED'
    AuditService.log(f'ADMIN_{action}_USER', target_type='User', target_id=user.id)
    flash(f"User '{user.username}' account has been {action.lower()}.", 'info')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/change-role', methods=['POST'])
@login_required
@role_required('admin')
def change_user_role(user_id):
    """Change user role ('user', 'head', 'admin')."""
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')

    if user.id == current_user.id and new_role != 'admin':
        flash('You cannot demote your own admin account.', 'danger')
        return redirect(url_for('admin.manage_users'))

    if new_role in ['user', 'head', 'admin']:
        old_role = user.role
        user.role = new_role
        db.session.commit()

        AuditService.log('ADMIN_CHANGED_ROLE', target_type='User', target_id=user.id, details=f"From {old_role} to {new_role}")
        flash(f"User '{user.username}' role changed to '{new_role}'.", 'success')

    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/soft-delete', methods=['POST'])
@login_required
@role_required('admin')
def soft_delete_user(user_id):
    """Soft delete a user."""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own admin account.', 'danger')
        return redirect(url_for('admin.manage_users'))

    user.is_deleted = True
    db.session.commit()

    AuditService.log('ADMIN_SOFT_DELETED_USER', target_type='User', target_id=user.id)
    flash(f"User '{user.username}' soft-deleted.", 'warning')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/restore', methods=['POST'])
@login_required
@role_required('admin')
def restore_user(user_id):
    """Restore a soft-deleted user."""
    user = User.query.get_or_404(user_id)
    user.is_deleted = False
    db.session.commit()

    AuditService.log('ADMIN_RESTORED_USER', target_type='User', target_id=user.id)
    flash(f"User '{user.username}' restored.", 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/categories', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_categories():
    """Category CRUD management."""
    form = CategoryForm()
    if form.validate_on_submit():
        slug = form.name.data.strip().lower().replace(' ', '-')
        existing = Category.query.filter_by(slug=slug).first()
        if existing:
            flash('Category already exists.', 'danger')
        else:
            category = Category(
                name=form.name.data.strip(),
                slug=slug,
                description=form.description.data.strip() if form.description.data else None
            )
            db.session.add(category)
            db.session.commit()

            AuditService.log('ADMIN_CREATED_CATEGORY', target_type='Category', target_id=category.id)
            flash(f"Category '{category.name}' created.", 'success')
            return redirect(url_for('admin.manage_categories'))

    categories = Category.query.order_by(Category.name.asc()).all()
    return render_template('admin/categories.html', form=form, categories=categories)

@admin_bp.route('/categories/<int:cat_id>/soft-delete', methods=['POST'])
@login_required
@role_required('admin')
def soft_delete_category(cat_id):
    """Soft delete category."""
    cat = Category.query.get_or_404(cat_id)
    cat.is_deleted = True
    db.session.commit()

    AuditService.log('ADMIN_SOFT_DELETED_CATEGORY', target_type='Category', target_id=cat.id)
    flash(f"Category '{cat.name}' soft-deleted.", 'warning')
    return redirect(url_for('admin.manage_categories'))

@admin_bp.route('/categories/<int:cat_id>/restore', methods=['POST'])
@login_required
@role_required('admin')
def restore_category(cat_id):
    """Restore soft-deleted category."""
    cat = Category.query.get_or_404(cat_id)
    cat.is_deleted = False
    db.session.commit()

    AuditService.log('ADMIN_RESTORED_CATEGORY', target_type='Category', target_id=cat.id)
    flash(f"Category '{cat.name}' restored.", 'success')
    return redirect(url_for('admin.manage_categories'))

@admin_bp.route('/posts', methods=['GET'])
@login_required
@role_required('admin')
def manage_posts():
    """System-wide post management (including soft-deleted posts)."""
    show_deleted = request.args.get('show_deleted', '0') == '1'
    status_filter = request.args.get('status', '').strip()

    query = Item.query
    if not show_deleted:
        query = query.filter(Item.is_deleted == False)

    if status_filter in Item.STATUSES:
        query = query.filter(Item.status == status_filter)

    items = query.order_by(Item.created_at.desc()).all()
    return render_template('admin/posts.html', items=items, show_deleted=show_deleted, status_filter=status_filter, statuses=Item.STATUSES)

@admin_bp.route('/posts/<int:item_id>/soft-delete', methods=['POST'])
@login_required
@role_required('admin')
def soft_delete_post(item_id):
    """Soft-delete any post."""
    item = Item.query.get_or_404(item_id)
    item.is_deleted = True
    db.session.commit()

    AuditService.log('ADMIN_SOFT_DELETED_POST', target_type='Item', target_id=item.id)
    flash(f"Post #{item.id} ('{item.title}') soft-deleted.", 'warning')
    return redirect(url_for('admin.manage_posts'))

@admin_bp.route('/posts/<int:item_id>/restore', methods=['POST'])
@login_required
@role_required('admin')
def restore_post(item_id):
    """Restore soft-deleted post."""
    item = Item.query.get_or_404(item_id)
    item.is_deleted = False
    db.session.commit()

    AuditService.log('ADMIN_RESTORED_POST', target_type='Item', target_id=item.id)
    flash(f"Post #{item.id} restored.", 'success')
    return redirect(url_for('admin.manage_posts'))

@admin_bp.route('/audit-logs')
@login_required
@role_required('admin')
def audit_logs():
    """System audit trail viewer."""
    action_filter = request.args.get('action', '').strip()
    username_filter = request.args.get('username', '').strip()

    query = AuditLog.query

    if action_filter:
        query = query.filter(AuditLog.action.ilike(f'%{action_filter}%'))
    if username_filter:
        query = query.filter(AuditLog.username.ilike(f'%{username_filter}%'))

    logs = query.order_by(AuditLog.timestamp.desc()).limit(200).all()
    return render_template('admin/audit_logs.html', logs=logs, action_filter=action_filter, username_filter=username_filter)
