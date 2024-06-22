from datetime import datetime
from apps import db
from .authentication.models import Users

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    messages = db.relationship('Message', backref='chat_history', lazy=True)
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