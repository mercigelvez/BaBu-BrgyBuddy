# -*- encoding: utf-8 -*-
"""
/*!

=========================================================
TEAM BABU - BSIT 3-2 OF 23-24
=========================================================

*/
"""

from flask import render_template, redirect, request, url_for
from flask_login import (
    current_user,
    login_user,
    logout_user
)

from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm, ForgotPasswordForm, ResetPasswordForm
from apps.authentication.models import Users
from flask import jsonify, request
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from apps import mail
from flask import render_template, redirect, url_for, flash
from apps.authentication import util
from flask import render_template_string, current_app
import os
from email.mime.image import MIMEImage
import base64

s = URLSafeTimedSerializer('Thisisasecret!')

from apps.authentication.util import verify_pass

@blueprint.route('/')
def route_default():
    return redirect(url_for('authentication_blueprint.login'))

# Login & Registration

@blueprint.route('/check_username', methods=['POST'])
def check_username():
    username = request.form.get('username')
    user = Users.query.filter_by(username=username).first()
    if user:
        return jsonify({'username_exists': True})
    else:
        return jsonify({'username_exists': False})


@blueprint.route('/check_email', methods=['POST'])
def check_email():
    email = request.form.get('email')
    user = Users.query.filter_by(email=email).first()
    if user:
        return jsonify({'email_exists': True})
    else:
        return jsonify({'email_exists': False})


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        username = request.form['username']
        password = request.form['password']

        # Locate user
        user = Users.query.filter_by(username=username).first()

        # Check the password
        if user and verify_pass(password, user.password):

            login_user(user)
            return redirect(url_for('authentication_blueprint.route_default'))

        # Something (user or pass) is not ok
        return render_template('accounts/login.html',
                               msg='Wrong user or password',
                               form=login_form)

    if not current_user.is_authenticated:
        return render_template('accounts/login.html',
                               form=login_form)
    return redirect(url_for('home_blueprint.index'))


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if passwords match
        if password != confirm_password:
            return render_template('accounts/register.html', msg='Passwords do not match', success=False, form=create_account_form)

        # Check if username exists
        user = Users.query.filter_by(username=username).first()
        if user:
            return render_template('accounts/register.html', msg='Username already registered', success=False, form=create_account_form)

        # Check if email exists
        user = Users.query.filter_by(email=email).first()
        if user:
            check_username_url = url_for('authentication_blueprint.check_username_availability')
            return render_template('accounts/register.html', msg='Email already registered', success=False, form=create_account_form, check_username_url=check_username_url)

        # Create the user
        user = Users(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()

        # Flash a success message
        flash('User created successfully. Please log in.', 'success')

        # Redirect to login page
        return redirect(url_for('authentication_blueprint.login'))
    else:
        return render_template('accounts/register.html', form=create_account_form)


@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authentication_blueprint.login')) 

# Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('home/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('home/page-500.html'), 500


@blueprint.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user:
            token = s.dumps(user.email, salt='email-confirm')
            reset_link = url_for('authentication_blueprint.reset_password', token=token, _external=True)
            
            # Load the HTML template
            template_path = os.path.join(current_app.root_path, 'templates', 'email', 'email_template.html')
            with open(template_path, 'r') as f:
                template_html = f.read()
            
            # Load and embed the logo image
            logo_base64 = None
            try:
                logo_path = os.path.join(current_app.root_path, 'static', 'assets', 'img', 'babu-logo.png')
                with open(logo_path, 'rb') as f:
                    logo_data = f.read()
                logo_base64 = base64.b64encode(logo_data).decode('utf-8')
            except FileNotFoundError:
                current_app.logger.warning(f"Logo file not found at {logo_path}")

            # Render the template with data
            rendered_html = render_template_string(template_html, user=user, reset_link=reset_link, logo_base64=logo_base64)
            
            msg = Message('Password Reset Request', sender='noreply@demo.com', recipients=[user.email])
            msg.html = rendered_html
            mail.send(msg)
        
        flash('If your email is registered, you will receive a password reset email.', 'info')
        return redirect(url_for('authentication_blueprint.forgot_password'))

    return render_template('accounts/forgot_password.html', form=form)



@blueprint.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    print(f"Received token: {token}")
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
        print(f"Decoded email: {email}")
    except Exception as e:
        print(f"Error decoding token: {e}")
        flash('The reset link is invalid or has expired.', 'warning')
        return redirect(url_for('authentication_blueprint.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=email).first()
        if user:
            hashed_password = util.hash_pass(form.password.data)
            user.password = hashed_password
            db.session.commit()
            flash('Your password has been updated! You can now login', 'success')

    return render_template('accounts/reset_password.html', form=form)
