from flask import Blueprint, request, render_template, flash, g, session, redirect
from flask.ext.login import login_user, logout_user, current_user, login_required
from gtb import db, app, login_manager
from forms import Register, LoginForm, ConversationForm, CreateOrg, InviteToOrg
from models import (User, Message, Conversation, Organization, OrganizationMember,
                    File)
from functools import wraps
import urllib
import os
import re

#DECORATORS

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.admin:
            return f(*args, **kwargs)
        return no_perms("You are not an admin!")
    return decorated_function


@app.before_request
def before_request():
    g.user = current_user
    if g.user is None:
        g.user = User("", "Guest", "")
    g.login_form = LoginForm()


@app.route("/")
def home():
    return render_template("home.html")


#TODO: Make this exclusively no_perms, and fix templates to use flashed text
@app.route("/no_perms")
def no_perms(msg):
    return render_template("message.html",  msg=msg)


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = Register()
    message = ""

    if request.method == "POST":
        if form.username.data < 4:
            message="Your username needs to be 4 or more characters!"
        elif len(form.password.data) < 4:
            message="Your password needs to be 4 or more characters!"
        elif form.password.data != form.confirm_pass.data:
            message="The passwords provided did not match!\n"
        elif User.query.filter_by(username=form.username.data).all():
            message="This username is taken!"
        else:
            #Add user to db
            user = User(name=form.name.data, username=form.username.data,
                password=form.password.data, admin=form.admin.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Registered and logged in successfully!")
            return redirect("/")

    return render_template('register.html',  form=form, message=message)


@login_manager.user_loader
def load_user(userid):
    return User.query.filter_by(id=userid).first()


def get_user():
    # A user id is sent in, to check against the session
    # and based on the result of querying that id we
    # return a user (whether it be a sqlachemy obj or an
    # obj named guest

    if 'user_id' in session:
            return User.query.filter_by(id=session["user_id"]).first()
    return None


@app.route("/login", methods=['GET', 'POST'])
def login():
    if g.user.is_anonymous():
        form=LoginForm(request.form, csrf_enabled=False)
        if form.validate_on_submit():
            # login and validate the user...
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                flash("Logged in successfully.")
                return redirect("/")
    else:
        return no_perms("There is a user already logged in!")
    return render_template("login.html", form=form)


@app.route("/logout", methods=['POST'])
def logout():
    logout_user()
    flash("Logged out successfully!")
    return redirect("/")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.')


#TODO: Sort most recent conversations to first
#TODO: Add in unread messages
@app.route("/inbox", methods=['GET'])
@login_required
def inbox():
    unsorted_conversations = Conversation.query.filter_by(sender_id=g.user.id).all() + \
                                Conversation.query.filter_by(receiver_id=g.user.id).all()

    if unsorted_conversations:
        conversations = []
        for conv in unsorted_conversations:
            if conv.receiver_id == g.user.id:
                conv.otherperson = User.query.filter_by(id=conv.sender_id).first()
            else:
                conv.otherperson = User.query.filter_by(id=conv.receiver_id).first()
            conversations.append(conv)

        #conversations = unsorted_conversations.sort(key=lambda r: r.messages[len(r.messages)-1].sent_at)
        return render_template('inbox.html', conversations=conversations)

    return no_perms("You do not have any conversations!")


#TODO: Make sure the first message is sent with the listing title
#TODO: Implement read and unread messages.
#TODO: Clean up this method, it is messy as shit.
#TODO: Rework the url to be less redundant, and more proper.
@app.route("/<sender_id>/<receiver_id>/conversation", methods=['GET', 'POST'])
@login_required
def conversation(sender_id,receiver_id):
    form = ConversationForm()
    sender = User.query.filter_by(id=sender_id).first()
    receiver = User.query.filter_by(id=receiver_id).first()

    if not sender or not receiver:
        return no_perms("One of the users provided does not exist!")

    if sender.id != g.user.id:
        receiver = sender

    conv = Conversation.query.filter_by(sender_id=sender_id).filter_by(receiver_id=receiver_id).first() or Conversation.query.filter_by(sender_id=receiver_id).filter_by(receiver_id=sender_id).first()


    if request.method == "POST":
        if not conv:
            if form.content.data and form.subject.data:
                conv = Conversation(sender_id=sender_id, receiver_id=receiver_id, subject=form.subject.data)
                db.session.add(conv)
                db.session.commit()
                msg = Message(conversation_id=conv.id, sender=g.user.id, content=form.content.data)

                db.session.add(msg)
                db.session.commit()

            else:
                return no_perms("You didn't input a subject/message!")

        elif form.content.data:

            msg = Message(conversation_id=conv.id, sender=g.user.id, content=form.content.data)

            db.session.add(msg)
            db.session.commit()
        else:
            return no_perms("You didn't input a message!")
    if conv:
        for msg in conv.messages:
            msg.sent_at = msg.sent_at.strftime("%b %d, %Y")
        conv.messages = Message.query.filter_by(conversation_id=conv.id).all()

    return render_template("conversation.html", form=form, conversation=conv, receiver=receiver)


@app.route("/search", methods=['GET', 'POST'])
def search():
    if not request.method == "POST":
        return no_perms("You need to provide a term to search for!")
    return "Search page!"


@app.route("/create/organization", methods=['GET', 'POST'])
@login_required
def create_org():
    form = CreateOrg()
    msg = ""
    if request.method == "POST":
        new_org = Organization(name=form.name.data, admin_id=current_user.id)
        db.session.add(new_org)
        db.session.commit()

        org_member = OrganizationMember(organization_id=new_org.id,
                                        user_id=current_user.id,
                                        accepted=True,
                                        rank=100)
        db.session.add(org_member)
        db.session.commit()
        msg = "Organization created successfully!"
        # Should redirect to add members page, but that's not created yet :(

    return render_template("create_org.html", form=form, msg=msg)


@app.route("/me/organizations")
@login_required
def my_orgs():
    orgs = current_user.organizations()
    admin_orgs = filter(lambda org: org.admin_id == current_user.id, orgs)
    member_orgs = filter(lambda org: org.admin_id != current_user.id, orgs)

    return render_template("my_orgs.html", admin_orgs=admin_orgs,
                           member_orgs=member_orgs)


# Make sure a user has permissions to view the org
@app.route("/display/organization/<int:id>")
def display_org(id):
    # for now lets just display members and files.
    members = OrganizationMember.query.filter_by(organization_id=id).all()
    files = File.query.filter_by(organization_id=id).all()

    return render_template("display_org.html", members=members, files=files)
