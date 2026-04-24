import os

from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)

    from app.models.auth_token import AuthToken
    from app.models.task import Task
    from app.models.user import User

    from app.routes.auth_routes import auth_bp
    from app.routes.task_routes import task_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(task_bp)

    from app.swagger import setup_swagger

    setup_swagger(app)

    return app