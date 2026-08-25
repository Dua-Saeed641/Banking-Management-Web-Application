from application.database import db
from flask_login import UserMixin
from datetime import datetime 
from datetime import timezone


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
    created_at = db.Column(db.DateTime,default=lambda: datetime.now(timezone.utc))
    assigned_pro_id = db.Column(db.Integer,db.ForeignKey("pros.pro_id"),nullable=True)
    assigned_pro = db.relationship("PRO",backref="customers",foreign_keys=[assigned_pro_id])
    def get_id(self):
        return f"user-{self.user_id}"

    bank_account = db.relationship("BankAccount",backref="user",uselist=False)
    scheme_assignments = db.relationship("UserScheme",backref="user",lazy=True)

class PRO(UserMixin, db.Model):

    __tablename__ = "pros"
    pro_id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    name = db.Column(db.String(100),nullable=False)
    email = db.Column(db.String(120),unique=True,nullable=False)
    password = db.Column(db.String(255),nullable=False)
    employee_code = db.Column(db.String(20),unique=True,nullable=True)
    contact_number = db.Column(db.String(10),nullable=False)
    experience = db.Column(db.Integer,default=0)
    joining_date = db.Column(db.Date,default=lambda: datetime.now(timezone.utc))
    is_approved = db.Column(db.Boolean,default=False)
    is_blacklisted = db.Column(db.Boolean,default=False)
    is_active = db.Column(db.Boolean,default=True)
    def get_id(self):
        return f"pro-{self.pro_id}"

    recommended_schemes = db.relationship("UserScheme",backref="pro",foreign_keys="UserScheme.assigned_by_pro")

class BankAccount(db.Model):
    __tablename__ = "bank_accounts"

    account_id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    user_id = db.Column(db.Integer,db.ForeignKey("users.user_id"),unique=True,nullable=False)
    account_number = db.Column(db.String(20),unique=True,nullable=False)
    account_type = db.Column(db.String(20),nullable=False,default="Savings")
    balance = db.Column(db.Float,nullable=False,default=0.0)
    minimum_balance = db.Column(db.Float,nullable=False,default=1000.0)
    ifsc_code = db.Column(db.String(20),nullable=False)
    opening_date = db.Column(db.Date,default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20),nullable=False,default="Active")
    last_transaction_date = db.Column(db.DateTime,nullable=True)
    scheme_id = db.Column(db.Integer,db.ForeignKey("banking_schemes.scheme_id"),nullable=True)

    transactions = db.relationship("Transaction",backref="account",lazy=True)
    scheme = db.relationship("BankingScheme",backref="accounts")

class Transaction(db.Model):

    __tablename__ = "transactions"

    transaction_id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    account_id = db.Column(db.Integer,db.ForeignKey("bank_accounts.account_id"),nullable=False)
    transaction_type = db.Column(db.String(20),nullable=False)
    amount = db.Column(db.Float,nullable=False)
    balance_after_transaction = db.Column(db.Float,nullable=False)
    transaction_date = db.Column(db.DateTime,default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20),nullable=False,default="Successful")

class BankingScheme(db.Model):

    __tablename__ = "banking_schemes"
    scheme_id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    scheme_name = db.Column(db.String(100),nullable=False)
    description = db.Column(db.Text,nullable=False)
    minimum_balance_required = db.Column(db.Float, nullable=False,default=0.0)
    interest_rate = db.Column(db.Float,nullable=False,default=0.0)
    status = db.Column(db.String(20),nullable=False,default="Active")
    created_at = db.Column(db.DateTime,default=lambda: datetime.now(timezone.utc))

    user_assignments = db.relationship("UserScheme",backref="scheme",lazy=True)

class UserScheme(db.Model):

    __tablename__ = "user_schemes"

    user_scheme_id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    user_id = db.Column(db.Integer,db.ForeignKey("users.user_id"),nullable=False)
    scheme_id = db.Column(db.Integer,db.ForeignKey("banking_schemes.scheme_id"),nullable=False)
    assigned_by_pro = db.Column(db.Integer,db.ForeignKey("pros.pro_id"),nullable=False)
    assigned_date = db.Column(db.DateTime,default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20),nullable=False,default="Pending")

