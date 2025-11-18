"""
Tests para app/sockets/message_events.py
"""

import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from app.sockets.message_events import register_message_events
from app.utils.database import mongo
from app.services.jwt_service import JWTService


@pytest.fixture
def app():
    app = create_app('testing')
    return app


@pytest.fixture
def socketio(app):
    from flask_socketio import SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")
    register_message_events(socketio)
    return socketio


@pytest.fixture
def client(app, socketio):
    return socketio.test_client(app, flask_test_client=app.test_client())


def test_send_message_success(client, app):
    with app.app_context():
        mongo.db.users.delete_many({})
        mongo.db.rooms.delete_many({})
        mongo.db.messages.delete_many({})

        # Crear usuario y sala
        from app.models import get_user_model, get_room_model
        user_model = get_user_model()
        room_model = get_room_model()
        user_model.create_user("testuser", "password123")
        room_model.create_room("General")
        user_model.update_room("testuser", "General", socket_id="fake_sid")

        with patch.object(JWTService, "verify_token", return_value="testuser"):
            with patch("app.sockets.message_events.emit") as mock_emit:
                client.emit("send_message", {
                    "token": "valid_token",
                    "room": "General",
                    "msg": "Hola"
                })
                assert mock_emit.called
                args = mock_emit.call_args[0]
                assert args[0] == "message"
                assert args[1]["msg"] == "Hola"


def test_send_message_no_room(client, app):
    with app.app_context():
        with patch.object(JWTService, "verify_token", return_value="testuser"):
            with patch("app.sockets.message_events.emit") as mock_emit:
                client.emit("send_message", {
                    "token": "valid_token",
                    "msg": "Hola"
                })
                assert mock_emit.called
                args = mock_emit.call_args[0]
                assert args[0] == "msg_error"
                assert "room requerido" in args[1]["msg"]


def test_get_messages(client, app):
    with app.app_context():
        mongo.db.messages.delete_many({})
        mongo.db.rooms.delete_many({})
        from app.models import get_room_model, get_message_model
        room_model = get_room_model()
        msg_model = get_message_model()
        room_model.create_room("General")
        msg_model.create_message("General", "user1", msg="Hola")

        with patch.object(JWTService, "verify_token", return_value="user1"):
            with patch("app.sockets.message_events.emit") as mock_emit:
                client.emit("get_messages", {
                    "token": "valid_token",
                    "room": "General",
                    "limit": 10
                })
                assert mock_emit.called
                args = mock_emit.call_args[0]
                assert args[0] == "messages_list"
                assert len(args[1]["messages"]) == 1


def test_typing(client, app):
    with app.app_context():
        mongo.db.users.delete_many({})
        from app.models import get_user_model
        user_model = get_user_model()
        user_model.create_user("testuser", "password123")
        user_model.update_room("testuser", "General", socket_id="fake_sid")

        with patch.object(JWTService, "verify_token", return_value="testuser"):
            with patch("app.sockets.message_events.emit") as mock_emit:
                client.emit("typing", {
                    "token": "valid_token",
                    "room": "General",
                    "is_typing": True
                })
                assert mock_emit.called
                args = mock_emit.call_args[0]
                assert args[0] == "user_typing"
                assert args[1]["username"] == "testuser"


def test_delete_message(client, app):
    with app.app_context():
        mongo.db.messages.delete_many({})
        mongo.db.users.delete_many({})
        from app.models import get_user_model, get_message_model
        from bson.objectid import ObjectId
        user_model = get_user_model()
        msg_model = get_message_model()
        user_model.create_user("testuser", "password123")
        msg = msg_model.create_message("General", "testuser", msg="Hola")
        msg_id = str(msg["_id"])

        with patch.object(JWTService, "verify_token", return_value="testuser"):
            with patch("app.sockets.message_events.emit") as mock_emit:
                client.emit("delete_message", {
                    "token": "valid_token",
                    "message_id": msg_id,
                    "room": "General"
                })
                assert mock_emit.called
                args = mock_emit.call_args[0]
                assert args[0] == "message_deleted"
                assert args[1]["message_id"] == msg_id


def test_search_messages(client, app):
    with app.app_context():
        mongo.db.messages.delete_many({})
        mongo.db.rooms.delete_many({})
        from app.models import get_message_model, get_room_model
        room_model = get_room_model()
        msg_model = get_message_model()
        room_model.create_room("SearchRoom")
        msg_model.create_message("SearchRoom", "user1", msg="Hola mundo")

        with patch.object(JWTService, "verify_token", return_value="user1"):
            with patch("app.sockets.message_events.emit") as mock_emit:
                client.emit("search_messages", {
                    "token": "valid_token",
                    "room": "SearchRoom",
                    "search_term": "mundo"
                })
                assert mock_emit.called
                args = mock_emit.call_args[0]
                assert args[0] == "search_results"
                assert len(args[1]["results"]) == 1