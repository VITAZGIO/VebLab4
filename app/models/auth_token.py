import uuid
from datetime import datetime
from app import db

class AuthToken(db.Model):
    __tablename__ = "auth_tokens"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)

    token_hash = db.Column(db.String(255), nullable=False)
    token_type = db.Column(db.String(50), nullable=False)  # access / refresh

    expires_at = db.Column(db.DateTime, nullable=False)
    revoked = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)