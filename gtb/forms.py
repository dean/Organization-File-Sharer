from flask.ext.wtf import (Form, SelectField, TextField, TextAreaField,
                            PasswordField, BooleanField, Required)
from constants import TERMS
from models import User
from util import get_tags, get_year_range


class Register(Form):
    name = TextField('name', [Required()])
    username = TextField('username', [Required()])
    password = PasswordField('password', [Required()])
    confirm_pass = PasswordField('confirm_pass', [Required()])
    admin = BooleanField('admin', default=False)

class LoginForm(Form):
    username = TextField('name', [Required()])
    password = PasswordField('password', [Required()])

class ConversationForm(Form):
    subject = TextField('subject')
    content = TextAreaField('content', [Required()])

class CreateOrg(Form):
    name = TextField('name', [Required()])

class InviteToOrg(Form):
    username = TextField('username', [Required()])
    rank = TextField('rank', [Required()])

class FileForm(Form):
    all_tags = get_tags()
    tags = zip(all_tags, all_tags)

    course_tag = SelectField('course_tag', choices=tags)
    course_id = TextField('course_id')

    terms = zip(TERMS, TERMS)
    term = SelectField('term', choices=terms)

    all_years = map(str, get_year_range()[::-1])
    years = zip(all_years, all_years)
    year = SelectField('year', choices=years)
