"""
Upload Service
Manages CSV file upload records in the database.
"""
from models.upload import Upload
from extensions import db


def save_upload(user_id, filename, filepath):
    upload = Upload(user_id=user_id, filename=filename, filepath=filepath)
    db.session.add(upload)
    db.session.commit()
    return upload


def get_user_uploads(user_id, limit=10):
    return Upload.query.filter_by(user_id=user_id).order_by(
        Upload.uploaded_at.desc()
    ).limit(limit).all()


def get_latest_upload_path(user_id):
    uploads = get_user_uploads(user_id, limit=1)
    return uploads[0].filepath if uploads else None
