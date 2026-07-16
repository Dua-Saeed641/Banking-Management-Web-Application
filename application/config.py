import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "your-secret-key"

    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///" +
        os.path.join(BASE_DIR, "..", "db_directory", "atm_simulation.sqlite3")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False