from app import app
from application.database import db
from application.models import Admin
from werkzeug.security import generate_password_hash, check_password_hash

with app.app_context():
    db.create_all()

    admin = Admin.query.filter_by(
        admin_email="admin@gmail.com"
    ).first()

    if admin is None:
        admin = Admin(
            admin_name="Admin",
            admin_email="admin@gmail.com",
            admin_password=generate_password_hash("admin123"),
            is_active=True
        )

        db.session.add(admin)
        db.session.commit()

        print("Admin created successfully.")

    else:
        print("Admin already exists.")
        print("Email:", admin.admin_email)
        print("Active:", admin.is_active)
        print(
            "Password match:",
            check_password_hash(admin.admin_password, "admin123")
        )