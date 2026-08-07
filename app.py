import os 

from flask import Flask

from application.config import LocalDevelopmentConfig

from application.database import db
from application.database import login_manager

from application.models import Admin  

app=None
#building application inside one function for better architecture,easier testing
def create_app():
    app=Flask(
        __name__,
        template_folder="application/templates",
        static_folder="application/static")
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
    return User.query.get(int(user_id))

from application.controllers import *

with app.app_context():
    db.create_all()

if __name__=="__main__":
    app.run(
        host="0.0.0.0",
        port=8080,
        debug=True
        )

    