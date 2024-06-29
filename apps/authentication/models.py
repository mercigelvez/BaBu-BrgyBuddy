# -*- encoding: utf-8 -*-

from flask_login import UserMixin
from flask import Flask
from itsdangerous import URLSafeTimedSerializer as Serializer, BadSignature, SignatureExpired
from apps import db, login_manager
from flask import session, current_app
from flask_login import logout_user
import secrets
from datetime import datetime, timezone

from apps.authentication.util import hash_pass

class Users(db.Model, UserMixin):

    __tablename__ = 'Users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(64), unique=True)
    password = db.Column(db.LargeBinary)
    chat_histories = db.relationship('ChatHistory', backref='user', lazy='dynamic')
    remember_token = db.Column(db.String(100), unique=True)
    role = db.Column(db.String(20), nullable=False, default='user')
    last_login = db.Column(db.DateTime)
    total_sessions = db.Column(db.Integer, default=0, nullable=False)
    total_session_duration = db.Column(db.Integer, default=0, nullable=False)
    language_preference = db.Column(db.String(10), nullable=False, default='english') 

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == 'password':
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)
    
    def get_remember_token(self, expires_in=2592000):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}, salt='remember-salt')

    @staticmethod
    def verify_remember_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, salt='remember-salt', max_age=2592000)  # 30 days
        except (BadSignature, SignatureExpired):
            return None
        return Users.query.get(data['user_id'])

    def set_remember_token(self):
        self.remember_token = secrets.token_urlsafe(32)
        db.session.commit()

    def clear_remember_token(self):
        self.remember_token = None
        db.session.commit()
        
    def update_login_info(self):
        self.last_login = datetime.utcnow().replace(tzinfo=timezone.utc)
        if self.total_sessions is None:
            self.total_sessions = 0
        self.total_sessions += 1
        db.session.commit()

    def update_session_duration(self, duration):
        if self.total_session_duration is None:
            self.total_session_duration = 0
        self.total_session_duration += duration
        db.session.commit()

    @property
    def avg_session_duration(self):
        if self.total_sessions and self.total_sessions > 0:
            return self.total_session_duration // self.total_sessions
        return 0


@login_manager.user_loader
def user_loader(user_id):
    user = Users.query.filter_by(id=user_id).first()
    if user:
        if 'remember_token' in session:
            if user.remember_token != session.get('remember_token'):
                # Token is invalid, log out the user
                logout_user()
                session.pop('remember_token', None)
                return None
        return user
    return None



@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = Users.query.filter_by(username=username).first()
    return user if user else None