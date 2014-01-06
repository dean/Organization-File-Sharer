from flask import Flask, render_template, g
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
import sqlite3

app = Flask(__name__)
app.config.from_object('config')

login_manager = LoginManager()
login_manager.setup_app(app)

db = SQLAlchemy(app)
db.init_app(app)

import models, views
