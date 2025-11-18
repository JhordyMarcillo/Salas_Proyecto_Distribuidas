"""
Tests para rutas de autenticación
Prueba registro, login, verificación de tokens
"""

import pytest
import json
from app.utils.database import mongo


class TestRegister:
    """Tests para el endpoint POST /auth/register"""
    
    def test_register_success(self, client):
        """Debe registrar un usuario exitosamente"""
        response = client.post('/auth/register', json={
            'username': 'testuser',
            'password': 'password123'
        })
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'token' in data
        assert data['user']['username'] == 'testuser'
        assert data['user']['is_admin'] == False
    
    def test_register_duplicate_user(self, client):
        """No debe permitir registrar usuarios duplicados"""
        # Registrar usuario
        client.post('/auth/register', json={
            'username': 'testuser',
            'password': 'password123'
        })
        
        # Intentar registrar de nuevo
        response = client.post('/auth/register', json={
            'username': 'testuser',
            'password': 'password123'
        })
        
        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_register_missing_fields(self, client):
        """Debe validar que username y password estén presentes"""
        # Sin username
        response = client.post('/auth/register', json={
            'password': 'password123'
        })
        assert response.status_code == 400
        
        # Sin password
        response = client.post('/auth/register', json={
            'username': 'testuser'
        })
        assert response.status_code == 400
    
    def test_register_short_username(self, client):
        """Username debe tener al menos 3 caracteres"""
        response = client.post('/auth/register', json={
            'username': 'ab',
            'password': 'password123'
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_register_short_password(self, client):
        """Password debe tener al menos 6 caracteres"""
        response = client.post('/auth/register', json={
            'username': 'testuser',
            'password': '12345'
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_register_invalid_username_chars(self, client):
        """Username solo debe contener letras, números y guión bajo"""
        response = client.post('/auth/register', json={
            'username': 'test@user',
            'password': 'password123'
        })
        
        assert response.status_code == 400


class TestLogin:
    """Tests para el endpoint POST /auth/login"""
    
    def test_login_success(self, client):
        """Debe hacer login exitosamente"""
        # Registrar usuario primero
        client.post('/auth/register', json={
            'username': 'testuser',
            'password': 'password123'
        })
        
        # Hacer login
        response = client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'token' in data
        assert data['user']['username'] == 'testuser'
    
    def test_login_invalid_credentials(self, client):
        """Debe rechazar credenciales inválidas"""
        response = client.post('/auth/login', json={
            'username': 'nonexistent',
            'password': 'password123'
        })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_login_wrong_password(self, client):
        """Debe rechazar contraseña incorrecta"""
        # Registrar usuario
        client.post('/auth/register', json={
            'username': 'testuser',
            'password': 'password123'
        })
        
        # Intentar login con password incorrecto
        response = client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
    
    def test_login_missing_fields(self, client):
        """Debe validar campos requeridos"""
        response = client.post('/auth/login', json={
            'username': 'testuser'
        })
        
        assert response.status_code == 400


class TestVerifyToken:
    """Tests para el endpoint POST /auth/verify"""
    
    def test_verify_token_success(self, client):
        """Debe verificar un token válido"""
        # Registrar y obtener token
        reg_response = client.post('/auth/register', json={
            'username': 'testuser',
            'password': 'password123'
        })
        token = json.loads(reg_response.data)['token']
        
        # Verificar token
        response = client.post('/auth/verify', json={
            'token': token
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['valid'] == True
        assert data['username'] == 'testuser'
    
    def test_verify_invalid_token(self, client):
        """Debe rechazar un token inválido"""
        response = client.post('/auth/verify', json={
            'token': 'invalid.token.here'
        })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['valid'] == False
    
    def test_verify_missing_token(self, client):
        """Debe validar que se proporcione un token"""
        response = client.post('/auth/verify', json={})
        
        assert response.status_code == 400


class TestGetCurrentUser:
    """Tests para el endpoint GET /auth/me"""
    
    def test_get_current_user(self, client):
        """Debe obtener datos del usuario autenticado"""
        # Registrar usuario
        reg_response = client.post('/auth/register', json={
            'username': 'testuser',
            'password': 'password123'
        })
        token = json.loads(reg_response.data)['token']
        
        # Obtener datos del usuario
        response = client.get(
            '/auth/me',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['username'] == 'testuser'
    
    def test_get_current_user_without_token(self, client):
        """Debe rechazar sin token"""
        response = client.get('/auth/me')
        
        assert response.status_code == 401
    
    def test_get_current_user_invalid_token(self, client):
        """Debe rechazar con token inválido"""
        response = client.get(
            '/auth/me',
            headers={'Authorization': 'Bearer invalid.token'}
        )
        
        assert response.status_code == 401


class TestListUsers:
    """Tests para el endpoint GET /auth/users"""
    
    def test_list_users(self, client):
        """Debe listar todos los usuarios"""
        # Registrar usuario
        reg_response = client.post('/auth/register', json={
            'username': 'testuser',
            'password': 'password123'
        })
        token = json.loads(reg_response.data)['token']
        
        # Listar usuarios
        response = client.get(
            '/auth/users',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'users' in data
        assert len(data['users']) >= 1
    
    def test_list_users_without_token(self, client):
        """Debe rechazar sin token"""
        response = client.get('/auth/users')
        
        assert response.status_code == 401


class TestAdminFunctionality:
    """Tests para funcionalidades de admin"""
    
    def test_admin_user_created(self, client, app):
        """Debe crear usuario admin durante seed"""
        with app.app_context():
            admin = mongo.db.users.find_one({'username': 'admin'})
            assert admin is not None
            assert admin.get('is_admin') == True
