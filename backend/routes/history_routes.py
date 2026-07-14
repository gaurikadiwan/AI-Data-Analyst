"""
History Routes (Blueprint)
User analysis and upload history.
"""
from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.analysis_history import AnalysisHistory
from services.upload_service import get_user_uploads
from utils.response_helpers import success_response, error_response

history_bp = Blueprint('history', __name__, url_prefix='/api/history')


@history_bp.route('/analysis', methods=['GET'])
@jwt_required()
def analysis_history():
    user_id = int(get_jwt_identity())
    items = AnalysisHistory.query.filter_by(user_id=user_id).order_by(
        AnalysisHistory.created_at.desc()
    ).limit(20).all()
    return success_response(data={'history': [h.to_dict() for h in items]})


@history_bp.route('/analysis/<int:history_id>', methods=['GET'])
@jwt_required()
def analysis_detail(history_id):
    user_id = int(get_jwt_identity())
    item = AnalysisHistory.query.filter_by(id=history_id, user_id=user_id).first()
    if not item:
        return error_response('History item not found', 404)
    return success_response(data={'history': item.to_dict()})


@history_bp.route('/uploads', methods=['GET'])
@jwt_required()
def upload_history():
    user_id = int(get_jwt_identity())
    uploads = get_user_uploads(user_id)
    return success_response(data={'uploads': [u.to_dict() for u in uploads]})
