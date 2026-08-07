from app import app
from application.database import db
from application.models import Admin


with app.app_context():
    db.create_all()
    admin = Admin.query.filter_by(admin_email="admin@gmail.com").first()

    if admin is None:
        admin = Admin(admin_name="Admin", admin_email="admin@gmail.com",admin_password="admin123", is_active=True)
        db.session.add(admin)
        db.session.commit()
        print("Default Admin created successfully.")
    else:
        print("Admin already exists.")