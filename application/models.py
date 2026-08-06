#1 designing models before writing any controllers, to have full knowledge of each entity
#User--1:1-->BankAccount,PROProfile

from application.database import db
from flask_login import UserMixin


class User(UserMixin, db.Model):

    __tablename__ = "users"

    user_id = db.Column(
        db.Integer,
        primary_key=True
    )