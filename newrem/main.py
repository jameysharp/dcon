import os

from flask import Flask
from flaskext.login import LoginManager

wd = os.getcwd()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s/temp.db" % wd
app.config["SECRET_KEY"] = "just a test!"
app.config["UPLOADS_DEFAULT_DEST"] = os.path.join(wd, "uploads")

lm = LoginManager()
lm.setup_app(app)
