import os
_basedir = os.path.abspath(os.path.dirname(__file__))

#use 'dev', 'test', or 'production'
DATABASE_TYPE = 'test'

DEBUG = False

SECRET_KEY = "ay98r0u2q9305jr2or@QTG%#QH^KWTRTGrqy43"
UPLOAD_FOLDER = "/var/www/xmls"

if DATABASE_TYPE == 'test' or DATABASE_TYPE == 'dev':
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'db/gtb.db')
elif DATABASE_TYPE == 'prod':
    SQLALCHEMY_DATABASE_URI = 'mysql://user:pass@localhost/dbname'
else:
    raise NameError('The value used for DATABASE_TYPE is not an accepted value.')
DATABASE_CONNECT_OPTIONS = {}

CSRF_ENABLED = True
CSRF_SESSION_KEY="aser43wAG$#WAg43WAY$JH%j%$KJW%$uWA$5eYaEgsahsu"

SQLALCHEMY_MIGRATE_REPO = os.path.join(_basedir, 'migrations')
