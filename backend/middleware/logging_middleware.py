"""
Logging middleware: logs every request with method, path, status, duration.
"""

import time
import logging

logger = logging.getLogger("api")


def register_logging_middleware(app):

    @app.before_request
    def start_timer():
        from flask import request
        request._start_time = time.time()

    @app.after_request
    def log_request(response):
        from flask import request

        if hasattr(request, "_start_time"):
            duration = round((time.time() - request._start_time) * 1000, 2)

            log_message = (
                f"{request.method} {request.path} -> "
                f"{response.status_code} ({duration}ms)"
            )

            if response.status_code >= 400:
                logger.warning(log_message)
            else:
                logger.info(log_message)

        return response