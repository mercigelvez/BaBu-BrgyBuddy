from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import Email, DataRequired, EqualTo, Length, ValidationError
import re

# login and registration
class LoginForm(FlaskForm):
    username = StringField("Username", id="username_login", validators=[DataRequired(),])
    password = PasswordField("Password", id="pwd_login", validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    
class PasswordComplexityValidator(object):
    def __init__(self, message=None):
        if not message:
            message = "Password must contain at least one uppercase letter, one lowercase letter, one number, one special character, and be at least 6 characters long."
        self.message = message

    def __call__(self, form, field):
        password = field.data
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$', password):
            raise ValidationError(self.message)

class CreateAccountForm(FlaskForm):
    username = StringField("Username", id="username_create", validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField("Email", id="email_create", validators=[DataRequired(), Email()])
    password = PasswordField("Password", id="pwd_create", validators=[DataRequired(), PasswordComplexityValidator()])
    confirm_password = PasswordField("Confirm Password", id="confirm_pwd_create", validators=[DataRequired(), EqualTo("password", message="Passwords must match")])
    language = SelectField('Preferred Language', choices=[('english', 'English'), ('tagalog', 'Tagalog')], validators=[DataRequired()])

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Password')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', id='new_pass' ,validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', id='confirm_new_pass', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')
    