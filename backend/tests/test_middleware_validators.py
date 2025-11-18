"""
test_middleware_validators.py - Tests para middleware/auth.py y validators.py
"""

import pytest
import json
from app.middleware import require_jwt_http, require_admin, optional_auth_http
from app.utils.validators import Validators, ValidationError


class TestMiddlewareAuth:
    """Tests para decoradores de autenticación"""
    
    def test_require_jwt_http_valid_token(self, client, admin_user, app):
        """Test acceso con token JWT válido"""
        with app.app_context():
            # Usar endpoint que requiere JWT
            token = admin_user['token']
            response = client.get(
                '/rooms/stats',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 200
    
    def test_require_jwt_http_missing_token(self, client):
        """Test acceso sin token JWT"""
        response = client.get('/rooms/stats')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'msg' in data
    
    def test_require_jwt_http_invalid_format(self, client):
        """Test token con formato inválido (sin 'Bearer')"""
        response = client.get(
            '/rooms/stats',
            headers={'Authorization': 'InvalidToken'}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'format' in data['msg'].lower() or 'formato' in data['msg'].lower()
    
    def test_require_jwt_http_expired_token(self, client, app):
        """Test token expirado"""
        with app.app_context():
            from app.services.jwt_service import JWTService
            
            # Crear token con tiempo muy corto
            expired_token = JWTService.create_token("testuser", expires_hours=-1)
            
            response = client.get(
                '/rooms/stats',
                headers={'Authorization': f'Bearer {expired_token}'}
            )
            
            assert response.status_code == 401
            data = json.loads(response.data)
            assert 'token_invalid' in data.get('code', '') or 'token_expired' in data.get('code', '')
    
    def test_require_jwt_http_malformed_token(self, client):
        """Test token malformado"""
        response = client.get(
            '/rooms/stats',
            headers={'Authorization': 'Bearer malformed.token'}
        )
        
        assert response.status_code == 401
    
    def test_require_admin_with_admin_user(self, client, admin_user, app):
        """Test crear sala como admin"""
        with app.app_context():
            from app.utils.database import mongo
            mongo.db.rooms.delete_many({})
        
        token = admin_user['token']
        response = client.post(
            '/rooms',
            json={'name': 'AdminRoom'},
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 201
    
    def test_require_admin_with_regular_user(self, client, regular_user):
        """Test crear sala como usuario regular"""
        token = regular_user['token']
        response = client.post(
            '/rooms',
            json={'name': 'RegularRoom'},
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'privilegios' in data['msg'].lower() or 'insufficient' in data['msg'].lower()
    
    def test_optional_auth_http_with_token(self, client, admin_user):
        """Test endpoint opcional con token válido"""
        token = admin_user['token']
        response = client.get(
            '/rooms',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
    
    def test_optional_auth_http_without_token(self, client):
        """Test endpoint opcional sin token"""
        response = client.get('/rooms')
        
        assert response.status_code == 200
    
    def test_optional_auth_http_invalid_token(self, client):
        """Test endpoint opcional con token inválido"""
        # Debe continuar con username=None
        response = client.get(
            '/rooms',
            headers={'Authorization': 'Bearer invalid'}
        )
        
        assert response.status_code == 200


class TestValidators:
    """Tests para validadores de datos"""
    
    def test_validate_username_valid(self):
        """Test validar username válido"""
        result = Validators.validate_username("user_123")
        assert result == "user_123"
    
    def test_validate_username_empty(self):
        """Test validar username vacío"""
        with pytest.raises(ValidationError):
            Validators.validate_username("")
    
    def test_validate_username_whitespace(self):
        """Test validar username solo espacios"""
        with pytest.raises(ValidationError):
            Validators.validate_username("   ")
    
    def test_validate_username_too_short(self):
        """Test validar username muy corto"""
        with pytest.raises(ValidationError, match="al menos 3"):
            Validators.validate_username("ab")
    
    def test_validate_username_too_long(self):
        """Test validar username muy largo"""
        with pytest.raises(ValidationError, match="exceder 50"):
            Validators.validate_username("a" * 51)
    
    def test_validate_username_invalid_chars(self):
        """Test validar username con caracteres inválidos"""
        with pytest.raises(ValidationError, match="letras, números y guión bajo"):
            Validators.validate_username("user@host")
    
    def test_validate_username_with_spaces(self):
        """Test validar username con espacios"""
        with pytest.raises(ValidationError):
            Validators.validate_username("user name")
    
    def test_validate_username_trim_spaces(self):
        """Test validar username con espacios al inicio/final"""
        result = Validators.validate_username("  user123  ")
        assert result == "user123"
    
    def test_validate_password_valid(self):
        """Test validar contraseña válida"""
        result = Validators.validate_password("secure_pass_123")
        assert result == "secure_pass_123"
    
    def test_validate_password_empty(self):
        """Test validar contraseña vacía"""
        with pytest.raises(ValidationError):
            Validators.validate_password("")
    
    def test_validate_password_too_short(self):
        """Test validar contraseña muy corta"""
        with pytest.raises(ValidationError, match="al menos 6"):
            Validators.validate_password("12345")
    
    def test_validate_password_too_long(self):
        """Test validar contraseña muy larga"""
        with pytest.raises(ValidationError, match="exceder 128"):
            Validators.validate_password("a" * 129)
    
    def test_validate_email_valid(self):
        """Test validar email válido"""
        result = Validators.validate_email("user@example.com")
        assert result == "user@example.com"
    
    def test_validate_email_invalid(self):
        """Test validar email inválido"""
        with pytest.raises(ValidationError):
            Validators.validate_email("invalid-email")
    
    def test_validate_email_empty(self):
        """Test validar email vacío"""
        with pytest.raises(ValidationError):
            Validators.validate_email("")
    
    def test_validate_room_name_valid(self):
        """Test validar nombre de sala válido"""
        result = Validators.validate_room_name("General Chat")
        assert result == "General Chat"
    
    def test_validate_room_name_empty(self):
        """Test validar nombre de sala vacío"""
        with pytest.raises(ValidationError):
            Validators.validate_room_name("")
    
    def test_validate_room_name_too_long(self):
        """Test validar nombre de sala muy largo"""
        with pytest.raises(ValidationError):
            Validators.validate_room_name("a" * 101)
    
    def test_validate_pin_valid(self):
        """Test validar PIN válido"""
        result = Validators.validate_pin("123456")
        assert result == "123456"
    
    def test_validate_pin_short(self):
        """Test validar PIN muy corto"""
        with pytest.raises(ValidationError):
            Validators.validate_pin("123")
    
    def test_validate_pin_non_numeric(self):
        """Test validar PIN no numérico"""
        with pytest.raises(ValidationError):
            Validators.validate_pin("abcdef")
    
    def test_validate_message_valid(self):
        """Test validar mensaje válido"""
        result = Validators.validate_message("Mensaje de prueba")
        assert result == "Mensaje de prueba"
    
    def test_validate_message_empty(self):
        """Test validar mensaje vacío"""
        with pytest.raises(ValidationError):
            Validators.validate_message("")
    
    def test_validate_filename_valid(self):
        """Test validar nombre de archivo válido"""
        result = Validators.validate_filename("document.pdf")
        assert "pdf" in result
    
    def test_validate_filename_no_extension(self):
        """Test validar archivo sin extensión"""
        with pytest.raises(ValidationError):
            Validators.validate_filename("documento")
    
    def test_validate_file_size_valid(self):
        """Test validar tamaño de archivo válido"""
        # 5MB
        result = Validators.validate_file_size(5 * 1024 * 1024, max_mb=10)
        assert result is True
    
    def test_validate_file_size_too_large(self):
        """Test validar archivo demasiado grande"""
        # 15MB max es 10MB - debería lanzar excepción
        with pytest.raises(ValidationError):
            Validators.validate_file_size(15 * 1024 * 1024, max_mb=10)
    
    def test_validate_room_type_valid(self):
        """Test validar tipo de sala válido"""
        result = Validators.validate_room_type("multimedia")
        assert result == "multimedia"
    
    def test_validate_room_type_invalid(self):
        """Test validar tipo de sala inválido"""
        with pytest.raises(ValidationError):
            Validators.validate_room_type("invalid_type")
