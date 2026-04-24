import os
import secrets
from datetime import datetime, timedelta

import requests

from app import db
from app.models.user import User
from app.models.auth_token import AuthToken
from app.utils.hash_utils import generate_salt, hash_password, verify_password, hash_token
from app.utils.jwt_utils import create_access_token, create_refresh_token, decode_refresh_token


class AuthService:

    @staticmethod
    def register(data):
        email = data["email"].strip().lower()
        password = data["password"]

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            raise ValueError("User already exists")

        salt = generate_salt()
        password_hash = hash_password(password, salt)

        user = User(
            email=email,
            password_hash=password_hash,
            password_salt=salt
        )

        db.session.add(user)
        db.session.commit()

        return user

    @staticmethod
    def create_session(user):
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        access_token_record = AuthToken(
            user_id=user.id,
            token_hash=hash_token(access_token),
            token_type="access",
            expires_at=datetime.utcnow() + timedelta(minutes=15),
            revoked=False
        )

        refresh_token_record = AuthToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            token_type="refresh",
            expires_at=datetime.utcnow() + timedelta(days=7),
            revoked=False
        )

        db.session.add(access_token_record)
        db.session.add(refresh_token_record)
        db.session.commit()

        return access_token, refresh_token

    @staticmethod
    def login(data):
        email = data["email"].strip().lower()
        password = data["password"]

        user = User.query.filter_by(email=email).first()

        if not user:
            return None

        if not verify_password(password, user.password_salt, user.password_hash):
            return None

        access_token, refresh_token = AuthService.create_session(user)

        return user, access_token, refresh_token

    @staticmethod
    def refresh(refresh_token):
        try:
            payload = decode_refresh_token(refresh_token)
        except Exception:
            return None

        if payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")

        user = User.query.filter_by(id=user_id).first()

        if not user:
            return None

        token_hash = hash_token(refresh_token)

        token_record = AuthToken.query.filter_by(
            user_id=user.id,
            token_hash=token_hash,
            token_type="refresh",
            revoked=False
        ).first()

        if not token_record:
            return None

        if token_record.expires_at < datetime.utcnow():
            token_record.revoked = True
            db.session.commit()
            return None

        token_record.revoked = True
        db.session.commit()

        access_token, new_refresh_token = AuthService.create_session(user)

        return user, access_token, new_refresh_token

    @staticmethod
    def logout(access_token=None, refresh_token=None):
        hashes = []

        if access_token:
            hashes.append(hash_token(access_token))

        if refresh_token:
            hashes.append(hash_token(refresh_token))

        if not hashes:
            return

        AuthToken.query.filter(AuthToken.token_hash.in_(hashes)).update(
            {"revoked": True},
            synchronize_session=False
        )

        db.session.commit()

    @staticmethod
    def logout_all(user_id):
        AuthToken.query.filter_by(user_id=user_id, revoked=False).update(
            {"revoked": True},
            synchronize_session=False
        )

        db.session.commit()

    @staticmethod
    def login_with_yandex(code):
        client_id = os.getenv("YANDEX_CLIENT_ID")
        client_secret = os.getenv("YANDEX_CLIENT_SECRET")
        redirect_uri = os.getenv("YANDEX_CALLBACK_URL")

        if not client_id or not client_secret or not redirect_uri:
            return None

        token_response = requests.post(
            "https://oauth.yandex.ru/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri
            },
            timeout=10
        )

        if token_response.status_code != 200:
            print("Yandex token error:", token_response.text)
            return None

        token_data = token_response.json()
        yandex_access_token = token_data.get("access_token")

        if not yandex_access_token:
            return None

        profile_response = requests.get(
            "https://login.yandex.ru/info",
            headers={
                "Authorization": f"OAuth {yandex_access_token}"
            },
            params={
                "format": "json"
            },
            timeout=10
        )

        if profile_response.status_code != 200:
            print("Yandex profile error:", profile_response.text)
            return None

        profile = profile_response.json()

        yandex_id = str(profile.get("id"))
        email = profile.get("default_email")

        if not yandex_id:
            return None

        if not email:
            email = f"yandex_{yandex_id}@local.test"

        email = email.strip().lower()

        user = User.query.filter_by(yandex_id=yandex_id).first()

        if not user:
            user = User.query.filter_by(email=email).first()

            if user:
                user.yandex_id = yandex_id
            else:
                random_password = secrets.token_urlsafe(32)
                salt = generate_salt()
                password_hash = hash_password(random_password, salt)

                user = User(
                    email=email,
                    password_hash=password_hash,
                    password_salt=salt,
                    yandex_id=yandex_id
                )

                db.session.add(user)

            db.session.commit()

        access_token, refresh_token = AuthService.create_session(user)

        return user, access_token, refresh_token
