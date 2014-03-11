from gtb import app, db
from gtb.models import Category
from bs4 import BeautifulSoup
from urllib2 import urlopen
import re

db.create_all()

# Add course categories via BeautifulSoup scraping
tags = dict((x[0], True) for x in db.session.query(Category.tag).all())

if not tags.get("None"):
    db.session.add(Category("None"))
    db.session.commit()

html = urlopen('http://catalog.oregonstate.edu/CourseDescription.aspx?level=undergrad').read()
soup = BeautifulSoup(html)
table = soup.find(id='ctl00_ContentPlaceHolder1_dlSubjects')
cats_text = table.find_all('a')
cat_re = re.compile(r'.+\((.+)\).*')

for a in cats_text:
    if not a.text.startswith('OS/'):
        match = cat_re.match(a.text)
        if match:
            tag = match.groups()[0].upper()
            print tag
            if not tags.get(tag):
                print "adding tag {0}".format(tag)
                db.session.add(Category(tag))
                db.session.commit()

