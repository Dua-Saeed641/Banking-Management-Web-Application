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