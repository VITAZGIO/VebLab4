from functools import wraps
from datetime import datetime

from flask import request, jsonify, g

from app import db
from app.models.user import User
from app.models.auth_token import AuthToken
from app.utils.hash_utils import hash_token
from app.utils.jwt_utils import decode_access_token


def auth_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.cookies.get("access_token")

        if not token:
            return jsonify({"message": "Unauthorized"}), 401

        try:
            payload = decode_access_token(token)

            if payload.get("type") != "access":
                return jsonify({"message": "Unauthorized"}), 401

            user = User.query.filter_by(id=payload["sub"]).first()

            if not user:
                return jsonify({"message": "Unauthorized"}), 401

            token_record = AuthToken.query.filter_by(
                user_id=user.id,
                token_hash=hash_token(token),
                token_type="access",
                revoked=False
            ).first()

            if not token_record:
                return jsonify({"message": "Unauthorized"}), 401

            if token_record.expires_at < datetime.utcnow():
                token_record.revoked = True
                db.session.commit()
                return jsonify({"message": "Unauthorized"}), 401

            g.current_user = user

        except Exception:
            return jsonify({"message": "Unauthorized"}), 401

        return f(*args, **kwargs)

    return wrapper
