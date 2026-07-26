"""
Normal User Routes Module.
Handles user dashboard, lost/found item submission with image uploads, smart match detection, and editing pending posts.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import db
from models.item import Item
from models.category import Category
from models.claim import ClaimRequest
from forms import ItemForm
from services.storage_service import StorageService
from services.matching_service import MatchingService
from services.notification_service import NotificationService
from services.audit_service import AuditService

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/dashboard')
@login_required
def dashboard():
    """Normal User Dashboard: Displays submitted posts, claim status, and notifications."""
    user_items = Item.query.filter_by(user_id=current_user.id, is_deleted=False).order_by(Item.created_at.desc()).all()
    user_claims = ClaimRequest.query.filter_by(user_id=current_user.id).order_by(ClaimRequest.created_at.desc()).all()

    return render_template(
        'user/dashboard.html',
        items=user_items,
        claims=user_claims
    )

@user_bp.route('/items/create', methods=['GET', 'POST'])
@login_required
def create_item():
    """Report Lost or Found Item."""
    form = ItemForm()
    categories = Category.query.filter_by(is_deleted=False).order_by(Category.name.asc()).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            try:
                image_filename = StorageService.save_image(form.image.data)
            except ValueError as e:
                flash(str(e), 'danger')
                return render_template('user/create_item.html', form=form)

        item = Item(
            title=form.title.data.strip(),
            item_type=form.item_type.data,
            category_id=form.category_id.data,
            description=form.description.data.strip(),
            location=form.location.data.strip(),
            date_event=form.date_event.data,
            image_filename=image_filename,
            status=Item.STATUS_PENDING,
            user_id=current_user.id
        )
        db.session.add(item)
        db.session.commit()

        AuditService.log('USER_SUBMITTED_ITEM', target_type='Item', target_id=item.id, details=f"Title: {item.title}")

        # Smart Matching Engine Check
        potential_matches = MatchingService.find_potential_matches(item)
        if potential_matches:
            match_titles = ", ".join([f"'{m.title}'" for m in potential_matches[:3]])
            NotificationService.send_notification(
                user_id=current_user.id,
                title="Possible Match Found!",
                message=f"We detected potential matches for your report: {match_titles}.",
                link=url_for('user.dashboard')
            )
            flash(f"Report submitted! System detected {len(potential_matches)} possible match(es). Check your dashboard notifications.", 'info')
        else:
            flash('Your item report has been submitted and is currently pending review by moderators.', 'success')

        return redirect(url_for('user.dashboard'))

    return render_template('user/create_item.html', form=form)

@user_bp.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    """
    Edit Pending Item.
    Users can only edit their OWN posts and ONLY if the post status is 'Pending'.
    """
    item = Item.query.get_or_404(item_id)

    if item.user_id != current_user.id:
        flash('You do not have permission to edit this post.', 'danger')
        abort(403)

    if item.status != Item.STATUS_PENDING:
        flash(f"You cannot edit this post because its status is '{item.status}'. Only 'Pending' posts can be edited.", 'warning')
        return redirect(url_for('user.dashboard'))

    form = ItemForm(obj=item)
    categories = Category.query.filter_by(is_deleted=False).order_by(Category.name.asc()).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        item.title = form.title.data.strip()
        item.item_type = form.item_type.data
        item.category_id = form.category_id.data
        item.description = form.description.data.strip()
        item.location = form.location.data.strip()
        item.date_event = form.date_event.data

        if form.image.data:
            try:
                new_image = StorageService.save_image(form.image.data)
                if new_image:
                    StorageService.delete_image(item.image_filename)
                    item.image_filename = new_image
            except ValueError as e:
                flash(str(e), 'danger')
                return render_template('user/edit_item.html', form=form, item=item)

        db.session.commit()

        AuditService.log('USER_EDITED_ITEM', target_type='Item', target_id=item.id)

        flash('Post updated successfully.', 'success')
        return redirect(url_for('user.dashboard'))

    if request.method == 'GET':
        form.item_type.data = item.item_type
        form.category_id.data = item.category_id

    return render_template('user/edit_item.html', form=form, item=item)
