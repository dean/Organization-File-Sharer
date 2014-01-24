from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
from gtb import db

""" Organizations will each have their own defined roles too... eventually.

    For now -- organizations have a single admin that can be transferred between
    members. The only thing they can do is delete items.
"""

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(20))
    password = db.Column(db.String(20))
    admin = db.Column(db.Boolean)

    def organizations(self):
        return (om.organization for om in OrganizationMember.query
                    .filter_by(user_id=self.id).all())

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def is_active(self):
        return True

    def get_id(self):
        return unicode(self.id)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __init__(self, username, name, password, admin=False):
        self.username = username
        self.name = name
        self.password = generate_password_hash(password)
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

class Organization(db.Model):
    __tablename__ = "organizations"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    admin = db.relationship('User')

    def __init__(self, name, admin=False):
        self.name = name
        self.admin = admin

class OrganizationMember(db.Model):
    __tablename__ = "organization_members"
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    accepted = db.Column(db.Boolean)
    rank = db.Column(db.Integer)

    organization = db.relationship('Organization')
    user = db.relationship('User')

    def __init__(self, organization_id, user_id, accepted=False, rank=1):
        self.organization_id = organization_id
        self.user_id = user_id
        self.accepted = accepted
        self.rank = rank

    def accept():
        self.accepted = True
        
class File(db.Model):
    __tablename__ = "files"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    organization = db.relationship('Organization')
    author = db.relationship('User')

    def __init__(self, name, organization_id, author):
        self.name = name
        self.organization_id = organization_id
        self.author = author
