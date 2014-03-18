from flask.ext.login import current_user

from constants import CURRENT_YEAR
from gtb import app, db, login_manager
from models import Category, OrganizationMember, User

from functools import wraps


"""
Decorators
"""


def is_current_user(f):
    """
    Decorator to require the user to be a member of an organization.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id == kwargs.get('id'):
            return f(*args, **kwargs)
        return no_perms("You can not modify other user's data!")
    return decorated_function


def require_org_member(f):
    """
    Decorator to require the user to be a member of an organization.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if member_of(kwargs.get('org_id')):
            return f(*args, **kwargs)
        return no_perms("You are not a member of this organization!")
    return decorated_function


def require_admin(f):
    """
    Decorator to require the user to be an administrator.
    (Overall, not of an organization)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.admin:
            return f(*args, **kwargs)
        return no_perms("You are not an admin!")
    return decorated_function


"""
Helper Functions
"""


def allowed_file(filename):
    """
    Checks that a file extension exists.
    Should also use a filter against whitelisted extentions.
    """
    return '.' in filename and filename.rsplit('.')


def create_dirs(folder, f=None):
    """
    Creates directiories for either JUST an organization, or
    within an organization for a single file being uploaded.
    """
    path = app.config['UPLOAD_PATH'] + folder.organization_id + '/'
    if not folder.top:
        path += folder.name.replace(' ', '_') + '/'
        if f:
            path += f.course_tag + '_' + f.course_id + '/'
    if not os.exists(path):
        os.makedirs(path)
    else:
        print "Path exists at: {0}".format(path)


def get_tags():
    """
    Returns a sorted list of the tags in the db.
    """
    tags = ['    ']
    tags += [x[0] for x in
                db.session.query(Category.tag).order_by(Category.tag).all()]
    return tags


def get_user():
    """
    A user id is sent in, to check against the session
    and based on the result of querying that id we
    return a user (whether it be a sqlachemy obj or an
    obj named guest
    """

    if 'user_id' in session:
            return User.query.filter_by(id=session["user_id"]).first()
    return None


def get_year_range():
    """
    Returns the year range for 1950 to CURRENT_YEAR.
    """
    return range(1850, CURRENT_YEAR + 1)


@login_manager.user_loader
def load_user(userid):
    return User.query.filter_by(id=userid).first()


def member_of(org_id):
    """
    Returns if the current user is a member of the organization with
    an id of org_id.
    """
    return db.session.query(OrganizationMember).filter_by(
                                        user_id=current_user.id,
                                        organization_id=org_id,
                                        accepted=True
                                ).first()
