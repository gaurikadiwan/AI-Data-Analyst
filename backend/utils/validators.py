"""
Request validation utilities and route decorators.
"""
import re
import os
import csv
import io
from functools import wraps
from flask import request


def validate_email(email):
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email.strip())) if email else False


def validate_password(password):
    if not password or len(password) < 6:
        return False, 'Password must be at least 6 characters'
    return True, ''


def validate_name(name):
    return bool(name and len(name.strip()) >= 2)


def validate_question(question):
    if not question or not question.strip():
        return False, 'No question provided'
    if len(question) > 500:
        return False, 'Question too long (max 500 characters)'
    return True, ''


def validate_json_body(*required_fields):
    """Decorator: ensures required JSON fields exist in request body."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json(silent=True)
            if not data:
                from utils.response_helpers import ValidationError
                raise ValidationError('Request body must be valid JSON')
            missing = [field for field in required_fields if field not in data]
            if missing:
                from utils.response_helpers import ValidationError
                raise ValidationError(f"Missing required fields: {', '.join(missing)}")
            return f(*args, **kwargs)
        return decorated
    return decorator


def validate_file_upload(f):
    """Decorator: ensures a CSV file was uploaded and validates its content."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'file' not in request.files:
            from utils.response_helpers import ValidationError
            raise ValidationError('No file provided')
        file = request.files['file']
        if not file.filename:
            from utils.response_helpers import ValidationError
            raise ValidationError('No file selected')
        if not file.filename.lower().endswith('.csv'):
            from utils.response_helpers import ValidationError
            raise ValidationError('Only CSV files are allowed')
        content = file.read(io.DEFAULT_BUFFER_SIZE)
        file.seek(0)
        try:
            reader = csv.reader(io.StringIO(content.decode('utf-8-sig')))
            header = next(reader, None)
            if not header or len([c for c in header if c.strip()]) == 0:
                raise ValidationError('CSV file appears empty or has no valid headers')
        except UnicodeDecodeError:
            raise ValidationError('CSV must be UTF-8 encoded')
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f'Invalid CSV file: {str(e)}')
        return f(*args, **kwargs)
    return decorated


def validate_mode_param(mode):
    if not mode:
        return True, ''
    valid_modes = ('executive_summary', 'technical_analysis', 'concise', 'business_insights', 'strict_factual')
    if mode not in valid_modes:
        return False, f"Invalid mode. Choose from: {', '.join(valid_modes)}"
    return True, ''


def check_empty_dataset(filepath):
    if not os.path.exists(filepath):
        return True, 'File not found'
    import pandas as pd
    try:
        df = pd.read_csv(filepath)
        if df.empty or len(df) == 0:
            return True, 'Dataset is empty'
        return False, ''
    except Exception as e:
        return True, f'Cannot read dataset: {str(e)}'
