"""
Tests adicionales para aumentar cobertura de app/middleware/auth.py
"""

import pytest
from unittest.mock import patch, MagicMock
from flask import request
from app import create_app
from app.middleware.auth import require_token_socket, require_admin_socket, optional_auth_http
from app.services.jwt_service import JWTService


@pytest.fixture
def app():
    return create_app('testing')


# ---------- Tests para require_token_socket ---------- #

def test_require_token_socket_no_token_no_user(app):
    with app.app_context():
        from app.utils.database import mongo
        mongo.db.users.delete_many({})

        @require_token_socket
        def dummy_handler(username, data):
            return username

        with app.test_request_context():
            mock_request = MagicMock()
            mock_request.sid = "fake_sid"
            with patch("app.middleware.auth.request", mock_request):
                with patch("app.middleware.auth.emit") as mock_emit:
                    result = dummy_handler({"token": None})
                    assert result is None
                    args = mock_emit.call_args[0][1]
                    assert args["code"] == "no_token"


def test_require_token_socket_expired_token(app):
    with app.app_context():
        @require_token_socket
        def dummy_handler(username, data):
            return username

        with app.test_request_context():
            with patch.object(JWTService, "verify_token", side_effect=ValueError("token_expired")):
                with patch("app.middleware.auth.emit") as mock_emit:
                    result = dummy_handler({"token": "expired_token"})
                    assert result is None
                    args = mock_emit.call_args[0][1]
                    assert args["code"] == "token_expired"


def test_require_token_socket_valid_user_by_socket_id(app):
    with app.app_context():
        from app.utils.database import mongo
        mongo.db.users.delete_many({})
        mongo.db.users.insert_one({
            "username": "anon_123",
            "socket_id": "test_sid"
        })

        @require_token_socket
        def dummy_handler(username, data):
            return username

        with app.test_request_context():
            mock_request = MagicMock()
            mock_request.sid = "test_sid"
            with patch("app.middleware.auth.request", mock_request):
                result = dummy_handler({"token": None})
                assert result == "anon_123"


# ---------- Tests para require_admin_socket ---------- #

def test_require_admin_socket_not_admin(app):
    with app.app_context():
        from app.utils.database import mongo
        mongo.db.users.delete_many({})
        mongo.db.users.insert_one({
            "username": "regular_user",
            "is_admin": False
        })

        @require_admin_socket
        def dummy_handler(username, data):
            return "should_not_reach"

        with app.test_request_context():
            with patch("app.middleware.auth.emit") as mock_emit:
                result = dummy_handler("regular_user", {})
                assert result is None
                args = mock_emit.call_args[0][1]
                assert args["code"] == "forbidden"


# ---------- Tests para optional_auth_http ---------- #

def test_optional_auth_http_invalid_format(app):
    @optional_auth_http
    def dummy_route(username):
        return username

    with app.test_request_context(headers={"Authorization": "InvalidFormat"}):
        result = dummy_route()
        assert result is None


def test_optional_auth_http_invalid_token(app):
    @optional_auth_http
    def dummy_route(username):
        return username

    with patch.object(JWTService, "verify_token", side_effect=ValueError("invalid")):
        with app.test_request_context(headers={"Authorization": "Bearer invalid_token"}):
            result = dummy_route()
            assert result is None