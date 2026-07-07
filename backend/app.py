"""
Flask application factory.
Dev entry point: python app.py
"""
import os
import logging
from flask import Flask, send_from_directory
from flask_cors import CORS
from config.config import Config
from extensions import init_extensions
from middleware.logging_middleware import register_logging_middleware
from utils.response_helpers import register_error_handlers, success_response
from routes.auth_routes import auth_bp
from routes.upload_routes import upload_bp
from routes.analysis_routes import analysis_bp
from routes.history_routes import history_bp

# Ensure logs directory exists (called at import time so Gunicorn workers have it)
os.makedirs(os.path.join(os.path.dirname(__file__), 'logs'), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'app.log')),
    ],
)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    init_extensions(app)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['CHART_FOLDER'], exist_ok=True)

    register_logging_middleware(app)
    register_error_handlers(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(history_bp)

    @app.route('/charts/<filename>')
    def serve_chart(filename):
        return send_from_directory(app.config['CHART_FOLDER'], filename)

    @app.route('/api/health', methods=['GET'])
    def health():
        return {
            'status': 'ok',
            'message': 'backend running',
            'services': {
                'ai_service': 'loaded',
                'analysis_service': 'loaded'
            }
        }, 200

    return app


if __name__ == '__main__':
    logging.getLogger('api').info('Starting AI Data Analyst API (dev mode)...')
    app = create_app()
    app.run(
    debug=Config.DEBUG,
    port=Config.FLASK_PORT,
    use_reloader=False
)
