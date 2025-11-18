"""
test_models.py - Tests para Room y Message models
Pruebas exhaustivas para cobertura 70%+
"""

import pytest
import json
from datetime import datetime
from app.models import get_room_model, get_message_model, get_user_model


class TestRoomModel:
    """Tests para el modelo Room"""
    
    def test_create_room_basic(self, app):
        """Test crear sala básica con valores mínimos"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            room = room_model.create_room("Test Room")
            
            assert room['name'] == "Test Room"
            assert room['type'] == 'text'
            assert len(room['pin']) == 6  # PIN auto-generado
            assert 'id' in room
            assert 'created_at' in room
    
    def test_create_room_multimedia(self, app):
        """Test crear sala multimedia con máximo de archivo"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            room = room_model.create_room(
                "Media Room",
                description="Sala con archivos",
                room_type="multimedia",
                max_file_mb=20
            )
            
            assert room['type'] == 'multimedia'
            assert room['max_file_mb'] == 20
            assert room['description'] == "Sala con archivos"
    
    def test_create_room_custom_pin(self, app):
        """Test crear sala con PIN personalizado"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            room = room_model.create_room(
                "Pinned Room",
                provided_pin="1234"
            )
            
            assert room['pin'] == "1234"
    
    def test_create_room_invalid_pin_short(self, app):
        """Test crear sala con PIN demasiado corto"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            with pytest.raises(ValueError, match="pin inválido"):
                room_model.create_room("Room", provided_pin="123")
    
    def test_create_room_invalid_pin_non_numeric(self, app):
        """Test crear sala con PIN no numérico"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            with pytest.raises(ValueError, match="pin inválido"):
                room_model.create_room("Room", provided_pin="abcd")
    
    def test_create_room_invalid_type(self, app):
        """Test crear sala con tipo inválido"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            with pytest.raises(ValueError, match="type inválido"):
                room_model.create_room("Room", room_type="invalid")
    
    def test_create_room_duplicate(self, app):
        """Test crear sala duplicada"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("Duplicate")
            
            with pytest.raises(ValueError, match="room ya existe"):
                room_model.create_room("Duplicate")
    
    def test_find_by_name(self, app):
        """Test buscar sala por nombre"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            created = room_model.create_room("Search Room")
            found = room_model.find_by_name("Search Room")
            
            assert found is not None
            assert found['name'] == "Search Room"
            assert found['id'] == created['id']
    
    def test_find_by_name_not_found(self, app):
        """Test buscar sala que no existe"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            found = room_model.find_by_name("NonExistent")
            
            assert found is None
    
    def test_find_by_id(self, app):
        """Test buscar sala por ID"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            created = room_model.create_room("ID Room")
            found = room_model.find_by_id(created['id'])
            
            assert found is not None
            assert found['id'] == created['id']
    
    def test_list_all(self, app):
        """Test listar todas las salas"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("Room 1")
            room_model.create_room("Room 2")
            room_model.create_room("Room 3")
            
            rooms = room_model.list_all()
            assert len(rooms) == 3
    
    def test_exists_true(self, app):
        """Test verificar que sala existe"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("Exists Room")
            
            assert room_model.exists("Exists Room") is True
    
    def test_exists_false(self, app):
        """Test verificar que sala no existe"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            
            assert room_model.exists("NonExistent") is False
    
    def test_verify_pin_correct(self, app):
        """Test verificar PIN correcto"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("PIN Room", provided_pin="9999")
            
            assert room_model.verify_pin("PIN Room", "9999") is True
    
    def test_verify_pin_incorrect(self, app):
        """Test verificar PIN incorrecto"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("PIN Room", provided_pin="9999")
            
            assert room_model.verify_pin("PIN Room", "1111") is False
    
    def test_verify_pin_nonexistent_room(self, app):
        """Test verificar PIN en sala inexistente"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            
            assert room_model.verify_pin("NonExistent", "1234") is False
    
    def test_get_type(self, app):
        """Test obtener tipo de sala"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("Text Room", room_type="text")
            room_model.create_room("Media Room", room_type="multimedia")
            
            assert room_model.get_type("Text Room") == "text"
            assert room_model.get_type("Media Room") == "multimedia"
    
    def test_get_type_nonexistent(self, app):
        """Test obtener tipo de sala inexistente"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            assert room_model.get_type("NonExistent") == "text"  # default
    
    def test_allows_files_true(self, app):
        """Test verificar que sala multimedia permite archivos"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("Media", room_type="multimedia")
            
            assert room_model.allows_files("Media") is True
    
    def test_allows_files_false(self, app):
        """Test verificar que sala texto NO permite archivos"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("Text", room_type="text")
            
            assert room_model.allows_files("Text") is False
    
    def test_get_max_file_size(self, app):
        """Test obtener máximo tamaño de archivo"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("Room", max_file_mb=25)
            
            assert room_model.get_max_file_size("Room") == 25
    
    def test_get_max_file_size_default(self, app):
        """Test obtener máximo tamaño por defecto"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("Room")
            
            assert room_model.get_max_file_size("Room") == 10
    
    def test_delete_room(self, app):
        """Test eliminar sala"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("Delete Me")
            
            result = room_model.delete_room("Delete Me")
            assert result is True
            assert room_model.exists("Delete Me") is False
    
    def test_delete_room_not_found(self, app):
        """Test eliminar sala inexistente"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            result = room_model.delete_room("NonExistent")
            
            assert result is False
    
    def test_update_description(self, app):
        """Test actualizar descripción de sala"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("Room", description="Old")
            
            updated = room_model.update_description("Room", "New Description")
            
            assert updated is not None
            assert updated['description'] == "New Description"
    
    def test_update_description_nonexistent(self, app):
        """Test actualizar descripción de sala inexistente"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            updated = room_model.update_description("NonExistent", "New")
            
            assert updated is None
    
    def test_count_all(self, app):
        """Test contar todas las salas"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("R1")
            room_model.create_room("R2")
            
            assert room_model.count_all() == 2


class TestMessageModel:
    """Tests para el modelo Message"""
    
    def test_create_message_text_only(self, app):
        """Test crear mensaje de texto"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.messages.delete_many({})
            
            message_model = get_message_model()
            msg = message_model.create_message(
                "General", "admin", msg="Hola mundo"
            )
            
            assert msg['room'] == "General"
            assert msg['username'] == "admin"
            assert msg['msg'] == "Hola mundo"
            assert 'timestamp' in msg
    
    def test_create_message_with_file(self, app):
        """Test crear mensaje con archivo adjunto"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.messages.delete_many({})
            
            message_model = get_message_model()
            msg = message_model.create_message(
                "General",
                "admin",
                msg="Documento",
                file_url="https://example.com/file.pdf",
                original_filename="documento.pdf"
            )
            
            assert msg['file_url'] == "https://example.com/file.pdf"
            assert msg['original_filename'] == "documento.pdf"
    
    def test_create_message_with_security_flags(self, app):
        """Test crear mensaje con flags de seguridad"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.messages.delete_many({})
            
            security_flags = {
                'has_encryption': True,
                'has_steganography_risk': False,
                'has_malicious_patterns': False,
                'has_suspicious_content': False,
                'risk_level': 'medium',
                'issues': ['encrypted_content']
            }
            
            message_model = get_message_model()
            msg = message_model.create_message(
                "General",
                "admin",
                msg="Mensaje secreto",
                security_flags=security_flags
            )
            
            assert msg['security_flags']['risk_level'] == 'medium'
            assert 'encrypted_content' in msg['security_flags']['issues']
    
    def test_create_message_anonymous(self, app):
        """Test crear mensaje anónimo con nickname"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.messages.delete_many({})
            
            message_model = get_message_model()
            msg = message_model.create_message(
                "General",
                "anon_123",
                msg="Mensaje anónimo",
                nickname="Visitante"
            )
            
            assert msg['nickname'] == "Visitante"
            assert msg['username'] == "anon_123"
    
    def test_get_room_messages_empty(self, app):
        """Test obtener mensajes de sala vacía"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.messages.delete_many({})
            
            message_model = get_message_model()
            messages = message_model.get_room_messages("Empty")
            
            assert messages == []
    
    def test_get_room_messages_ordered(self, app):
        """Test obtener mensajes ordenados por tiempo"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.messages.delete_many({})
            
            message_model = get_message_model()
            message_model.create_message("General", "user1", msg="Primero")
            message_model.create_message("General", "user2", msg="Segundo")
            message_model.create_message("General", "user3", msg="Tercero")
            
            messages = message_model.get_room_messages("General")
            
            assert len(messages) == 3
            assert messages[0]['msg'] == "Primero"
            assert messages[2]['msg'] == "Tercero"
    
    def test_get_room_messages_limit(self, app):
        """Test límite de mensajes obtenidos"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.messages.delete_many({})
            
            message_model = get_message_model()
            for i in range(10):
                message_model.create_message("General", "user", msg=f"Msg {i}")
            
            messages = message_model.get_room_messages("General", limit=5)
            
            assert len(messages) == 5
    
    def test_count_room_messages(self, app):
        """Test contar mensajes en sala"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.messages.delete_many({})
            
            message_model = get_message_model()
            message_model.create_message("Room1", "user", msg="Msg")
            message_model.create_message("Room1", "user", msg="Msg")
            message_model.create_message("Room2", "user", msg="Msg")
            
            assert message_model.count_room_messages("Room1") == 2
            assert message_model.count_room_messages("Room2") == 1
    
    def test_delete_room_messages(self, app):
        """Test eliminar todos los mensajes de una sala"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.messages.delete_many({})
            
            message_model = get_message_model()
            message_model.create_message("Room1", "user", msg="Msg1")
            message_model.create_message("Room1", "user", msg="Msg2")
            message_model.create_message("Room2", "user", msg="Msg3")
            
            deleted = message_model.delete_room_messages("Room1")
            
            assert deleted == 2
            assert message_model.count_room_messages("Room1") == 0
            assert message_model.count_room_messages("Room2") == 1
    
    def test_delete_user_messages(self, app):
        """Test eliminar todos los mensajes de un usuario"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.messages.delete_many({})
            
            message_model = get_message_model()
            message_model.create_message("Room1", "user1", msg="Msg")
            message_model.create_message("Room1", "user1", msg="Msg")
            message_model.create_message("Room1", "user2", msg="Msg")
            
            deleted = message_model.delete_user_messages("user1")
            
            assert deleted == 2
            assert message_model.count_room_messages("Room1") == 1
    
    def test_get_messages_with_files(self, app):
        """Test obtener solo mensajes con archivos"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.messages.delete_many({})
            
            message_model = get_message_model()
            message_model.create_message("Room1", "user", msg="Sin archivo")
            message_model.create_message(
                "Room1", "user",
                msg="Con archivo",
                file_url="https://example.com/file.pdf"
            )
            
            messages = message_model.get_messages_with_files("Room1")
            
            assert len(messages) == 1
            assert messages[0]['file_url'] is not None
    
    def test_search_messages(self, app):
        """Test buscar mensajes por término"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.messages.delete_many({})
            
            message_model = get_message_model()
            message_model.create_message("Room1", "user", msg="Python es genial")
            message_model.create_message("Room1", "user", msg="JavaScript también")
            message_model.create_message("Room1", "user", msg="Python rules")
            
            results = message_model.search_messages("Room1", "Python")
            
            assert len(results) == 2
    
    def test_get_messages_by_user(self, app):
        """Test obtener mensajes de un usuario específico"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.messages.delete_many({})
            
            message_model = get_message_model()
            message_model.create_message("Room1", "user1", msg="Msg1")
            message_model.create_message("Room1", "user1", msg="Msg2")
            message_model.create_message("Room1", "user2", msg="Msg3")
            
            messages = message_model.get_messages_by_user("Room1", "user1")
            
            assert len(messages) == 2
    
    def test_format_message_for_emit(self, app):
        """Test formatear mensaje para WebSocket"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.messages.delete_many({})
            
            message_model = get_message_model()
            msg_doc = message_model.create_message(
                "Room1",
                "user1",
                msg="Test",
                nickname="Nick"
            )
            
            formatted = message_model.format_message_for_emit(msg_doc)
            
            assert formatted['username'] == "user1"
            assert formatted['msg'] == "Test"
            assert formatted['nickname'] == "Nick"
            assert 'timestamp' in formatted
            assert 'security_flags' in formatted
    
    def test_format_messages_for_api(self, app):
        """Test formatear múltiples mensajes para API"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.messages.delete_many({})
            
            message_model = get_message_model()
            message_model.create_message("Room1", "user1", msg="Msg1")
            message_model.create_message("Room1", "user2", msg="Msg2")
            
            all_msgs = list(mongo.db.messages.find({"room": "Room1"}))
            formatted = message_model.format_messages_for_api(all_msgs)
            
            assert len(formatted) == 2
            assert formatted[0]['username'] in ["user1", "user2"]
            assert 'security_flags' in formatted[0]
