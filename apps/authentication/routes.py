# -*- encoding: utf-8 -*-
"""
/*!

=========================================================
TEAM BABU - BSIT 3-2 OF 23-24
=========================================================

*/
"""

from flask import render_template, redirect, request, url_for, session
from flask_login import (
    current_user,
    login_user,
    logout_user,
    login_required
)
from datetime import datetime, timedelta, timezone
from functools import wraps
import time
from apps.authentication.util import check_timeout, check_session_timeout, update_last_activity
from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm, ForgotPasswordForm, ResetPasswordForm
from apps.authentication.models import Users
from flask import jsonify, request, make_response
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from apps import mail
from flask import render_template, redirect, url_for, flash
from apps.authentication import util
from flask import render_template_string, current_app
import os
from email.mime.image import MIMEImage
import base64
from .util import validate_remember_token

s = URLSafeTimedSerializer('Thisisasecret!')

from apps.authentication.util import verify_pass

# @blueprint.route('/')
# def route_default():
#     return redirect(url_for('authentication_blueprint.login'))

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
        username = request.form['username']
        password = request.form['password']
        user = Users.query.filter_by(username=username).first()
        if user and verify_pass(password, user.password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('home_blueprint.tables'))
            else:
                flash('Only admin users can log in.', 'warning')
                return redirect(url_for('home_blueprint.public_chatbot'))
        flash('Wrong username or password.', 'warning')
    return render_template('accounts/login.html', form=login_form)


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        language = request.form['language']

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
        user = Users(username=username, email=email, password=password, language_preference=language)
        db.session.add(user)
        db.session.commit()

        # Flash a success message
        flash('User created successfully. Please log in.', 'success')

        # Redirect to login page
        return redirect(url_for('authentication_blueprint.login'))
    else:
        return render_template('accounts/register.html', form=create_account_form)


@blueprint.route('/logout')
@login_required
def logout():
    if current_user.is_authenticated:
        # Update session duration
        login_time = session.get('login_time')
        if login_time:
            duration = (datetime.now(timezone.utc) - login_time).total_seconds()
            current_user.update_session_duration(int(duration))
        
        # Clear remember token
        current_user.clear_remember_token()
    
    # Perform logout
    logout_user()
    
   # Clear session data
    session.clear()
    
    # Create response
    response = make_response(redirect(url_for('authentication_blueprint.login')))
    
    # Set cache control headers
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    # Clear any cookies
    response.set_cookie('session', '', expires=0)
    
    return redirect(url_for('authentication_blueprint.login'))
# Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    flash('Session Expired. Please log in.', 'warning')
    return redirect(url_for('authentication_blueprint.login'))


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
    try:
        email = s.loads(token, salt='email-confirm', max_age=1800)
    except Exception as e:
        flash('The reset link is invalid or has expired.', 'warning')
        return redirect(url_for('authentication_blueprint.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=email).first()
        if user:
            if verify_pass(form.password.data, user.password):
                flash('New password must be different from the current password', 'danger')
                return render_template('accounts/reset_password.html', form=form)
            
            hashed_password = util.hash_pass(form.password.data)
            user.password = hashed_password
            db.session.commit()
            flash('Your password has been updated! You can now login', 'success')
            return redirect(url_for('authentication_blueprint.login'))

    return render_template('accounts/reset_password.html', form=form)

@blueprint.before_request
def before_request():
    if current_user.is_authenticated:
        check_session_timeout()
        session['last_activity'] = time.time()
        
@blueprint.route('/')
@update_last_activity
def route_default():
    return render_template('landing-page.html')