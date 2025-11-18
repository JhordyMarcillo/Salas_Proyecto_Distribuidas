"""
test_rooms_endpoints.py - Tests para endpoints de Rooms
Pruebas para routes/rooms.py y services/room_service.py
"""

import pytest
import json


class TestRoomsEndpoints:
    """Tests para endpoints HTTP de salas"""
    
    def test_list_rooms_empty(self, client):
        """Test listar salas cuando está vacío"""
        response = client.get('/rooms')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['rooms'] == []
    
    def test_list_rooms_with_data(self, client, app):
        """Test listar salas con datos"""
        with app.app_context():
            from app.models import get_room_model
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.messages.delete_many({})
            mongo.db.users.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("General")
            room_model.create_room("Random")
        
        response = client.get('/rooms')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['rooms']) >= 2
        assert any(r['name'] == 'General' for r in data['rooms'])
    
    def test_get_room_details_found(self, client, app):
        """Test obtener detalles de una sala existente"""
        with app.app_context():
            from app.models import get_room_model
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            room_model = get_room_model()
            room_model.create_room("TestRoom", description="Sala de prueba")
        
        response = client.get('/rooms/TestRoom')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'TestRoom'
        assert data['description'] == 'Sala de prueba'
        assert 'created_at' in data
    
    def test_get_room_details_not_found(self, client):
        """Test obtener detalles de sala inexistente"""
        response = client.get('/rooms/NonExistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_room_summary(self, client, app):
        """Test obtener resumen completo de sala"""
        with app.app_context():
            from app.models import get_room_model, get_message_model
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.messages.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("SummaryRoom")
            
            msg_model = get_message_model()
            msg_model.create_message("SummaryRoom", "admin", msg="Test")
        
        response = client.get('/rooms/SummaryRoom/summary')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'room' in data
        assert 'stats' in data
        assert 'recent_messages' in data
    
    def test_get_room_messages_empty(self, client, app):
        """Test obtener mensajes de sala sin mensajes"""
        with app.app_context():
            from app.models import get_room_model
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.messages.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("EmptyRoom")
        
        response = client.get('/rooms/EmptyRoom/messages')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['messages'] == []
    
    def test_get_room_messages_with_data(self, client, app):
        """Test obtener mensajes de sala con datos"""
        with app.app_context():
            from app.models import get_room_model, get_message_model
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.messages.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("MessageRoom")
            
            msg_model = get_message_model()
            msg_model.create_message("MessageRoom", "user1", msg="First")
            msg_model.create_message("MessageRoom", "user2", msg="Second")
        
        response = client.get('/rooms/MessageRoom/messages')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['messages']) == 2
    
    def test_get_room_messages_limit(self, client, app):
        """Test límite de mensajes obtenidos"""
        with app.app_context():
            from app.models import get_room_model, get_message_model
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.messages.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room("LimitRoom")
            
            msg_model = get_message_model()
            for i in range(10):
                msg_model.create_message("LimitRoom", "user", msg=f"Msg {i}")
        
        response = client.get('/rooms/LimitRoom/messages?limit=5')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['messages']) == 5
    
    def test_get_room_messages_limit_exceeded(self, client):
        """Test límite máximo de mensajes excedido"""
        response = client.get('/rooms/AnyRoom/messages?limit=600')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_room_success(self, client, admin_user, app):
        """Test crear sala exitosamente"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
        
        token = admin_user['token']
        response = client.post(
            '/rooms',
            json={
                'name': 'NewRoom',
                'description': 'Nueva sala',
                'type': 'multimedia',
                'max_file_mb': 15
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['room']['name'] == 'NewRoom'
        assert data['room']['type'] == 'multimedia'
    
    def test_create_room_no_auth(self, client, app):
        """Test crear sala sin autenticación"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
        
        response = client.post('/rooms', json={'name': 'NewRoom'})
        
        assert response.status_code == 401
    
    def test_create_room_not_admin(self, client, regular_user, app):
        """Test crear sala sin privilegios de admin"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
        
        token = regular_user['token']
        response = client.post(
            '/rooms',
            json={'name': 'NewRoom'},
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 403
    
    def test_create_room_invalid_type(self, client, admin_user, app):
        """Test crear sala con tipo inválido"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
        
        token = admin_user['token']
        response = client.post(
            '/rooms',
            json={
                'name': 'BadRoom',
                'type': 'invalid_type'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_room_duplicate(self, client, admin_user, app):
        """Test crear sala duplicada"""
        with app.app_context():
            from app.models import get_room_model
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            room_model = get_room_model()
            room_model.create_room('DuplicateRoom')
        
        token = admin_user['token']
        response = client.post(
            '/rooms',
            json={'name': 'DuplicateRoom'},
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_room_missing_name(self, client, admin_user):
        """Test crear sala sin nombre"""
        token = admin_user['token']
        response = client.post(
            '/rooms',
            json={},
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_delete_room_success(self, client, admin_user, app):
        """Test eliminar sala exitosamente"""
        with app.app_context():
            from app.models import get_room_model
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.messages.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room('DeleteMe')
        
        token = admin_user['token']
        response = client.delete(
            '/rooms/DeleteMe',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['stats']['room_deleted'] is True
    
    def test_delete_room_not_found(self, client, admin_user):
        """Test eliminar sala inexistente"""
        token = admin_user['token']
        response = client.delete(
            '/rooms/NonExistent',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 404
    
    def test_delete_room_not_admin(self, client, regular_user):
        """Test eliminar sala sin privilegios"""
        token = regular_user['token']
        response = client.delete(
            '/rooms/AnyRoom',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 403
    
    def test_update_room_success(self, client, admin_user, app):
        """Test actualizar descripción de sala"""
        with app.app_context():
            from app.models import get_room_model
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            room_model = get_room_model()
            room_model.create_room('UpdateMe', description='Old')
        
        token = admin_user['token']
        response = client.patch(
            '/rooms/UpdateMe',
            json={'description': 'New Description'},
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['room']['description'] == 'New Description'
    
    def test_update_room_missing_description(self, client, admin_user):
        """Test actualizar sala sin descripción"""
        token = admin_user['token']
        response = client.patch(
            '/rooms/AnyRoom',
            json={},
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 400
    
    def test_get_room_members_empty(self, client, app):
        """Test obtener miembros de sala vacía"""
        with app.app_context():
            from app.models import get_room_model
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.users.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room('EmptyRoom')
        
        response = client.get('/rooms/EmptyRoom/members')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['members_count'] == 0
        assert data['members'] == []
    
    def test_get_room_members_not_found(self, client):
        """Test obtener miembros de sala inexistente"""
        response = client.get('/rooms/NonExistent/members')
        
        assert response.status_code == 404
    
    def test_get_global_stats(self, client, admin_user, app):
        """Test obtener estadísticas globales"""
        with app.app_context():
            from app.models import get_room_model, get_message_model
            from app.utils.database import mongo
            
            mongo.db.rooms.delete_many({})
            mongo.db.messages.delete_many({})
            
            room_model = get_room_model()
            room_model.create_room('Room1')
            room_model.create_room('Room2')
            
            msg_model = get_message_model()
            msg_model.create_message('Room1', 'user', msg='Hi')
        
        token = admin_user['token']
        response = client.get(
            '/rooms/stats',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_rooms' in data
        assert 'total_messages' in data
        assert 'total_users_online' in data
