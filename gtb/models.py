from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.sqlalchemy import SQLAlchemy
from constants import TERMS
from datetime import datetime
from gtb import app, db

import os


""" Organizations will each have their own defined roles too... eventually.

    For now -- organizations have a single admin that can be transferred between
    members. The only thing they can do is delete items.
"""


class Category(db.Model):
    """
    Represents a course category
    """
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(6))

    def __init__(self, tag):
        self.tag = tag


class Conversation(db.Model):
    """
    Represents a conversation between users.
    """
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


class File(db.Model):
    """
    Represents a file for an organization
    """
    __tablename__ = "files"

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    folder_id = db.Column(db.String, db.ForeignKey('folders.id'))
    course_tag = db.Column(db.String(6))
    course_id = db.Column(db.Integer)
    class_date = db.Column(db.DateTime)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization', backref='files')
    author = db.relationship('User', backref='uploads')
    folder = db.relationship('Folder', backref='files')

    # File does not need to be a course document.
    def __init__(self, file_name, author_id, organization_id, folder_id,
                    course_tag=None, course_id=None, class_date=None):
        self.file_name = file_name
        self.author_id = author_id
        self.organization_id = organization_id
        self.folder_id = folder_id
        self.course_tag = course_tag
        self.course_id = course_id
        self.class_date = class_date

        if course_tag and course_id:
            folder = db.session.query(Folder).filter_by(id=folder_id).first()
            path = (folder.path + self.course_tag + '_' +
                    self.course_id + '/')

            if not os.path.exists(path):
                os.makedirs(path)

    @property
    def full_path(self):
        """
        Returns the path to the file
        """
        if self.course_tag and self.course_id:
            return (self.folder.path + self.course_tag + '_' +
                    str(self.course_id) + '/')
        else:
            return self.folder.path

    @property
    def course_folder(self):
        """
        Returns the folder name via course_tag and course_id
        """
        return self.course_tag + ' ' + str(self.course_id)


class Folder(db.Model):
    """
    Represents a Folder
    """
    __tablename__ = 'folders'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    top = db.Column(db.Boolean)
    term = db.Column(db.Enum(*TERMS))
    year = db.Column(db.Integer)

    organization = db.relationship('Organization', backref='folders')

    # Lets allow for a public folder for documents too.
    def __init__(self, organization_id, top=False, term=None, year=None):
        self.organization_id = organization_id
        self.top = top
        self.term = term
        self.year = year

        path = app.config['UPLOAD_FOLDER']
        if not top:
            path += term + '_' + year + '/'

        if not os.path.exists(path):
            os.makedirs(path)

    @property
    def name(self):
        if self.term and self.year:
            return self.term + ' ' + str(self.year)
        else:
            return str(self.organization_id)

    @property
    def path(self):
        if self.term and self.year:
            return (app.config['UPLOAD_FOLDER'] +
                   '{0}/{1}_{2}/'.format(str(self.organization_id),
                                          self.term,
                                          str(self.year)))
        else:
            return '{0}/'.format(str(self.organization_id))


class Message(db.Model):
    """
    Represents a message as part of a conversation.
    """
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


class Organization(db.Model):
    """
    Represents an organization that has members, and files.
    """
    __tablename__ = "organizations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    admin = db.relationship('User')

    def __init__(self, name, admin_id):
        self.name = name
        self.admin_id = admin_id


class OrganizationMember(db.Model):
    """
    Represents a member of an organization
    """
    __tablename__ = "organization_members"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    accepted = db.Column(db.Boolean)
    rank = db.Column(db.Integer)

    organization = db.relationship('Organization', backref='members')
    user = db.relationship('User')

    def __init__(self, organization_id, user_id, accepted=False, rank=1):
        self.organization_id = organization_id
        self.user_id = user_id
        self.accepted = accepted
        self.rank = rank

    def accept(self):
        self.accepted = True
        db.session.commit()

    def deny(self):
        self.accepted = False
        db.session.commit()


class User(db.Model):
    """
    Represents a standard user. (Login, own objects, etc)
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(20))
    password = db.Column(db.String(20))
    admin = db.Column(db.Boolean)

    def organizations(self):
        return [om.organization for om in
                    OrganizationMember.query.filter_by(
                                            user_id=self.id,
                                            accepted=True
                                        ).all()
                ]

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
