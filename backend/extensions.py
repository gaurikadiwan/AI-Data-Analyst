"""
Extensions Module
Centralizes Flask extension initialization (db, migrate, jwt).
Extensions are created here and imported wherever needed.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def init_extensions(app):
    """Bind all extensions to the Flask app and create tables."""
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    with app.app_context():
        db.create_all()
