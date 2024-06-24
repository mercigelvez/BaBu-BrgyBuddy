# -*- encoding: utf-8 -*-
"""
/*!

=========================================================
TEAM BABU - BSIT 3-2 OF 23-24
=========================================================

*/
"""

import os

import os
import click
from flask import Flask, session
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from flask_migrate import Migrate
from flask_mail import Mail
from datetime import timedelta
from flask.cli import with_appcontext

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()

def register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

def register_blueprints(app):
    for module_name in ('authentication', 'home'):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)

def configure_database(app):
    from apps.models import ChatHistory  # Import the ChatHistory model

    @app.before_first_request
    def initialize_database():
        db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()
        
def create_admin_user(username, email, password):
    from apps.authentication.models import Users
    
    admin_user = Users(
        username=username,
        email=email,
        password=password,  # The Users model will hash this
        role='admin'
    )
    db.session.add(admin_user)
    db.session.commit()

@click.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.argument('password')
@with_appcontext
def create_admin_command(username, email, password):
    create_admin_user(username, email, password)
    click.echo(f"Admin user {username} created.")

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Configure session
    app.config['SESSION_PERMANENT'] = False  # Change this to False
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
    
    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    
    # Set remember cookie duration
    login_manager.remember_cookie_duration = timedelta(days=30)
    
    @app.before_request
    def before_request():
        if current_user.is_authenticated:
            session.permanent = session.get('remember', False)
            if session.permanent:
                app.permanent_session_lifetime = timedelta(days=30)
            else:
                app.permanent_session_lifetime = timedelta(minutes=30)
                
    app.cli.add_command(create_admin_command)
    
    return app