import os

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)


class LocalDevelopmentConfig:
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///" +
        os.path.join(
            BASE_DIR,
            "db_directory",
            "atm_simulation.sqlite3"
        )
    )

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "local-development-secret-key"
    )


class ProductionConfig:
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    database_url = os.getenv("DATABASE_URL")
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    SQLALCHEMY_DATABASE_URI = database_url
    SECRET_KEY = os.getenv("SECRET_KEY")
