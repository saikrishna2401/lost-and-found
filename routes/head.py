"""
Head Reviewer Routes Module.
Handles pending submission moderation, approving/rejecting item reports, and claim request management.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db
from models.item import Item
from models.claim import ClaimRequest
from models.found_report import FoundReport
from utils.decorators import role_required
from services.audit_service import AuditService
from services.notification_service import NotificationService

head_bp = Blueprint('head', __name__, url_prefix='/head')

@head_bp.route('/dashboard')
@login_required
@role_required('head', 'admin')
def dashboard():
    """Head Reviewer Dashboard: Lists pending submissions, claim requests, found reports, and all posts."""
    status_filter = request.args.get('status', '').strip()

    pending_query = Item.query.filter(
        Item.is_deleted == False,
        Item.status.in_([Item.STATUS_PENDING, Item.STATUS_UNDER_REVIEW])
    ).order_by(Item.created_at.asc())

    if status_filter and status_filter in Item.STATUSES:
        all_items = Item.query.filter_by(is_deleted=False, status=status_filter).order_by(Item.created_at.desc()).all()
    else:
        all_items = Item.query.filter_by(is_deleted=False).order_by(Item.created_at.desc()).all()

    pending_items = pending_query.all()
    pending_claims = ClaimRequest.query.filter_by(status=ClaimRequest.STATUS_PENDING).order_by(ClaimRequest.created_at.asc()).all()
    pending_found_reports = FoundReport.query.filter_by(status=FoundReport.STATUS_PENDING).order_by(FoundReport.created_at.asc()).all()

    return render_template(
        'head/dashboard.html',
        pending_items=pending_items,
        pending_claims=pending_claims,
        pending_found_reports=pending_found_reports,
        all_items=all_items,
        status_filter=status_filter,
        statuses=Item.STATUSES
    )

@head_bp.route('/items/<int:item_id>/review', methods=['GET', 'POST'])
@login_required
@role_required('head', 'admin')
def review_item(item_id):
    """Review an item post and update its lifecycle status."""
    item = Item.query.get_or_404(item_id)

    if request.method == 'POST':
        action = request.form.get('action') # 'approve', 'reject', 'under_review', 'returned', 'archived'
        rejection_reason = request.form.get('rejection_reason', '').strip()

        if action == 'approve':
            item.status = Item.STATUS_APPROVED
            item.rejection_reason = None
            db.session.commit()

            AuditService.log('HEAD_APPROVED_POST', target_type='Item', target_id=item.id)
            NotificationService.send_notification(
                user_id=item.user_id,
                title="Post Approved!",
                message=f"Your lost/found item report '{item.title}' has been approved and is now public.",
                link=url_for('main.item_detail', item_id=item.id)
            )
            flash(f"Item '{item.title}' has been APPROVED.", 'success')

        elif action == 'reject':
            if not rejection_reason:
                flash('Rejection reason is required when rejecting a post.', 'danger')
                return render_template('head/review_item.html', item=item)

            item.status = Item.STATUS_REJECTED
            item.rejection_reason = rejection_reason
            db.session.commit()

            AuditService.log('HEAD_REJECTED_POST', target_type='Item', target_id=item.id, details=f"Reason: {rejection_reason}")
            NotificationService.send_notification(
                user_id=item.user_id,
                title="Post Rejected",
                message=f"Your lost/found report '{item.title}' was rejected. Reason: {rejection_reason}",
                link=url_for('user.dashboard')
            )
            flash(f"Item '{item.title}' has been REJECTED.", 'info')

        elif action in [Item.STATUS_UNDER_REVIEW, Item.STATUS_RETURNED, Item.STATUS_ARCHIVED]:
            item.status = action
            db.session.commit()

            AuditService.log(f'HEAD_UPDATED_STATUS_{action.upper()}', target_type='Item', target_id=item.id)
            flash(f"Item '{item.title}' status updated to '{action}'.", 'success')

        return redirect(url_for('head.dashboard'))

    return render_template('head/review_item.html', item=item)

@head_bp.route('/claims/<int:claim_id>/review', methods=['GET', 'POST'])
@login_required
@role_required('head', 'admin')
def review_claim(claim_id):
    """Review an ownership claim request."""
    claim = ClaimRequest.query.get_or_404(claim_id)
    item = Item.query.get_or_404(claim.item_id)

    if request.method == 'POST':
        action = request.form.get('action') # 'approve' or 'reject'
        rejection_reason = request.form.get('rejection_reason', '').strip()

        claim.reviewed_by_id = current_user.id

        if action == 'approve':
            claim.status = ClaimRequest.STATUS_APPROVED
            item.status = Item.STATUS_CLAIMED
            db.session.commit()

            AuditService.log('HEAD_APPROVED_CLAIM', target_type='ClaimRequest', target_id=claim.id)
            
            # Notify Claimant (unlocks contact info)
            contact_msg = f" (Phone: {item.phone_number})" if item.phone_number else ""
            NotificationService.send_notification(
                user_id=claim.user_id,
                title="Claim Request Approved!",
                message=f"Your claim for '{item.title}' has been approved! The uploader's contact number{contact_msg} is now unlocked.",
                link=url_for('main.item_detail', item_id=item.id)
            )

            # Notify Uploader (informs contact sharing)
            if item.user_id != claim.user_id:
                NotificationService.send_notification(
                    user_id=item.user_id,
                    title="Claim Approved for Your Item",
                    message=f"Your item '{item.title}' has an approved claim by user '{claim.claimant.username}'. Your contact phone number has been shared with them.",
                    link=url_for('main.item_detail', item_id=item.id)
                )

            flash('Claim request APPROVED. Contact phone number unlocked for claimant.', 'success')

        elif action == 'reject':
            claim.status = ClaimRequest.STATUS_REJECTED
            claim.rejection_reason = rejection_reason
            db.session.commit()

            AuditService.log('HEAD_REJECTED_CLAIM', target_type='ClaimRequest', target_id=claim.id, details=f"Reason: {rejection_reason}")
            NotificationService.send_notification(
                user_id=claim.user_id,
                title="Claim Request Rejected",
                message=f"Your claim for '{item.title}' was rejected. Reason: {rejection_reason or 'Insufficient proof'}",
                link=url_for('user.dashboard')
            )
            flash('Claim request REJECTED.', 'info')

        return redirect(url_for('head.dashboard'))

    return render_template('head/review_claim.html', claim=claim, item=item)

@head_bp.route('/found_reports/<int:report_id>/review', methods=['GET', 'POST'])
@login_required
@role_required('head', 'admin')
def review_found_report(report_id):
    """Review a Found Item Report submitted for a Lost Item."""
    report = FoundReport.query.get_or_404(report_id)
    item = Item.query.get_or_404(report.item_id)

    if request.method == 'POST':
        action = request.form.get('action') # 'approve' or 'reject'
        rejection_reason = request.form.get('rejection_reason', '').strip()

        report.reviewed_by_id = current_user.id

        if action == 'approve':
            report.status = FoundReport.STATUS_APPROVED
            item.status = Item.STATUS_CLAIMED
            db.session.commit()

            AuditService.log('HEAD_APPROVED_FOUND_REPORT', target_type='FoundReport', target_id=report.id)

            # Notify Lost Item Owner (unlocks finder's contact details)
            NotificationService.send_notification(
                user_id=item.user_id,
                title="Someone Found Your Lost Item!",
                message=f"A report for your lost item '{item.title}' has been approved! Finder's contact details (Phone: {report.phone_number}, Email: {report.email}) are now unlocked.",
                link=url_for('main.item_detail', item_id=item.id)
            )

            # Notify Finder
            NotificationService.send_notification(
                user_id=report.user_id,
                title="Found Item Report Approved!",
                message=f"Your found report for '{item.title}' was approved! Your contact details have been shared with the item owner.",
                link=url_for('main.item_detail', item_id=item.id)
            )

            flash('Found item report APPROVED. Contact details unlocked for Lost Item owner.', 'success')

        elif action == 'reject':
            report.status = FoundReport.STATUS_REJECTED
            report.rejection_reason = rejection_reason
            db.session.commit()

            AuditService.log('HEAD_REJECTED_FOUND_REPORT', target_type='FoundReport', target_id=report.id, details=f"Reason: {rejection_reason}")
            NotificationService.send_notification(
                user_id=report.user_id,
                title="Found Item Report Rejected",
                message=f"Your found report for '{item.title}' was rejected. Reason: {rejection_reason or 'Insufficient details'}",
                link=url_for('user.dashboard')
            )
            flash('Found item report REJECTED.', 'info')

        return redirect(url_for('head.dashboard'))

    return render_template('head/review_found_report.html', report=report, item=item)
