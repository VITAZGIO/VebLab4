import os
import secrets
from urllib.parse import urlencode

from flask import Blueprint, request, jsonify, make_response, g, redirect

from app.services.auth_service import AuthService
from app.utils.cookie_utils import set_auth_cookies, clear_auth_cookies
from app.middleware.auth_middleware import auth_required


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"message": "JSON body is required"}), 400

    if not data.get("email") or not data.get("password"):
        return jsonify({"message": "Email and password are required"}), 400

    try:
        user = AuthService.register(data)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400

    return jsonify({
        "id": user.id,
        "email": user.email
    }), 201


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"message": "JSON body is required"}), 400

    if not data.get("email") or not data.get("password"):
        return jsonify({"message": "Email and password are required"}), 400

    result = AuthService.login(data)

    if not result:
        return jsonify({"message": "Invalid credentials"}), 401

    user, access_token, refresh_token = result

    response = make_response(jsonify({"message": "Logged in"}))
    set_auth_cookies(response, access_token, refresh_token)

    return response, 200


@auth_bp.route("/auth/refresh", methods=["POST"])
def refresh():
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        return jsonify({"message": "Refresh token is missing"}), 401

    result = AuthService.refresh(refresh_token)

    if not result:
        return jsonify({"message": "Invalid refresh token"}), 401

    user, access_token, new_refresh_token = result

    response = make_response(jsonify({
        "message": "Tokens refreshed",
        "user": {
            "id": user.id,
            "email": user.email
        }
    }))

    set_auth_cookies(response, access_token, new_refresh_token)

    return response, 200


@auth_bp.route("/auth/whoami", methods=["GET"])
@auth_required
def whoami():
    user = g.current_user

    return jsonify({
        "id": user.id,
        "email": user.email,
        "yandex_id": user.yandex_id
    }), 200


@auth_bp.route("/auth/logout", methods=["POST"])
@auth_required
def logout():
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    AuthService.logout(access_token, refresh_token)

    response = make_response(jsonify({"message": "Logged out"}))
    clear_auth_cookies(response)

    return response, 200


@auth_bp.route("/auth/logout-all", methods=["POST"])
@auth_required
def logout_all():
    user = g.current_user

    AuthService.logout_all(user.id)

    response = make_response(jsonify({"message": "Logged out from all sessions"}))
    clear_auth_cookies(response)

    return response, 200


@auth_bp.route("/auth/oauth/yandex", methods=["GET"])
def yandex_oauth_start():
    client_id = os.getenv("YANDEX_CLIENT_ID")
    redirect_uri = os.getenv("YANDEX_CALLBACK_URL")

    if not client_id or not redirect_uri:
        return jsonify({"message": "Yandex OAuth is not configured"}), 500

    state = secrets.token_urlsafe(32)

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state
    }

    yandex_url = "https://oauth.yandex.ru/authorize?" + urlencode(params)

    response = redirect(yandex_url)
    response.set_cookie(
        "oauth_state",
        state,
        httponly=True,
        samesite="Lax",
        max_age=300
    )

    return response


@auth_bp.route("/auth/oauth/yandex/callback", methods=["GET"])
def yandex_oauth_callback():
    code = request.args.get("code")
    state = request.args.get("state")
    saved_state = request.cookies.get("oauth_state")

    if not code:
        return jsonify({"message": "Authorization code is missing"}), 400

    if not state or not saved_state or state != saved_state:
        return jsonify({"message": "Invalid OAuth state"}), 400

    result = AuthService.login_with_yandex(code)

    if not result:
        return jsonify({"message": "Yandex OAuth failed"}), 401

    user, access_token, refresh_token = result

    response = redirect("/auth/whoami")
    set_auth_cookies(response, access_token, refresh_token)
    response.delete_cookie("oauth_state")

    return response
