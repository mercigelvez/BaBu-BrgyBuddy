from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import Email, DataRequired, EqualTo, Length

# login and registration
class LoginForm(FlaskForm):
    username = StringField("Username", id="username_login", validators=[DataRequired(),])
    password = PasswordField("Password", id="pwd_login", validators=[DataRequired()])

class CreateAccountForm(FlaskForm):
    username = StringField("Username", id="username_create", validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField("Email", id="email_create", validators=[DataRequired(), Email()])
    password = PasswordField("Password", id="pwd_create", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password", id="confirm_pwd_create", validators=[DataRequired(), EqualTo("password", message="Passwords must match")])

