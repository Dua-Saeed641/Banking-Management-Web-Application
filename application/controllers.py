from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user,logout_user,login_required,current_user
from app import app
from functools import wraps
from application.database import db
from application.models import User, BankAccount, PRO, Admin,Transaction, BankingScheme, UserScheme

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

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not isinstance(current_user, Admin):
            return "Unauthorized", 403
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def home():
    return render_template("home.html")

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
        ifsc_code="ATM001",
        status="Active"
    )

    db.session.add(bank_account)
    db.session.commit()

    flash("Registration successful. You can now login.","success")
    return redirect(url_for("login", role="User"))

@app.route("/register/pro", methods=["GET", "POST"])
def register_pro():
    if request.method == "GET":
        return render_template("auth/register_pro.html")

    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    contact_number = request.form.get("contact_number")
    experience = request.form.get("experience")

    password_valid, password_message = validate_password(password)
    if not password_valid:
        return render_template("auth/register_pro.html",name=name,email=email,contact_number=contact_number,experience=experience,password_error=password_message)

    if not contact_number.isdigit() or len(contact_number) != 10:
        flash("Contact number must contain exactly 10 digits.","danger")
        return render_template("auth/register_pro.html",name=name,email=email,contact_number=contact_number,experience=experience)

    existing_email = PRO.query.filter_by(email=email).first()
    if existing_email:
        flash("An account with this email already exists.","danger")
        return render_template("auth/register_pro.html",name=name,email=email,contact_number=contact_number,experience=experience)
    
    new_pro = PRO(
        name=name,
        email=email,
        password=generate_password_hash(password),
        contact_number=contact_number,
        experience=int(experience or 0),
        is_approved=False,
        is_blacklisted=False,
        is_active=True
    )

    db.session.add(new_pro)
    db.session.commit()

    flash("Registration successful. Your account is awaiting admin approval.","success")
    return redirect(url_for("login", role="pro"))

@app.route("/login/<role>", methods=["GET", "POST"])
def login(role):
    role=role.lower()
    if request.method == "GET":
        return render_template("auth/login.html",role=role)

    email = request.form["email"].strip().lower()
    password = request.form["password"]
#Admin login
    if role.lower() == "admin":
        admin = Admin.query.filter_by(admin_email=email).first()

        if admin and check_password_hash(admin.admin_password,password):
            if not admin.is_active:
                flash("Admin account is inactive.", "danger")
                return redirect(url_for("login", role="Admin"))

            login_user(admin)
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin email or password.", "danger")
        return redirect(url_for("login", role="admin"))

#PRO login
    if role == "pro":
        pro = PRO.query.filter_by(email=email).first()

        if pro is None or not check_password_hash(pro.password, password):
            return render_template("auth/login.html",role=role,login_error="Invalid email or password.")

        if not pro.is_approved:
            return render_template("auth/login.html",role=role,login_error="Your PRO account is awaiting admin approval.")

        if pro.is_blacklisted:
            return render_template("auth/login.html",role=role,login_error="Your PRO account has been blacklisted.")

        if not pro.is_active:
            return render_template("auth/login.html",role=role,login_error="Your PRO account is inactive.")

        login_user(pro)

        return redirect(url_for("pro_dashboard"))
#user login
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

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    return render_template("admin/dashboard.html")

@app.route("/admin/users")
@login_required
def admin_users():
    if not isinstance(current_user, Admin):
        return "Unauthorized", 403

    users = User.query.all()
    pros = PRO.query.all()

    return render_template("admin/users.html",users=users,pros=pros)

@app.route("/admin/schemes")
@admin_required
def admin_schemes():
    schemes = BankingScheme.query.all()
    return render_template("admin/schemes.html", schemes=schemes)

@app.route("/admin/schemes/add", methods=["GET", "POST"])
@admin_required
def add_scheme():
    if request.method == "GET":
        return render_template("admin/add_scheme.html")

    scheme_name = request.form["scheme_name"].strip()
    description = request.form["description"].strip()
    minimum_balance = request.form["minimum_balance"]
    interest_rate = request.form["interest_rate"]

    if not scheme_name or not description:
        flash("Please fill in all required fields.", "danger")
        return redirect(url_for("add_scheme"))

    scheme = BankingScheme(
        scheme_name=scheme_name,
        description=description,
        minimum_balance_required=float(minimum_balance),
        interest_rate=float(interest_rate),
        status="Active"
    )

    db.session.add(scheme)
    db.session.commit()

    flash("Banking scheme added successfully.", "success")
    return redirect(url_for("admin_schemes"))

@app.route("/admin/schemes/<int:scheme_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_scheme(scheme_id):
    scheme = BankingScheme.query.get_or_404(scheme_id)

    if request.method == "GET":
        return render_template("admin/edit_scheme.html", scheme=scheme)

    scheme.scheme_name = request.form["scheme_name"].strip()
    scheme.description = request.form["description"].strip()
    scheme.minimum_balance_required = float(request.form["minimum_balance"])
    scheme.interest_rate = float(request.form["interest_rate"])

    db.session.commit()

    flash("Banking scheme updated successfully.", "success")
    return redirect(url_for("admin_schemes"))

@app.route("/admin/schemes/<int:scheme_id>/toggle", methods=["POST"])
@admin_required
def toggle_scheme(scheme_id):
    scheme = BankingScheme.query.get_or_404(scheme_id)

    if scheme.status == "Active":
        scheme.status = "Inactive"
        flash("Banking scheme deactivated.", "success")
    else:
        scheme.status = "Active"
        flash("Banking scheme activated.", "success")

    db.session.commit()
    return redirect(url_for("admin_schemes"))

@app.route("/admin/users/<int:user_id>/assign-pro", methods=["POST"])
@login_required
def assign_pro(user_id):
    if not isinstance(current_user, Admin):
        return "Unauthorized", 403

    user = User.query.get_or_404(user_id)

    pro_id = request.form.get("pro_id")

    if not pro_id:
        flash("Please select a PRO.", "danger")
        return redirect(url_for("admin_users"))

    pro = PRO.query.get_or_404(pro_id)

    if not pro.is_approved:
        flash("This PRO is not approved.", "danger")
        return redirect(url_for("admin_users"))

    if pro.is_blacklisted or not pro.is_active:
        flash("This PRO is inactive or blacklisted.", "danger")
        return redirect(url_for("admin_users"))

    user.assigned_pro_id = pro.pro_id
    db.session.commit()

    flash("PRO assigned successfully.", "success")
    return redirect(url_for("admin_users"))

@app.route("/admin/users/<int:user_id>/blacklist", methods=["POST"])
@admin_required
def blacklist_user(user_id):
    user = User.query.get_or_404(user_id)

    user.is_active = False
    db.session.commit()

    flash("User has been blacklisted.", "success")
    return redirect(url_for("admin_users"))

@app.route("/admin/users/<int:user_id>/activate", methods=["POST"])
@admin_required
def activate_user(user_id):
    user = User.query.get_or_404(user_id)

    user.is_active = True
    db.session.commit()

    flash("User has been activated.", "success")
    return redirect(url_for("admin_users"))

@app.route("/user/dashboard")
@login_required
def user_dashboard():
    if not isinstance(current_user, User):
        return "Unauthorized", 403

    account = current_user.bank_account

    if account is None:
        return "Bank account not found.", 404

    return render_template(
        "user/dashboard.html",
        user=current_user,
        account=account
    )

@app.route("/pro/dashboard")
@login_required
def pro_dashboard():
    if not isinstance(current_user, PRO):
        return "Unauthorized", 403

    if current_user.is_blacklisted:
        logout_user()
        return "Your PRO account has been blacklisted.", 403

    if not current_user.is_active:
        logout_user()
        return "Your PRO account is inactive.", 403

    if not current_user.is_approved:
        logout_user()
        return "Your PRO account is not approved.", 403

    return render_template(
        "pro/dashboard.html",
        pro=current_user
    )

@app.route("/pro/customers")
@login_required
def pro_customers():
    if not isinstance(current_user, PRO):
        return "Unauthorized", 403

    customers = User.query.filter_by(
        assigned_pro_id=current_user.pro_id,
        is_active=True
    ).all()

    return render_template("pro/customers.html", customers=customers)


@app.route("/pro/customers/<int:user_id>")
@login_required
def pro_customer_details(user_id):
    if not isinstance(current_user, PRO):
        return "Unauthorized", 403

    user = User.query.filter_by(
        user_id=user_id,
        assigned_pro_id=current_user.pro_id,
        is_active=True
    ).first_or_404()

    schemes = BankingScheme.query.filter_by(status="Active").all()

    return render_template("pro/customer_details.html", user=user, schemes=schemes)


@app.route("/pro/customers/<int:user_id>/recommend-scheme", methods=["POST"])
@login_required
def recommend_scheme(user_id):
    if not isinstance(current_user, PRO):
        return "Unauthorized", 403

    user = User.query.filter_by(
        user_id=user_id,
        assigned_pro_id=current_user.pro_id,
        is_active=True
    ).first_or_404()

    if not user.bank_account:
        flash("Customer does not have a bank account.", "danger")
        return redirect(url_for("pro_customer_details", user_id=user.user_id))

    scheme_id = request.form.get("scheme_id")

    if not scheme_id:
        flash("Please select a scheme.", "danger")
        return redirect(url_for("pro_customer_details", user_id=user.user_id))

    scheme = BankingScheme.query.filter_by(
        scheme_id=scheme_id,
        status="Active"
    ).first()

    if not scheme:
        flash("Invalid or inactive scheme.", "danger")
        return redirect(url_for("pro_customer_details", user_id=user.user_id))

    if user.bank_account.balance < scheme.minimum_balance_required:
        flash(
            f"Customer is not eligible for {scheme.scheme_name}. "
            f"Minimum balance required is ₹{scheme.minimum_balance_required:.2f}.",
            "danger"
        )
        return redirect(url_for("pro_customer_details", user_id=user.user_id))

    recommendation = UserScheme(
        user_id=user.user_id,
        scheme_id=scheme.scheme_id,
        assigned_by_pro=current_user.pro_id,
        status="Pending"
    )

    db.session.add(recommendation)
    db.session.commit()

    flash(f"{scheme.scheme_name} recommended successfully.", "success")

    return redirect(url_for("pro_customer_details", user_id=user.user_id))

@app.route("/pro/recommendations")
@login_required
def pro_recommendations():
    if not isinstance(current_user, PRO):
        return "Unauthorized", 403

    recommendations = UserScheme.query.filter_by(
        assigned_by_pro=current_user.pro_id
    ).all()

    return render_template("pro/recommendations.html",recommendations=recommendations)

@app.route("/pro/customers/<int:user_id>/transactions")
@login_required
def pro_customer_transactions(user_id):
    if not isinstance(current_user, PRO):
        return "Unauthorized", 403

    user = User.query.filter_by(
        user_id=user_id,
        assigned_pro_id=current_user.pro_id,
        is_active=True
    ).first_or_404()

    if not user.bank_account:
        flash("Customer does not have a bank account.", "danger")
        return redirect(url_for("pro_customer_details", user_id=user.user_id))

    transactions = Transaction.query.filter_by(
        account_id=user.bank_account.account_id
    ).order_by(Transaction.transaction_date.desc()).all()

    return render_template("pro/customer_transactions.html",user=user, transactions=transactions)

@app.route("/pro/customers/<int:user_id>/account-status", methods=["POST"])
@login_required
def pro_update_account_status(user_id):
    if not isinstance(current_user, PRO):
        return "Unauthorized", 403

    user = User.query.filter_by(
        user_id=user_id,
        assigned_pro_id=current_user.pro_id,
        is_active=True
    ).first_or_404()

    if not user.bank_account:
        flash("Customer does not have a bank account.", "danger")
        return redirect(url_for("pro_customer_details", user_id=user.user_id))

    status = request.form.get("status")

    if status not in ["Active", "Blocked", "Closed"]:
        flash("Invalid account status.", "danger")
        return redirect(url_for("pro_customer_details", user_id=user.user_id))

    user.bank_account.status = status
    db.session.commit()

    flash(f"Account status changed to {status}.", "success")
    return redirect(url_for("pro_customer_details", user_id=user.user_id))

@app.route("/admin/pro-request")
@admin_required
def pro_requests():
    pros = PRO.query.filter_by(is_approved=False, is_blacklisted=False).all()
    return render_template("admin/pro_request.html", pros=pros)

@app.route("/admin/pro-requests/<int:pro_id>/approve", methods=["POST"])
@admin_required
def approve_pro(pro_id):
    pro = PRO.query.get_or_404(pro_id)

    if pro.is_approved:
        flash("PRO is already approved.", "danger")
        return redirect(url_for("pro_requests"))

    last_pro = PRO.query.filter(PRO.employee_code.isnot(None)).order_by(PRO.pro_id.desc()).first()

    if last_pro and last_pro.employee_code:
        number = int(last_pro.employee_code.replace("EMP", "")) + 1
    else:
        number = 1

    pro.employee_code = f"EMP{number:03d}"
    pro.is_approved = True
    pro.is_blacklisted = False

    db.session.commit()

    flash(f"PRO approved successfully. Employee Code: {pro.employee_code}", "success")
    return redirect(url_for("pro_requests"))

@app.route("/admin/pro-requests/<int:pro_id>/blacklist", methods=["POST"])
@admin_required
def blacklist_pro(pro_id):
    pro = PRO.query.get_or_404(pro_id)

    pro.is_blacklisted = True
    pro.is_approved = False

    db.session.commit()

    flash("PRO has been blacklisted.", "success")
    return redirect(url_for("pro_requests"))

@app.route("/admin/pros")
@login_required
def manage_pros():
    if not isinstance(current_user, Admin):
        return "Unauthorized", 403

    pros = PRO.query.order_by(PRO.pro_id.desc()).all()

    return render_template("admin/manage_pros.html", pros=pros)

@app.route("/admin/pros/<int:pro_id>/customers")
@login_required
def admin_pro_customers(pro_id):
    if not isinstance(current_user, Admin):
        return "Unauthorized", 403

    pro = PRO.query.get_or_404(pro_id)

    customers = User.query.filter_by(
        assigned_pro_id=pro.pro_id
    ).all()

    return render_template(
        "admin/pro_customers.html",
        pro=pro,
        customers=customers
    )

@app.route("/admin/pros/<int:pro_id>/toggle-blacklist", methods=["POST"])
@login_required
def toggle_pro_blacklist(pro_id):
    if not isinstance(current_user, Admin):
        return "Unauthorized", 403

    pro = PRO.query.get_or_404(pro_id)

    pro.is_blacklisted = not pro.is_blacklisted

    db.session.commit()

    return redirect(url_for("manage_pros"))

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

@app.route("/user/withdraw", methods=["GET", "POST"])
@login_required
def user_withdraw():

    if not isinstance(current_user, User):
        return "Unauthorized", 403

    if not current_user.bank_account:
        flash("No bank account found.", "danger")
        return redirect(url_for("user_dashboard"))

    account = current_user.bank_account

    if account.status != "Active":
        flash("Withdrawals are not allowed on an inactive account.", "danger")
        return redirect(url_for("user_dashboard"))

    if account.scheme and account.scheme.status == "Active":
        effective_minimum = account.scheme.minimum_balance_required
    else:
        effective_minimum = account.minimum_balance

    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", 0))
        except ValueError:
            amount = 0

        if amount <= 0:
            flash("Enter a valid withdrawal amount.", "danger")
            return redirect(url_for("user_withdraw"))

        if account.balance - amount < effective_minimum:
            flash(
                f"Withdrawal denied. Minimum balance of ₹{effective_minimum:.2f} must be maintained.",
                "danger"
            )
            return redirect(url_for("user_withdraw"))

        account.balance -= amount
        account.last_transaction_date = datetime.now(timezone.utc)

        transaction = Transaction(
            account_id=account.account_id,
            transaction_type="Withdrawal",
            amount=amount,
            balance_after_transaction=account.balance,
            status="Successful"
        )

        db.session.add(transaction)
        db.session.commit()

        flash("Amount withdrawn successfully.", "success")
        return redirect(url_for("transaction_history"))

    return render_template(
        "user/withdraw.html",
        account=account,
        effective_minimum=effective_minimum
    )


@app.route("/user/transactions")
@login_required
def transaction_history():

    if not isinstance(current_user, User):
        return "Unauthorized", 403

    account = current_user.bank_account
    if account is None:
        return "Bank account not found.", 404

    transactions = Transaction.query.filter_by(
        account_id=account.account_id
    ).order_by(
        Transaction.transaction_date.desc()
    ).all()
    
    return render_template(
        "user/transactions.html",
        account=account,
        transactions=transactions
    )

@app.route("/user/schemes")
@login_required
def user_schemes():
    if not isinstance(current_user, User):
        return "Unauthorized", 403

    active = UserScheme.query.filter_by(
        user_id=current_user.user_id,
        status="Accepted"
    ).first()

    pending = UserScheme.query.filter_by(
        user_id=current_user.user_id,
        status="Pending"
    ).order_by(UserScheme.assigned_date.desc()).all()

    history = UserScheme.query.filter(
        UserScheme.user_id == current_user.user_id,
        UserScheme.status.in_(["Replaced", "Rejected"])
    ).order_by(UserScheme.assigned_date.desc()).all()

    return render_template(
        "user/schemes.html",
        active=active,
        pending=pending,
        history=history
    )

@app.route("/user/schemes/<int:user_scheme_id>/accept", methods=["POST"])
@login_required
def accept_scheme(user_scheme_id):
    if not isinstance(current_user, User):
        return "Unauthorized", 403

    recommendation = UserScheme.query.filter_by(
        user_scheme_id=user_scheme_id,
        user_id=current_user.user_id,
        status="Pending"
    ).first_or_404()

    account = current_user.bank_account

    if account is None:
        flash("Bank account not found.", "danger")
        return redirect(url_for("user_schemes"))

    scheme = recommendation.scheme

    if account.balance < scheme.minimum_balance_required:
        flash(
            f"You cannot accept {scheme.scheme_name}. Your current balance does not meet the minimum balance requirement.",
            "danger"
        )
        return redirect(url_for("user_schemes"))

    previous = UserScheme.query.filter_by(
        user_id=current_user.user_id,
        status="Accepted"
    ).first()

    if previous:
        previous.status = "Replaced"

    recommendation.status = "Accepted"

    account.scheme_id = scheme.scheme_id

    db.session.commit()

    flash(f"{scheme.scheme_name} is now your active banking scheme.", "success")
    return redirect(url_for("user_schemes"))


@app.route("/user/schemes/<int:user_scheme_id>/reject", methods=["POST"])
@login_required
def reject_scheme(user_scheme_id):
    if not isinstance(current_user, User):
        return "Unauthorized", 403

    recommendation = UserScheme.query.filter_by(
        user_scheme_id=user_scheme_id,
        user_id=current_user.user_id,
        status="Pending"
    ).first_or_404()

    recommendation.status = "Rejected"
    db.session.commit()

    flash("Scheme recommendation rejected.", "info")
    return redirect(url_for("user_schemes"))

