#this file is made to simply import db object everywhere to follow the DRY principle


from flask_sqlalchemy import SQLAlchemy 
from flask_login import LoginManager

db=SQLAlchemy()
login_manager=LoginManager()
#for all authentication tasks and route 

login_manager.login_view="home"