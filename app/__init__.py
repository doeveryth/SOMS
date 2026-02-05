import os
from flask import Flask
from dotenv import load_dotenv

from .extensions import db, migrate, login_manager
from .routes import auth, dashboard, customers, uploads
from .routes import sr, schedule, work
from .bootstrap import ensure_bootstrap_admin


def create_app():
    load_dotenv()

    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "CHANGE_ME")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    max_mb = int(os.getenv("MAX_UPLOAD_MB", "500"))
    app.config["MAX_CONTENT_LENGTH"] = max_mb * 1024 * 1024

    app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "app/static/uploads")

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(customers.bp)
    app.register_blueprint(uploads.bp)
    app.register_blueprint(sr.bp)
    app.register_blueprint(work.bp)
    app.register_blueprint(schedule.bp)

    with app.app_context():
        ensure_bootstrap_admin()

    return app