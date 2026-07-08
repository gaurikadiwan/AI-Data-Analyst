from datetime import datetime
from extensions import db


class AnalysisHistory(db.Model):
    __tablename__ = 'analysis_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    question = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    chart_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'question': self.question,
            'response': self.response,
            'chart_path': self.chart_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
