from datetime import datetime
import uuid
from apps import db
from .authentication.models import Users

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    messages = db.relationship('Message', backref='chat_history', lazy=True, cascade="all, delete-orphan")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ChatHistory {self.user_id}>'

        
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_history_id = db.Column(db.Integer, db.ForeignKey('chat_history.id'), nullable=False)
    sender = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(1000), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Message {self.message}>'
    
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.String(8), unique=True, nullable=False, default=lambda: uuid.uuid4().hex[:8])
    full_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    birthplace = db.Column(db.String(100), nullable=False)
    purpose = db.Column(db.String(200), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Appointment {self.appointment_id}>'
    

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())