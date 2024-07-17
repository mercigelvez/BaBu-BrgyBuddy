# -*- encoding: utf-8 -*-
"""
/*!

=========================================================
TEAM BABU - BSIT 3-2 OF 23-24
=========================================================

*/
"""
from time import sleep
import click
from flask import Flask, request, session, redirect, url_for
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from flask_migrate import Migrate
from flask_mail import Mail
from datetime import timedelta,  datetime
from flask.cli import with_appcontext
from sqlalchemy.exc import OperationalError, SQLAlchemyError
import logging
from logging.handlers import RotatingFileHandler
from flask_session import Session

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
    for module_name in ("authentication", "home"):
        module = import_module("apps.{}.routes".format(module_name))
        app.register_blueprint(module.blueprint)

def configure_logging(app):
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

def configure_database(app):

    @app.before_first_request
    def initialize_database():
        db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        try:
            db.session.remove()
        except Exception as e:
            app.logger.error(f"Error in shutdown_session: {str(e)}")


def register_error_handlers(app):
    @app.errorhandler(OperationalError)
    def handle_db_connection_error(error):
        db.session.rollback()
        app.logger.error(f"Database connection error: {str(error)}")
        
        # Attempt to reconnect
        try:
            db.session.ping()
        except:
            sleep(1)  # Wait for 1 second before trying again
        
        # Redirect to the same page, which will retry the operation
        return redirect(url_for(request.endpoint, **request.view_args))

    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error):
        db.session.rollback()
        app.logger.error(f"SQLAlchemy error: {str(error)}")
        
        # Redirect to the same page, which will retry the operation
        return redirect(url_for(request.endpoint, **request.view_args))


def create_admin_user(username, email, password):
    from apps.authentication.models import Users

    admin_user = Users(
        username=username,
        email=email,
        password=password,  # The Users model will hash this
        role="admin",
    )
    db.session.add(admin_user)
    db.session.commit()


@click.command("create-admin")
@click.argument("username")
@click.argument("email")
@click.argument("password")
@with_appcontext
def create_admin_command(username, email, password):
    create_admin_user(username, email, password)
    click.echo(f"Admin user {username} created.")


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    Session(app)
    
    register_error_handlers(app)
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
            
            # Clear old sessions
            if 'last_active' in session:
                last_active = datetime.fromisoformat(session['last_active'])
                if datetime.utcnow() - last_active > timedelta(hours=1):
                    session.clear()
                    return redirect(url_for('authentication_blueprint.login'))
            session['last_active'] = datetime.utcnow().isoformat()

    app.cli.add_command(create_admin_command)

    return app
