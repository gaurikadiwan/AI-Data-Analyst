"""
Upload routes: CSV file upload.
"""
import os
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from services.upload_service import save_upload
from utils.file_helpers import unique_filename, ensure_dir
from utils.response_helpers import success_response
from utils.validators import validate_file_upload

upload_bp = Blueprint('uploads', __name__, url_prefix='/api/uploads')


@upload_bp.route('', methods=['POST'])
@jwt_required()
@validate_file_upload
def upload():
    user_id = int(get_jwt_identity())
    file = request.files['file']
    name = unique_filename(secure_filename(file.filename))
    path = os.path.join(ensure_dir(current_app.config['UPLOAD_FOLDER']), name)
    file.save(path)
    upload = save_upload(user_id, file.filename, path)
    return success_response(data={'upload': upload.to_dict()}, message='File uploaded', status_code=201)
