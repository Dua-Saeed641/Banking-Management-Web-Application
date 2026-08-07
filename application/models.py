#1 designing models before writing any controllers, to have full knowledge of each entity
#User--1:1-->BankAccount,PROProfile

from application.database import db
from flask_login import UserMixin
from datetime import datetime 


class Admin(UserMixin, db.Model):

    __tablename__ = "admin"
    admin_id = db.Column(db.Integer,primary_key=True, autoincrement=True)
    admin_name=db.Column(db.String(100), nullable=False)
    admin_email=db.Column(db.String(100),unique=True, nullable=False)
    admin_password = db.Column(db.String(255),nullable=False)
    is_active=db.Column(db.Boolean, default=True)
    def get_id(self):
        return f"admin-{self.admin_id}"

class User(UserMixin, db.Model):

    __tablename__ = "users"
    user_id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    name = db.Column(db.String(100),nullable=False)
    email = db.Column(db.String(120),unique=True,nullable=False)
    password = db.Column(db.String(255),nullable=False)
    is_active = db.Column(db.Boolean,default=True)
    created_at = db.Column(db.DateTime,default=datetime.utcnow)
    def get_id(self):
        return f"user-{self.user_id}"

class PRO(UserMixin, db.Model):

    __tablename__ = "pros"
    pro_id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    name = db.Column(db.String(100),nullable=False)
    email = db.Column(db.String(120),unique=True,nullable=False)
    password = db.Column(db.String(255),nullable=False)
    employee_code = db.Column(db.String(20),unique=True,nullable=False)
    contact_number = db.Column(db.integer(12))
    experience = db.Column(db.Integer,default=0)
    joining_date = db.Column(db.Date,default=datetime.utcnow)
    is_approved = db.Column(db.Boolean,default=False)
    is_blacklisted = db.Column(db.Boolean,default=False)
    is_active = db.Column(db.Boolean,default=True)
    def get_id(self):
        return f"pro-{self.pro_id}"