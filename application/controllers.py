from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user,logout_user,login_required,current_user
from app import app

from application.database import db
from application.models import User, BankAccount, PRO, Admin,Transaction

from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime, timezone
import secrets
import string

def generate_account_number():
    while True:
        account_number = ''.join(secrets.choice(string.digits)for i in range(12))
        existing_account = BankAccount.query.filter_by(account_number=account_number).first()
        if existing_account is None:
            return account_number

def validate_password(password):
    if len(password) < 8:
        return False, "Password must contain at least 8 characters."
    upper = 0
    lower = 0
    digit = 0
    special = 0
    for character in password:
        if character.isupper():
            upper += 1
        elif character.islower():
            lower += 1
        elif character.isdigit():
            digit += 1
        elif not character.isalnum() and character != " ":
            special += 1
        elif character == " ":
            return False, "Password must not contain spaces."
    if upper == 0:
        return False, "Password must contain at least one uppercase letter."
    if lower == 0:
        return False, "Password must contain at least one lowercase letter."
    if digit == 0:
        return False, "Password must contain at least one digit."
    if special == 0:
        return False, "Password must contain at least one special character."

    return True, "Password is valid."

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register/pro", methods=["GET", "POST"])
def register_pro():
    if request.method == "GET":
        return render_template("auth/register_pro.html")
    return "PRO registration submitted."

@app.route("/register/user", methods=["GET", "POST"])
def register_user():
    if request.method == "GET":
        return render_template("auth/register_user.html")

    name = request.form["name"].strip()
    email = request.form["email"].strip().lower()
    password = request.form["password"]

    password_valid, password_message = validate_password(password)
    if not password_valid:
        return render_template("auth/register_user.html",name=name,email=email,password_error=password_message)
    
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash("An account with this email already exists.","danger")
        return redirect(url_for("register_user"))
    
    existing_pro = PRO.query.filter_by(email=email).first()
    if existing_pro:
        flash("This email is already registered.","danger")
        return redirect(url_for("register_user"))

    hashed_password = generate_password_hash(password)

    user = User(
        name=name,
        email=email,
        password=hashed_password
    )

    db.session.add(user)
    db.session.flush()
    account_number = generate_account_number()
    bank_account = BankAccount(
        user_id=user.user_id,
        account_number=account_number,
        account_type="Savings",
        balance=0.0,
        minimum_balance=0.0,
        ifsc_code="ATM001",
        status="Active"
    )

    db.session.add(bank_account)
    db.session.commit()

    flash("Registration successful. You can now login.","success")
    return redirect(url_for("login", role="User"))

@app.route("/login/<role>", methods=["GET", "POST"])
def login(role):
    if request.method == "GET":
        return render_template(
            "auth/login.html",
            role=role
        )

    email = request.form["email"].strip().lower()
    password = request.form["password"]

    if role.lower() == "user":
        user = User.query.filter_by(email=email).first()
        if user is None:
            return render_template(
                "auth/login.html",
                role=role,
                login_error="Invalid email or password."
            )
        if not user.is_active:
            return render_template(
                "auth/login.html",
                role=role,
                login_error="Your account has been blacklisted."
            )
        if not check_password_hash(user.password, password):
            return render_template(
                "auth/login.html",
                role=role,
                login_error="Invalid email or password."
            )

        login_user(user)

        return redirect(url_for("user_dashboard"))
    return "Login for this role is not implemented yet."

@app.route("/user/dashboard")
@login_required
def user_dashboard():

    return render_template(
        "user/dashboard.html",
        user=current_user,
        account=current_user.bank_account
    )

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/user/deposit", methods=["GET", "POST"])
@login_required
def deposit():

    if not isinstance(current_user, User):
        return "Unauthorized", 403

    account = current_user.bank_account
    if account is None:
        return "Bank account not found.", 404

    if request.method == "GET":
        return render_template(
            "user/deposit.html",
            account=account
        )

    amount = request.form.get("amount")
    try:
        amount = float(amount)
    except (TypeError, ValueError):

        return render_template(
            "user/deposit.html",
            account=account,
            deposit_error="Please enter a valid amount."
        )

    if amount <= 0:
        return render_template(
            "user/deposit.html",
            account=account,
            deposit_error="Deposit amount must be greater than zero."
        )

    if account.status != "Active":
        return render_template(
            "user/deposit.html",
            account=account,
            deposit_error="Deposits are allowed only on active accounts."
        )

    account.balance += amount
    transaction = Transaction(
        account_id=account.account_id,
        transaction_type="Deposit",
        amount=amount,
        balance_after_transaction=account.balance,
        status="Successful"
    )

    account.last_transaction_date = datetime.now(timezone.utc)

    db.session.add(transaction)
    db.session.commit()

    return redirect(url_for("user_dashboard"))