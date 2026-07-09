"""
Authentication service: user creation, password hashing, JWT generation.
"""
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from models.user import User
from extensions import db


def create_user(name, email, password):
    if User.query.filter_by(email=email).first():
        return None, 'Email already registered'
    user = User(name=name, email=email, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    return user, None


def authenticate_user(email, password):
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return None, 'Invalid email or password'
    return user, None


def generate_token(user, expires_seconds=86400):
    return create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(seconds=expires_seconds),
        additional_claims={'name': user.name, 'email': user.email},
    )


def get_user_by_id(user_id):
    return User.query.get(int(user_id))
