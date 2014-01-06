from wtforms import Form, TextField, TextAreaField, PasswordField, BooleanField, SelectField
from wtforms.validators import Required, Email, EqualTo
from models import User

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
