"""
Main Public Routes Module.
Handles public landing page, approved items gallery search with pagination, item detail view, claims submission, and user notifications.
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user, login_required
from models import db
from models.item import Item
from models.category import Category
from models.claim import ClaimRequest
from models.notification import Notification
from forms import ClaimForm
from services.audit_service import AuditService
from services.notification_service import NotificationService

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    Public Lost and Found Gallery & Search Feed.
    Supports filtering by keyword, category, location, date range, item type, and status with pagination (10 items/page).
    """
    page = request.args.get('page', 1, type=int)
    query_param = request.args.get('q', '').strip()
    category_id = request.args.get('category_id', type=int)
    location_param = request.args.get('location', '').strip()
    item_type = request.args.get('item_type', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    status_param = request.args.get('status', '').strip()

    # Base query: non-deleted items
    query = Item.query.filter(Item.is_deleted == False)

    # Public users only see Approved posts by default; Heads/Admins can see non-approved if requested
    if current_user.is_authenticated and current_user.is_head_or_admin() and status_param:
        query = query.filter(Item.status == status_param)
    else:
        query = query.filter(Item.status == Item.STATUS_APPROVED)

    # Apply filters
    if query_param:
        query = query.filter(
            (Item.title.ilike(f'%{query_param}%')) | 
            (Item.description.ilike(f'%{query_param}%')) |
            (Item.location.ilike(f'%{query_param}%'))
        )

    if category_id:
        query = query.filter(Item.category_id == category_id)

    if location_param:
        query = query.filter(Item.location.ilike(f'%{location_param}%'))

    if item_type in ['lost', 'found']:
        query = query.filter(Item.item_type == item_type)

    if date_from:
        try:
            d_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Item.date_event >= d_from)
        except ValueError:
            pass

    if date_to:
        try:
            d_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Item.date_event <= d_to)
        except ValueError:
            pass

    # Order newest first
    query = query.order_by(Item.created_at.desc())

    # Paginate 10 items per page
    pagination = query.paginate(page=page, per_page=10, error_out=False)
    items = pagination.items

    categories = Category.query.filter_by(is_deleted=False).order_by(Category.name.asc()).all()

    return render_template(
        'main/index.html',
        items=items,
        pagination=pagination,
        categories=categories,
        query_param=query_param,
        category_id=category_id,
        location_param=location_param,
        item_type=item_type,
        date_from=date_from,
        date_to=date_to,
        status_param=status_param,
        statuses=Item.STATUSES
    )

@main_bp.route('/items/<int:item_id>')
def item_detail(item_id):
    """View details for a specific item."""
    item = Item.query.get_or_404(item_id)

    if item.is_deleted:
        abort(404)

    # Permission check: Non-approved items visible only to submitter, head, or admin
    if item.status != Item.STATUS_APPROVED:
        if not current_user.is_authenticated:
            abort(403)
        if current_user.id != item.user_id and not current_user.is_head_or_admin():
            abort(403)

    # Check if logged-in user has already submitted a claim for this item
    existing_claim = None
    if current_user.is_authenticated:
        existing_claim = ClaimRequest.query.filter_by(item_id=item.id, user_id=current_user.id).first()

    return render_template('main/item_detail.html', item=item, existing_claim=existing_claim)

@main_bp.route('/items/<int:item_id>/claim', methods=['GET', 'POST'])
@login_required
def submit_claim(item_id):
    """Submit ownership claim request for a found item."""
    item = Item.query.get_or_404(item_id)

    if item.is_deleted or item.status != Item.STATUS_APPROVED:
        flash('This item is not available for claim.', 'warning')
        return redirect(url_for('main.item_detail', item_id=item.id))

    if item.user_id == current_user.id:
        flash('You cannot claim an item that you reported.', 'info')
        return redirect(url_for('main.item_detail', item_id=item.id))

    # Prevent duplicate claims
    existing_claim = ClaimRequest.query.filter_by(item_id=item.id, user_id=current_user.id).first()
    if existing_claim:
        flash('You have already submitted a claim for this item.', 'info')
        return redirect(url_for('main.item_detail', item_id=item.id))

    form = ClaimForm()
    if form.validate_on_submit():
        claim = ClaimRequest(
            item_id=item.id,
            user_id=current_user.id,
            reason=form.reason.data.strip(),
            description_proof=form.description_proof.data.strip(),
            contact_info=form.contact_info.data.strip()
        )
        db.session.add(claim)
        db.session.commit()

        AuditService.log('SUBMITTED_CLAIM', target_type='ClaimRequest', target_id=claim.id, details=f"Item ID: {item.id}")

        # Notify submitter/heads that a claim was filed
        NotificationService.send_notification(
            user_id=item.user_id,
            title="New Claim Filed on Your Item",
            message=f"Someone submitted an ownership claim for your found item: '{item.title}'.",
            link=url_for('user.dashboard')
        )

        flash('Your claim request has been submitted successfully and is pending review by moderators.', 'success')
        return redirect(url_for('main.item_detail', item_id=item.id))

    return render_template('main/submit_claim.html', form=form, item=item)

@main_bp.route('/notifications')
@login_required
def notifications():
    """User in-app notifications inbox."""
    user_notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('main/notifications.html', notifications=user_notifs)

@main_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    """Mark notification as read."""
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return redirect(notif.link or url_for('main.notifications'))
