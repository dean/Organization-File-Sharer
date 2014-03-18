from flask import (Blueprint, request, render_template, flash, g, session,
                    redirect, url_for, send_from_directory, send_file)
from flask.ext.login import (login_user, logout_user, current_user,
                                login_required)
from flask.ext.wtf import Form
from sqlalchemy import desc, and_
from werkzeug.utils import secure_filename
from wtforms.ext.sqlalchemy.orm import model_form

from constants import TERMS
from gtb import db, app, login_manager
from forms import (Register, LoginForm, ConversationForm, CreateOrg,
                    InviteToOrg, FileForm)
from models import (User, Message, Conversation, Organization,
                    OrganizationMember, File, Folder)
from util import (is_current_user, require_org_member, require_admin,
                    allowed_file, get_tags, get_user, get_year_range,
                    member_of)

import datetime
from functools import wraps
import os
import re
import urllib


@app.before_request
def before_request():
    """
    Execute this code before each request.
    """
    g.user = current_user
    if g.user is None:
        g.user = User("", "Guest", "")
    g.login_form = LoginForm()


"""
Routes
"""


@app.route("/organization/<int:org_id>/accept")
def accept_invitation():
    """
    Accept an invitation to an organization.
    """
    org_member = OrganizationMember.query.filter_by(
                                            organization_id=org_id,
                                            user_id=current_user.id,
                                            accepted=False
                                        ).first()

    if org_member:
        org_member.accept()
        return redirect('handle_invites')
    else:
        return no_perms('Could not find your invite!')


@app.route("/organization/<int:org_id>/add_member", methods=["GET", "POST"])
@login_required
def add_member(org_id):
    """
    Add member (a User) to an organization.
    """
    msg = ""
    form = InviteToOrg()

    if request.method == "POST":
        user = User.query.filter_by(username=form.username.data).first()
        if not user:
            return no_perms("User not found!")

        invite = OrganizationMember.query.filter_by(
                                            organization_id=org_id,
                                            user_id=user.id
                                        ).first()
        if invite:
            msg = "This user has already been invited!"
        else:
            org_member = OrganizationMember(organization_id=org_id,
                                            user_id=user.id,
                                            rank=form.rank.data,
                                            accepted=False)
            db.session.add(org_member)
            db.session.commit()

            msg = form.username.data + " invited to the organization!"

    return render_template("add_member.html", form=form, msg=msg)


#TODO: Make sure the first message is sent with the listing title
#TODO: Implement read and unread messages.
#TODO: Clean up this method, it is messy as shit.
#TODO: Rework the url to be less redundant, and more proper.
@app.route("/<sender_id>/<receiver_id>/conversation", methods=['GET', 'POST'])
@login_required
def conversation(sender_id, receiver_id):
    """
    Show a conversation between two users.
    """
    form = ConversationForm()
    sender = User.query.filter_by(id=sender_id).first()
    receiver = User.query.filter_by(id=receiver_id).first()

    if not sender or not receiver:
        return no_perms("One of the users provided does not exist!")

    if sender.id != g.user.id:
        receiver = sender

    conv = Conversation.query.filter_by(
                    sender_id=sender_id
                ).filter_by(
                    receiver_id=receiver_id
                ).first() or \
           Conversation.query.filter_by(
                    sender_id=receiver_id
                ).filter_by(
                    receiver_id=sender_id
                ).first()

    if request.method == "POST":
        if not conv:
            if form.content.data and form.subject.data:
                conv = Conversation(sender_id=sender_id,
                                    receiver_id=receiver_id,
                                    subject=form.subject.data)
                db.session.add(conv)
                db.session.commit()

                msg = Message(conversation_id=conv.id,
                              sender=g.user.id,
                              content=form.content.data)
                db.session.add(msg)
                db.session.commit()
            else:
                return no_perms("You didn't input a subject or message!")

        elif form.content.data:
            msg = Message(conversation_id=conv.id,
                          sender=g.user.id,
                          content=form.content.data)
            db.session.add(msg)
            db.session.commit()
        else:
            return no_perms("You didn't input a message!")
    if conv:
        for msg in conv.messages:
            msg.sent_at = msg.sent_at.strftime("%b %d, %Y")
        conv.messages = Message.query.filter_by(conversation_id=conv.id).all()

    return render_template("conversation.html", form=form, conversation=conv,
                            receiver=receiver)


@app.route("/create/organization", methods=['GET', 'POST'])
@login_required
def create_org():
    """
    Create organization.
    """
    form = CreateOrg()
    msg = ""
    if request.method == "POST":
        new_org = Organization(name=form.name.data, admin_id=current_user.id)
        db.session.add(new_org)
        db.session.commit()

        folder = Folder(organization_id=new_org.id,
                        top=True)
        db.session.add(folder)

        org_member = OrganizationMember(organization_id=new_org.id,
                                        user_id=current_user.id,
                                        accepted=True,
                                        rank=100)
        db.session.add(org_member)
        db.session.commit()
        msg = "Organization created successfully!"
        # Should redirect to add members page, but that's not created yet :(
        return redirect(url_for('display_org', org_id=new_org.id))

    return render_template("create_org.html", form=form, msg=msg)


# Make sure a user has permissions to view the org
@app.route("/organization/<int:org_id>/display")
@require_org_member
def display_org(org_id):
    """
    Display home page for an organization.
    """
    # for now lets just display members and files.
    organization = Organization.query.filter_by(id=org_id).first()
    members = OrganizationMember.query.filter_by(
                                        organization_id=org_id,
                                        accepted=True
                                    ).all()
    files = File.query.filter_by(
                            organization_id=org_id
                        ).order_by(
                            File.upload_date.desc()
                ).all()
    num_files = 5 if len(files) > 5 else len(files)

    # Grab 5 most recent files
    recent_files = files[:num_files]

    # Get all folders
    folders = Folder.query.filter_by(
                            organization_id=org_id,
                            top=False
                        ).all()
    print folders

    return render_template("display_org.html", organization=organization,
                            members=members, recent_files=recent_files,
                            folders=folders)


@app.route('/organization/<int:organization_id>' +
            '/term/<path:term>/folder/<path:folder>')
def display_files(organization_id, term="", folder=""):
    """
    Returns all files for a given folder.
    """
    print folder
    course_tag = folder.split(" ")[0]
    course_id = folder.split(" ")[1]

    files = File.query.filter_by(
                        organization_id=organization_id,
                        course_tag=course_tag,
                        course_id=course_id
                    ).order_by(
                            File.upload_date.desc()
                    ).all()

    files = filter(lambda x: x.folder.name == term, files)

    return render_template("files.html", folder=folder,
                            files=files, organization_id=organization_id)


@app.route('/uploads/<int:file_id>', methods=['GET', 'POST'])
def download(file_id):
    """
    Sends an uploaded file from the 'uploads' directory.
    """
    f = File.query.filter_by(id=file_id).first()
    return send_from_directory(f.full_path, f.file_name, as_attachment=True)


@app.route('/organization/<int:organization_id>/folder/<int:folder_id>')
def get_folder(organization_id, folder_id):
    """
    Displays a folder and it's contents.
    """
    organization = Organization.query.filter_by(id=organization_id).first()
    folder = Folder.query.filter_by(id=folder_id).first()
    course_folders_dup = [file.course_folder for file in folder.files]
    print course_folders_dup
    # remove duplicates with set, then convert back to list.
    course_folders_uniq = list(set(course_folders_dup))

    print course_folders_uniq
    return render_template('folder.html', folder=folder,
                            course_folders=course_folders_uniq,
                            organization=organization)


@app.route("/")
def home():
    """
    Index/Home page.
    """
    return render_template("home.html")


@app.route("/me/invites", methods=['GET', 'POST'])
@login_required
def handle_invites():
    """
    Show the organizations you have pending invites for.
    """
    if request.method == "POST":
        print "wtf"
        print "hi"
        org_id = request.form.get('accept') or request.form.get('deny')
        if not org_id:
            return no_perms("That invite doesn't exist!")
        org_member_req = OrganizationMember.query.filter_by(
                                                    organization_id=org_id,
                                                    user_id=current_user.id
                                                ).first()
        if request.form.get('accept'):
            org_member_req.accept()
        elif request.form.get('deny'):
            org_member_req.deny()

    orgs = OrganizationMember.query.filter_by(
                                        user_id=current_user.id,
                                        accepted=False
                                    ).all()

    return render_template("my_invites.html", orgs=orgs)


#TODO: Sort most recent conversations to first
#TODO: Add in unread messages
@app.route("/inbox", methods=['GET'])
@login_required
def inbox():
    """
    Shows an inbox of messages for the currently logged in user.
    """
    unsorted_conversations = Conversation.query.filter_by(
                                            sender_id=g.user.id
                                        ).all() + \
                                Conversation.query.filter_by(
                                            receiver_id=g.user.id
                                        ).all()

    if unsorted_conversations:
        conversations = []
        for conv in unsorted_conversations:
            if conv.receiver_id == g.user.id:
                conv.otherperson = User.query.filter_by(
                                            id=conv.sender_id
                                        ).first()
            else:
                conv.otherperson = User.query.filter_by(
                                            id=conv.receiver_id
                                        ).first()
            conversations.append(conv)

        conversations.sort(key=lambda r: r.messages[len(r.messages)-1].sent_at)
        return render_template('inbox.html', conversations=conversations)

    return no_perms("You do not have any conversations!")


@app.route("/me/organizations")
@login_required
def my_orgs():
    """
    Show the organizations you are a part of, and an administrator for.
    """
    orgs = current_user.organizations()
    admin_orgs = filter(lambda org: org.admin_id == current_user.id, orgs)
    member_orgs = filter(lambda org: org.admin_id != current_user.id, orgs)

    return render_template("my_orgs.html", admin_orgs=admin_orgs,
                           member_orgs=member_orgs)


#TODO: Make this exclusively no_perms, and fix templates to use flashed text
@app.route("/no_perms")
def no_perms(msg):
    """
    Error message page. Name for this function and template should be changed.
    """
    return render_template("message.html",  msg=msg)


@app.route("/login", methods=['GET', 'POST'])
def login():
    """
    Login page/handle.
    """
    form = LoginForm(request.form, csrf_enabled=False)
    if g.user.is_anonymous():
        if request.method == "POST" and form.validate_on_submit():

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
    """
    Logs a user out.
    """
    logout_user()
    flash("Logged out successfully!")
    return redirect("/")


@app.route("/register", methods=['GET', 'POST'])
def register():
    """
    Register a User.
    """
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


@app.route("/search", methods=['GET', 'POST'])
def search():
    """
    Search the db for files.
    * Should be search for files from orgs we are a part of? Idk.
    Will search:
        - Organization (All files for organization)
        - Term
        - Class
        - File name
    """

    if not request.method == "POST" or not request.form.get('search'):
        return no_perms("You need to provide a term to search for!")

    my_orgs = OrganizationMember.query.filter_by(
                                        user_id=current_user.id,
                                        accepted=True
                                    ).all()
    my_org_ids = [org.organization_id for org in my_orgs]

    term = request.form.get('search')
    results = []

    # Check organizations
    organizations = Organization.query.filter(
                            Organization.name.like("%" + term + "%")
                        ).all()

    if organizations:
        org_ids = [org.id for org in organizations]
        for org_id in org_ids:
            if org_id in my_org_ids:
                files = File.query.filter_by(organization_id=org_id).all()
                results += files

    temp_term = term.replace(" ", "").lower()

    # Check terms
    folders = Folder.query.filter(Folder.organization_id.in_(my_org_ids)).all()
    for folder in folders:
        if folder.name.replace(" ", "").lower() == temp_term:
            results += folder.files

    # Check files classes matches
    all_files =  File.query.filter_by(organization_id=2).all()
    relevant_files = File.query.filter(File.organization_id.in_(my_org_ids)).all()
    for file in relevant_files:
        if file.course_folder.replace(" ", "").lower() == temp_term:
            results += [file]

    # Check file names similar
    temp_term = term.split(' ') or term
    for t in temp_term:
        relevant_files = File.query.filter(
                                    and_(File.organization_id.in_(my_org_ids),
                                         File.file_name.like("%" + t + "%"))
                                ).all()
        results += relevant_files if relevant_files else []

    results = list(set(results))

    if results:
        return render_template('search.html', results=results, term=term)
    else:
        return no_perms("No results found...")


@login_required
@app.route('/organization/<int:org_id>/upload', methods=['GET', 'POST'])
def upload_file(org_id):
    """
    Allows an organization member to upload a file for an organization.
    """
    form = FileForm()

    organization = Organization.query.filter_by(id=org_id).first()

    if request.method == "POST":
        file = request.files['file']

        if (file and allowed_file(file.filename) and form.course_id.data and
            request.form.get('date')):

            exists = Folder.query.filter_by(
                                    organization_id=org_id,
                                    term=form.term.data,
                                    year=form.year.data
                                ).first()
            folder_id = 0
            if exists:
                folder_id = exists.id
            else:
                folder = Folder(organization_id=organization.id,
                                top=False,
                                term=form.term.data,
                                year=form.year.data)
                db.session.add(folder)
                db.session.commit()
                folder_id = folder.id

            # Parse date and create a datetime object
            date_inp = map(int, request.form['date'].split('/'))
            month = date_inp[0]
            day = date_inp[1]
            year = date_inp[2]
            date = datetime.datetime(year, month, day, 0, 0, 0)

            filename = secure_filename(file.filename)
            f = File(file_name=filename, author_id=g.user.id,
                     organization_id=org_id, folder_id=folder_id,
                     course_tag=form.course_tag.data,
                     course_id=form.course_id.data,
                     class_date=date)

            db.session.add(f)
            db.session.commit()

            file.save(f.full_path + f.file_name)
            return redirect(url_for('display_org', org_id=org_id))
    else:
        return render_template('upload.html', form=form,
                                organization=organization)
