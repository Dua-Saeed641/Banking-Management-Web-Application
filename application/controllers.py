from app import app
from flask import render_template,request

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    role = request.args.get("role")
    return render_template("auth/login.html",role=role)

@app.route("/register/pro", methods=["GET", "POST"])
def register_pro():
    if request.method == "GET":
        return render_template("auth/register_pro.html")
    return "PRO registration submitted."

@app.route("/register/user", methods=["GET", "POST"])
def register_user():
    if request.method == "GET":
        return render_template("auth/register_user.html")
    return "User registration submitted."