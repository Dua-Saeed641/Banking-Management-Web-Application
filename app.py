import os 

from flask import Flask

from application.config import LocalDevelopmentConfig

from application.database import db
from application.database import login_manager

from application.models import Admin, PRO, User  

app=None
#building application inside one function for better architecture,easier testing
def create_app():
    app=Flask(
        __name__,
        template_folder="templates",
        static_folder="static")
    app.secret_key="atm_simulation_secret_key"

    if os.getenv("ENV","development")=="production":
        raise Exception("Production configuration not implemented")
    else:
        print("Startting Local Development...")

        app.config.from_object(LocalDevelopmentConfig)

    db.init_app(app) 
    login_manager.init_app(app)
    app.app_context().push()
    return app 

app=create_app()

@login_manager.user_loader
def load_user(user_id):

    role, actual_id = user_id.split("-")

    if role == "admin":
        return Admin.query.get(int(actual_id))

    elif role == "pro":
        return PRO.query.get(int(actual_id))

    elif role == "user":
        return User.query.get(int(actual_id))

    return None

from application.controllers import *

with app.app_context():
    db.create_all()

if __name__=="__main__":
    app.run(
        host="0.0.0.0",
        port=8080,
        debug=True
        )

    