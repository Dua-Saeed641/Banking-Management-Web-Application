import os

from flask import Flask

from application.config import (
    LocalDevelopmentConfig,
    ProductionConfig
)
from application.database import db, login_manager
from application.models import Admin, PRO, User


def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    environment = os.getenv("ENV", "development")

    if environment == "production":
        print("Starting Production...")
        app.config.from_object(ProductionConfig)
    else:
        print("Starting Local Development...")
        app.config.from_object(LocalDevelopmentConfig)

    app.secret_key = app.config.get(
        "SECRET_KEY",
        os.getenv("SECRET_KEY", "local-development-secret-key")
    )

    db.init_app(app)
    login_manager.init_app(app)

    return app


app = create_app()


@login_manager.user_loader
def load_user(user_id):
    try:
        role, actual_id = user_id.split("-")

        if role == "admin":
            return db.session.get(Admin, int(actual_id))
        elif role == "pro":
            return db.session.get(PRO, int(actual_id))
        elif role == "user":
            return db.session.get(User, int(actual_id))
    except (ValueError, TypeError):
        return None

    return None


from application.controllers import *

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        debug=os.getenv("ENV", "development") != "production"
    )