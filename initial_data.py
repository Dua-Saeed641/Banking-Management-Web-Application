import os
from app import app
from application.database import db
from application.models import Admin
from werkzeug.security import generate_password_hash, check_password_hash

with app.app_context():
    db.create_all()

    admin_email = os.getenv("ADMIN_EMAIL", "admin@gmail.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

    admin = Admin.query.filter_by(
        admin_email=admin_email
    ).first()

    if admin is None:
        admin = Admin(
            admin_name="Admin",
            admin_email=admin_email,
            admin_password=generate_password_hash(admin_password),
            is_active=True
        )

        db.session.add(admin)
        db.session.commit()

        print(f"Admin ({admin_email}) created successfully.")
    else:
        print(f"Admin ({admin_email}) already exists.")
        print("Active:", admin.is_active)
        print(
            "Password match:",
            check_password_hash(admin.admin_password, admin_password)
        )