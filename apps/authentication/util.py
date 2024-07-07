# -*- encoding: utf-8 -*-
"""
/*!

=========================================================
TEAM BABU - BSIT 3-2 OF 23-24
=========================================================

*/
"""

from datetime import datetime
import os
import hashlib
import binascii
from flask import session, current_app, redirect, url_for, flash, abort
from flask_login import logout_user, current_user
from functools import wraps
import time
from apps import db

# Inspiration -> https://www.vitoshacademy.com/hashing-passwords-in-python/


def hash_pass(password):
    """Hash a password for storing."""

    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                  salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash)  # return bytes


def verify_pass(provided_password, stored_password):
    """Verify a stored password against one provided by user"""

    stored_password = stored_password.decode('ascii')
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512',
                                  provided_password.encode('utf-8'),
                                  salt.encode('ascii'),
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password

def check_timeout(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and check_session_timeout():
            return redirect(url_for('authentication_blueprint.login'))
        session['last_activity'] = time.time()
        return f(*args, **kwargs)
    return decorated_function

def check_session_timeout():
    if 'last_activity' in session:
        now = time.time()
        last_activity = session['last_activity']
        if now - last_activity > current_app.config['PERMANENT_SESSION_LIFETIME'].total_seconds():
            logout_user()
            session.clear()
            flash('Your session has expired. Please log in again.', 'info')
            return True
    return False

def update_last_activity(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session['last_activity'] = time.time()
        return f(*args, **kwargs)
    return decorated_function

def validate_remember_token():
    if current_user.is_authenticated and 'remember_token' in session:
        token = session['remember_token']
        if current_user.verify_remember_token(token) != current_user:
            logout_user()
            session.pop('remember_token', None)
            flash('Your session has expired. Please log in again.', 'warning')
            return False
    return True

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

