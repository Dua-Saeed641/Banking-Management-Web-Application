import os
from flask import Flask
from .config import Config
from .database import db

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

app.config.from_object(Config)

db.init_app(app)

from application import controllers