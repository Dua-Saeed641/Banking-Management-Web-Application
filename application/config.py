import os 

BASE_DIR=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#configuration class
class LocalDevelopmentConfig:
    DEBUG=True 
    SQLALCHEMY_TRACK_MODIFICATIONS=False 

    #DB LOCATION
    SQLALCHEMY_DATABASE_URI=("sqlite:///"+os.path.join(BASE_DIR,"db_directory","atm_simulation.sqlite3"))
