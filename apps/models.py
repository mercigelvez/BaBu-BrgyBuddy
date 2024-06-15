from apps import db

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    messages = db.Column(db.Text, nullable=False)

    def __init__(self, user_id, messages):
        self.user_id = user_id
        self.messages = messages