"""
Auth middleware: token validation and user context decorator.
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from services.auth_service import get_user_by_id


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 401
        kwargs['current_user'] = user
        return f(*args, **kwargs)
    return decorated
