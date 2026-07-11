"""
Standardized API responses and error handling.
"""
import time
import logging
from datetime import datetime
from functools import wraps
from flask import jsonify, request as flask_request

logger = logging.getLogger('api')


# ── Custom Exceptions ──────────────────────────────────────

class AppError(Exception):
    def __init__(self, message, status_code=400, payload=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload


class ValidationError(AppError):
    def __init__(self, message='Validation failed'):
        super().__init__(message, status_code=400)


class AuthenticationError(AppError):
    def __init__(self, message='Authentication failed'):
        super().__init__(message, status_code=401)


class NotFoundError(AppError):
    def __init__(self, message='Resource not found'):
        super().__init__(message, status_code=404)


class ConflictError(AppError):
    def __init__(self, message='Resource conflict'):
        super().__init__(message, status_code=409)


class AIAnalysisError(AppError):
    def __init__(self, message='AI analysis failed'):
        super().__init__(message, status_code=500)


# ── Response Builders ───────────────────────────────────────

def success_response(data=None, message=None, status_code=200):
    body = {
        'success': True,
        'data': data,
        'error': None,
        'message': message,
        'timestamp': datetime.utcnow().isoformat(),
    }
    return jsonify(body), status_code


def error_response(error_message, status_code=400, data=None):
    body = {
        'success': False,
        'data': data,
        'error': error_message,
        'message': None,
        'timestamp': datetime.utcnow().isoformat(),
    }
    return jsonify(body), status_code


# ── Decorators ──────────────────────────────────────────────

def log_execution_time(f):
    """Decorator: logs how long a route handler takes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        duration = time.time() - start
        logger.info(
    f"{flask_request.method} {flask_request.path} -> {duration:.2f}s"
)
        return result
    return decorated


# ── Error Handler Registration ──────────────────────────────

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        logger.warning(f"AppError: {error.message} ({error.status_code})")
        return jsonify({
            'success': False, 'data': error.payload,
            'error': error.message, 'message': None,
            'timestamp': datetime.utcnow().isoformat(),
        }), error.status_code

    status_handlers = {
        400: 'Bad request',
        401: 'Unauthorized. Please provide a valid token.',
        403: 'Forbidden',
        404: 'Route not found',
        405: 'Method not allowed',
        413: 'File too large. Maximum size is 16MB.',
        500: 'Internal server error',
    }
    for code, msg in status_handlers.items():
        @app.errorhandler(code)
        def handler(error, _code=code, _msg=msg):
            if _code == 500:
                logger.error(f"Internal error: {str(error)}")
            return jsonify({
                'success': False, 'data': None,
                'error': _msg, 'message': None,
                'timestamp': datetime.utcnow().isoformat(),
            }), _code
