from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
from appname import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(20))
    password = db.Column(db.String(20))
    admin = db.Column(db.Boolean)

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def is_active(self):
        return True

    def get_id(self):
        return unicode(self.id)

    def __init__(self, username, name, password, admin=False):
        self.username = username
        self.name = name
        self.password = password
        self.admin = admin

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    sender = db.relationship('User')
    content = db.Column(db.String(511))
    sent_at = db.Column(db.DateTime(), default=datetime.utcnow)
    read = db.Column(db.Boolean())

    def read_msg(self):
        self.read = True

    def __init__(self, conversation_id, sender, content, read=False):
        self.conversation_id = conversation_id
        self.sender_id = sender
        self.content = content
        self.read = read

class Conversation(db.Model):
    __tablename__  = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer)
    receiver_id = db.Column(db.Integer)
    subject = db.Column(db.String(100))
    messages = db.relationship('Message', backref='conversation')

    def __init__(self, sender_id, receiver_id, subject):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.subject = subject

