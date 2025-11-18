"""
test_services.py - Tests para services
Pruebas para room_service.py y cloudinary_service.py
"""

import pytest
import json


class TestRoomService:
    """Tests para RoomService"""
    
    def test_get_room_details_with_members_found(self, app):
        """Test obtener detalles de sala con miembros"""
        with app.app_context():
            from app.models import get_room_model
            from app.services.room_service import RoomService
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.users.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("TestRoom", description="Test")
            
            details = RoomService.get_room_details_with_members("TestRoom")
            
            assert details is not None
            assert details['name'] == 'TestRoom'
            assert details['description'] == 'Test'
            assert 'members_count' in details
            assert 'created_at' in details
    
    def test_get_room_details_with_members_not_found(self, app):
        """Test obtener detalles de sala inexistente"""
        with app.app_context():
            from app.services.room_service import RoomService
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            
            details = RoomService.get_room_details_with_members("NonExistent")
            
            assert details is None
    
    def test_list_rooms_with_stats_empty(self, app):
        """Test listar salas con estadísticas (vacío)"""
        with app.app_context():
            from app.services.room_service import RoomService
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.messages.delete_many({})
            
            rooms = RoomService.list_rooms_with_stats()
            
            assert rooms == []
    
    def test_list_rooms_with_stats(self, app):
        """Test listar salas con estadísticas"""
        with app.app_context():
            from app.models import get_room_model, get_message_model
            from app.services.room_service import RoomService
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.messages.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("Room1")
            room_model.create_room("Room2")
            
            msg_model = get_message_model()
            msg_model.create_message("Room1", "user", msg="Test")
            
            rooms = RoomService.list_rooms_with_stats()
            
            assert len(rooms) == 2
            room1 = next(r for r in rooms if r['name'] == 'Room1')
            assert room1['messages'] == 1
    
    def test_validate_join_request_valid(self, app):
        """Test validar solicitud de unirse a sala (válida)"""
        with app.app_context():
            from app.models import get_room_model, get_user_model
            from app.services.room_service import RoomService
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.users.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("JoinRoom", provided_pin="1234")
            
            user_model = get_user_model()
            user_model.create_user("testuser", "password123")
            
            valid, msg = RoomService.validate_join_request("testuser", "JoinRoom", "1234")
            
            assert valid is True
            assert msg is None
    
    def test_validate_join_request_room_not_found(self, app):
        """Test validar solicitud de unirse (sala no existe)"""
        with app.app_context():
            from app.models import get_user_model
            from app.services.room_service import RoomService
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.users.delete_many({})
            
            user_model = get_user_model()
            user_model.create_user("testuser", "password123")
            
            valid, msg = RoomService.validate_join_request("testuser", "NonExistent", None)
            
            assert valid is False
            assert "no existe" in msg.lower()
    
    def test_validate_join_request_wrong_pin(self, app):
        """Test validar solicitud con PIN incorrecto"""
        with app.app_context():
            from app.models import get_room_model, get_user_model
            from app.services.room_service import RoomService
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.users.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("PinRoom", provided_pin="1234")
            
            user_model = get_user_model()
            user_model.create_user("testuser", "password123")
            
            valid, msg = RoomService.validate_join_request("testuser", "PinRoom", "9999")
            
            assert valid is False
            assert "pin" in msg.lower()
    
    def test_validate_join_request_user_not_found(self, app):
        """Test validar solicitud de usuario inexistente"""
        with app.app_context():
            from app.models import get_room_model
            from app.services.room_service import RoomService
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.users.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("JoinRoom")
            
            valid, msg = RoomService.validate_join_request("NonExistent", "JoinRoom", None)
            
            assert valid is False
            assert msg is not None  # Hay un mensaje de error
    
    def test_can_send_file_valid(self, app):
        """Test verificar que puede enviar archivo (válido)"""
        with app.app_context():
            from app.models import get_room_model, get_user_model
            from app.services.room_service import RoomService
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.users.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("MediaRoom", room_type="multimedia", max_file_mb=10)
            
            user_model = get_user_model()
            user_model.create_user("testuser", "password123")
            user_model.update_room("testuser", "MediaRoom")
            
            can_send, msg = RoomService.can_send_file("testuser", "MediaRoom", 5)
            
            assert can_send is True
            assert msg is None
    
    def test_can_send_file_not_in_room(self, app):
        """Test verificar archivo (usuario no en sala)"""
        with app.app_context():
            from app.models import get_room_model, get_user_model
            from app.services.room_service import RoomService
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.users.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("MediaRoom", room_type="multimedia")
            
            user_model = get_user_model()
            user_model.create_user("testuser", "password123")
            
            can_send, msg = RoomService.can_send_file("testuser", "MediaRoom", 5)
            
            assert can_send is False
            assert "no estás" in msg.lower()
    
    def test_can_send_file_text_only_room(self, app):
        """Test verificar archivo en sala solo texto"""
        with app.app_context():
            from app.models import get_room_model, get_user_model
            from app.services.room_service import RoomService
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.users.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("TextRoom", room_type="text")
            
            user_model = get_user_model()
            user_model.create_user("testuser", "password123")
            user_model.update_room("testuser", "TextRoom")
            
            can_send, msg = RoomService.can_send_file("testuser", "TextRoom", 5)
            
            assert can_send is False
            assert "no permite archivos" in msg.lower()
    
    def test_can_send_file_exceeds_size(self, app):
        """Test verificar archivo excede tamaño máximo"""
        with app.app_context():
            from app.models import get_room_model, get_user_model
            from app.services.room_service import RoomService
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.users.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("SmallRoom", room_type="multimedia", max_file_mb=5)
            
            user_model = get_user_model()
            user_model.create_user("testuser", "password123")
            user_model.update_room("testuser", "SmallRoom")
            
            can_send, msg = RoomService.can_send_file("testuser", "SmallRoom", 10)
            
            assert can_send is False
            assert "excede" in msg.lower() or "exceeds" in msg.lower()
    
    def test_delete_room_cascade(self, app):
        """Test eliminar sala en cascada"""
        with app.app_context():
            from app.models import get_room_model, get_message_model, get_user_model
            from app.services.room_service import RoomService
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.messages.delete_many({})
            mongo.db.users.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("DeleteRoom")
            
            user_model = get_user_model()
            user_model.create_user("user1", "pass")
            user_model.create_user("user2", "pass")
            user_model.update_room("user1", "DeleteRoom")
            user_model.update_room("user2", "DeleteRoom")
            
            msg_model = get_message_model()
            msg_model.create_message("DeleteRoom", "user1", msg="Msg1")
            msg_model.create_message("DeleteRoom", "user2", msg="Msg2")
            
            stats = RoomService.delete_room_cascade("DeleteRoom")
            
            assert stats['room_deleted'] is True
            assert stats['messages_deleted'] == 2
            assert stats['users_cleared'] == 2
    
    def test_get_room_summary(self, app):
        """Test obtener resumen de sala"""
        with app.app_context():
            from app.models import get_room_model, get_message_model
            from app.services.room_service import RoomService
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.messages.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("SummaryRoom")
            
            msg_model = get_message_model()
            msg_model.create_message("SummaryRoom", "user", msg="Test")
            
            summary = RoomService.get_room_summary("SummaryRoom")
            
            assert summary is not None
            assert 'room' in summary
            assert 'stats' in summary
            assert 'recent_messages' in summary
            assert summary['stats']['total_messages'] == 1
    
    def test_get_room_summary_not_found(self, app):
        """Test obtener resumen de sala inexistente"""
        with app.app_context():
            from app.services.room_service import RoomService
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            
            summary = RoomService.get_room_summary("NonExistent")
            
            assert summary is None
