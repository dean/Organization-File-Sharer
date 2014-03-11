from constants import CURRENT_YEAR
from gtb import db
from models import Category


def get_year_range():
    """
    Returns the year range for 1950 to CURRENT_YEAR.
    """
    return range(1850, CURRENT_YEAR + 1)


def get_tags():
    """
    Returns a sorted list of the tags in the db.
    """
    tags = ['    ']
    tags += [x[0] for x in
                db.session.query(Category.tag).order_by(Category.tag).all()]
    return tags

