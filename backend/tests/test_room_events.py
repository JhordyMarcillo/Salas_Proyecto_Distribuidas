"""
Tests para app/sockets/room_events.py
"""

import pytest
from unittest.mock import patch
from app import create_app
from app.sockets.room_events import register_room_events
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
    register_room_events(socketio)
    return socketio


@pytest.fixture
def client(app, socketio):
    return socketio.test_client(app, flask_test_client=app.test_client())


def test_join_room_success(client, app):
    with app.app_context():
        mongo.db.users.delete_many({})
        mongo.db.rooms.delete_many({})
        from app.models import get_user_model, get_room_model
        user_model = get_user_model()
        room_model = get_room_model()
        user_model.create_user("testuser", "password123")
        room_model.create_room("JoinTestRoom", provided_pin="1234")

        with patch.object(JWTService, "verify_token", return_value="testuser"):
            with patch("app.sockets.room_events.emit") as mock_emit, \
                 patch("app.sockets.room_events.join_room") as mock_join:

                client.emit("join", {
                    "token": "valid_token",
                    "room": "JoinTestRoom",
                    "pin": "1234"
                })

                assert mock_emit.called
                args = mock_emit.call_args_list[0][0]
                assert args[0] == "join_success"
                assert mock_join.called


def test_join_room_wrong_pin(client, app):
    with app.app_context():
        mongo.db.rooms.delete_many({})
        from app.models import get_room_model
        room_model = get_room_model()
        room_model.create_room("PinTestRoom", provided_pin="1234")

        with patch.object(JWTService, "verify_token", return_value="testuser"):
            with patch("app.sockets.room_events.emit") as mock_emit:
                client.emit("join", {
                    "token": "valid_token",
                    "room": "PinTestRoom",
                    "pin": "0000"
                })
                assert mock_emit.called
                args = mock_emit.call_args[0]
                assert args[0] == "join_error"
                assert "PIN inválido" in args[1]["msg"]


def test_leave_room(client, app):
    with app.app_context():
        mongo.db.users.delete_many({})
        mongo.db.rooms.delete_many({})
        from app.models import get_user_model, get_room_model
        user_model = get_user_model()
        room_model = get_room_model()
        user_model.create_user("testuser", "password123")
        user_model.update_room("testuser", "LeaveTestRoom")
        room_model.create_room("LeaveTestRoom")

        with patch.object(JWTService, "verify_token", return_value="testuser"):
            with patch("app.sockets.room_events.emit") as mock_emit, \
                 patch("app.sockets.room_events.leave_room") as mock_leave:

                client.emit("leave", {
                    "token": "valid_token",
                    "room": "LeaveTestRoom"
                })

                assert mock_emit.called
                args = mock_emit.call_args_list[0][0]
                assert args[0] == "leave_success"
                assert mock_leave.called


def test_get_room_info(client, app):
    with app.app_context():
        mongo.db.rooms.delete_many({})
        from app.models import get_room_model
        room_model = get_room_model()
        room_model.create_room("InfoTestRoom")

        with patch.object(JWTService, "verify_token", return_value="testuser"):
            with patch("app.sockets.room_events.emit") as mock_emit:
                client.emit("get_room_info", {
                    "token": "valid_token",
                    "room": "InfoTestRoom"
                })
                assert mock_emit.called
                args = mock_emit.call_args[0]
                assert args[0] == "room_info"
                assert args[1]["name"] == "InfoTestRoom"


def test_list_rooms(client, app):
    with app.app_context():
        mongo.db.rooms.delete_many({})
        from app.models import get_room_model
        room_model = get_room_model()
        room_model.create_room("General")

        with patch("app.sockets.room_events.emit") as mock_emit:
            client.emit("list_rooms", {})
            args = mock_emit.call_args[0]
            assert args[0] == "rooms_list"
            assert len(args[1]["rooms"]) >= 1


def test_get_members(client, app):
    with app.app_context():
        mongo.db.users.delete_many({})
        mongo.db.rooms.delete_many({})
        from app.models import get_user_model, get_room_model
        user_model = get_user_model()
        room_model = get_room_model()
        user_model.create_user("testuser", "password123")
        user_model.update_room("testuser", "MembersTestRoom")
        room_model.create_room("MembersTestRoom")

        with patch.object(JWTService, "verify_token", return_value="testuser"):
            with patch("app.sockets.room_events.emit") as mock_emit:
                client.emit("get_members", {
                    "token": "valid_token",
                    "room": "MembersTestRoom"
                })
                assert mock_emit.called
                args = mock_emit.call_args[0]
                assert args[0] == "members_list"
                assert args[1]["count"] >= 1