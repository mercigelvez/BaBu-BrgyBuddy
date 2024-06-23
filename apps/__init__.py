# -*- encoding: utf-8 -*-
"""
/*!

=========================================================
TEAM BABU - BSIT 3-2 OF 23-24
=========================================================

*/
"""

import os

from flask import Flask, session
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from flask_migrate import Migrate
from flask_mail import Mail
from datetime import timedelta


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

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Configure session
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
    
    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    
    @app.before_request
    def before_request():
        session.permanent = True
        app.permanent_session_lifetime = app.config['PERMANENT_SESSION_LIFETIME']
    
    return app