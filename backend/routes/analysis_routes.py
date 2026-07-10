"""
Analysis routes: pandas analysis, AI insights, Q&A, data quality, recommendations, model config, architecture metadata.
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.analysis_service import run_full_analysis
from services.ai_service import (
    run_ai_pipeline, answer_question, run_data_quality,
    ProfilingAgent, RecommendationAgent, get_architecture_metadata,
    compare_models, PIPELINE_STATUS,
)
from services.llm_service import get_llm, get_model_info, set_model
from services.upload_service import get_latest_upload_path
from models.analysis_history import AnalysisHistory
from extensions import db
from utils.response_helpers import success_response, error_response, log_execution_time, ValidationError, AIAnalysisError
from utils.validators import validate_mode_param, check_empty_dataset
import os

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api/analysis')


def _require_csv(user_id):
    fp = get_latest_upload_path(user_id)
    if not fp or not os.path.exists(fp):
        raise ValidationError('No CSV uploaded. Upload a file first.')
    is_empty, msg = check_empty_dataset(fp)
    if is_empty:
        raise ValidationError(msg)
    return fp


@analysis_bp.route('/analyze', methods=['POST'])
@jwt_required()
def analyze():
    user_id = int(get_jwt_identity())
    try:
        result = run_full_analysis(_require_csv(user_id))
    except Exception as e:
        raise AIAnalysisError(f'Analysis failed: {str(e)}')
    db.session.add(AnalysisHistory(user_id=user_id, question='Full analysis', response='Completed'))
    db.session.commit()
    return success_response(data=result)


@analysis_bp.route('/insights', methods=['POST'])
@jwt_required()
@log_execution_time
def insights():
    user_id = int(get_jwt_identity())
    mode = (request.json or {}).get('mode')
    valid, msg = validate_mode_param(mode)
    if not valid:
        return error_response(msg)
    try:
        result = run_ai_pipeline(_require_csv(user_id), mode=mode)
    except Exception as e:
        raise AIAnalysisError(f'Insights failed: {str(e)}')
    db.session.add(AnalysisHistory(user_id=user_id, question='AI insights', response=result['insights']))
    db.session.commit()
    return success_response(data=result)


@analysis_bp.route('/ask', methods=['POST'])
@jwt_required()
def ask():
    user_id = int(get_jwt_identity())
    data = request.json
    if not data or not data.get('question'):
        raise ValidationError('No question provided')
    question = data['question'].strip()
    if not question:
        raise ValidationError('Question cannot be empty')
    if len(question) > 500:
        raise ValidationError('Question too long (max 500 characters)')
    mode = data.get('mode')
    valid, msg = validate_mode_param(mode)
    if not valid:
        return error_response(msg)
    try:
        analysis = run_full_analysis(_require_csv(user_id))
        answer = answer_question(analysis, question, mode=mode)
    except Exception as e:
        raise AIAnalysisError(f'Question failed: {str(e)}')
    db.session.add(AnalysisHistory(user_id=user_id, question=question, response=answer))
    db.session.commit()
    return success_response(data={'answer': answer})


@analysis_bp.route('/quality', methods=['POST'])
@jwt_required()
def quality():
    user_id = int(get_jwt_identity())
    try:
        result = run_data_quality(_require_csv(user_id))
    except Exception as e:
        raise AIAnalysisError(f'Quality check failed: {str(e)}')
    return success_response(data=result)


@analysis_bp.route('/profile', methods=['POST'])
@jwt_required()
def profile():
    user_id = int(get_jwt_identity())
    try:
        analysis = run_full_analysis(_require_csv(user_id))
        result = ProfilingAgent().run(analysis)
    except Exception as e:
        raise AIAnalysisError(f'Profiling failed: {str(e)}')
    return success_response(data=result)


@analysis_bp.route('/recommend', methods=['POST'])
@jwt_required()
def recommend():
    user_id = int(get_jwt_identity())
    mode = (request.json or {}).get('mode')
    valid, msg = validate_mode_param(mode)
    if not valid:
        return error_response(msg)
    try:
        analysis = run_full_analysis(_require_csv(user_id))
        result = RecommendationAgent().run(analysis, get_llm(), mode=mode)
    except Exception as e:
        raise AIAnalysisError(f'Recommendation failed: {str(e)}')
    db.session.add(AnalysisHistory(user_id=user_id, question='AI recommendation', response=result['text']))
    db.session.commit()
    return success_response(data=result)


@analysis_bp.route('/model', methods=['GET', 'POST'])
@jwt_required()
def model_config():
    if request.method == 'POST':
        data = request.json
        if not data or not data.get('model'):
            raise ValidationError('No model specified')
        result = set_model(data['model'])
        return success_response(data=result)
    return success_response(data=get_model_info())


@analysis_bp.route('/compare-models', methods=['POST'])
@jwt_required()
def compare_models_endpoint():
    data = request.json
    if not data or not data.get('question'):
        raise ValidationError('No question provided')
    question = data['question'].strip()
    if not question:
        raise ValidationError('Question cannot be empty')
    try:
        result = compare_models(question)
    except Exception as e:
        raise AIAnalysisError(f'Model comparison failed: {str(e)}')
    return success_response(data={"comparisons": result})


@analysis_bp.route('/architecture', methods=['GET'])
@jwt_required()
def architecture():
    return success_response(data=get_architecture_metadata())


@analysis_bp.route('/status', methods=['GET'])
@jwt_required()
def pipeline_status():
    return success_response(data=PIPELINE_STATUS)
