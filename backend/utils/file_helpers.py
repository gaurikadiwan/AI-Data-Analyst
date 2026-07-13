"""
File system helpers.
"""
import os
import uuid
from datetime import datetime


def unique_filename(original_filename):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    name, ext = os.path.splitext(original_filename)
    return f"{name}_{timestamp}_{unique_id}{ext}"


def ensure_dir(directory):
    os.makedirs(directory, exist_ok=True)
    return directory
