"""
Authentication routes: signup, login, profile.
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.auth_service import create_user, authenticate_user, generate_token, get_user_by_id
from utils.validators import validate_email, validate_password, validate_name, validate_json_body
from utils.response_helpers import success_response, error_response, AuthenticationError, ValidationError

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/signup', methods=['POST'])
@validate_json_body('name', 'email', 'password')
def signup():
    data = request.json
    name, email, password = data['name'].strip(), data['email'].strip().lower(), data['password']
    if not validate_name(name):
        raise ValidationError('Name must be at least 2 characters')
    if not validate_email(email):
        raise ValidationError('Invalid email format')
    ok, err = validate_password(password)
    if not ok:
        raise ValidationError(err)
    user, err = create_user(name, email, password)
    if err:
        return error_response(err, 409)
    return success_response(data={'user': user.to_dict(), 'token': generate_token(user)}, message='Account created', status_code=201)


@auth_bp.route('/login', methods=['POST'])
@validate_json_body('email', 'password')
def login():
    data = request.json
    email, password = data['email'].strip().lower(), data['password']
    user, err = authenticate_user(email, password)
    if err:
        raise AuthenticationError(err)
    return success_response(data={'user': user.to_dict(), 'token': generate_token(user)}, message='Login successful')


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = get_user_by_id(user_id)
    if not user:
        return error_response('User not found', 404)
    return success_response(data={'user': user.to_dict()})
