"""
Forms Module.
Defines WTForms for authentication, item submission, claims, user management, moderation, and password resets.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, DateField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models.user import User
from models.category import Category

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register Account')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data.strip()).first():
            raise ValidationError('Username is already registered.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError('Email address is already registered.')

class LoginForm(FlaskForm):
    username_or_email = StringField('Username or Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match.')])
    submit = SubmitField('Update Password')

class ForgotPasswordForm(FlaskForm):
    email_or_username = StringField('Email or Username', validators=[DataRequired()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match.')])
    submit = SubmitField('Reset Password')

class AdminResetPasswordForm(FlaskForm):
    new_password = PasswordField('New Password for User', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Set User Password')

class ItemForm(FlaskForm):
    title = StringField('Item Title', validators=[DataRequired(), Length(min=3, max=150)])
    item_type = SelectField('Report Type', choices=[('lost', 'Lost Item'), ('found', 'Found Item')], validators=[DataRequired()])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    description = TextAreaField('Detailed Description', validators=[DataRequired(), Length(min=10)])
    location = StringField('Location (City / Building / Area)', validators=[DataRequired(), Length(max=150)])
    date_event = DateField('Date (When Lost or Found)', validators=[DataRequired()])
    image = FileField('Upload Photo (Optional)', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp', 'gif'], 'Only images are allowed.')])
    submit = SubmitField('Submit Report')

class ClaimForm(FlaskForm):
    reason = TextAreaField('Reason for Claim', validators=[DataRequired(), Length(min=10)])
    description_proof = TextAreaField('Proof of Ownership (Unique identifiers, receipt, serial #)', validators=[DataRequired(), Length(min=10)])
    contact_info = StringField('Contact Details (Phone / Alternate Email)', validators=[DataRequired(), Length(max=150)])
    submit = SubmitField('Submit Claim Request')

class ReviewActionForm(FlaskForm):
    action = SelectField('Action', choices=[('approve', 'Approve'), ('reject', 'Reject')], validators=[DataRequired()])
    rejection_reason = TextAreaField('Rejection Reason (Required if rejected)', validators=[])
    submit = SubmitField('Submit Decision')

class UserManageForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    role = SelectField('System Role', choices=[('user', 'Normal User'), ('head', 'Head Reviewer'), ('admin', 'Administrator')], validators=[DataRequired()])
    password = PasswordField('Password (Leave blank to keep existing)', validators=[])
    submit = SubmitField('Save User')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(min=2, max=50)])
    description = StringField('Description', validators=[Length(max=200)])
    submit = SubmitField('Save Category')
