"""
conftest.py - Configuración compartida para todos los tests

Define fixtures globales y configuración de pytest
"""

import pytest
import json
from app import create_app
from app.utils.database import mongo
from datetime import datetime


@pytest.fixture(scope="session")
def app():
    """
    Crea una aplicación Flask con configuración de testing
    Scope: session - Se ejecuta una sola vez para toda la sesión de tests
    """
    app = create_app('testing')
    
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    with app.app_context():
        # Limpiar base de datos de testing
        mongo.db.users.delete_many({})
        mongo.db.rooms.delete_many({})
        mongo.db.messages.delete_many({})

        # ✅ Crear admin directamente en la BD de testing
        from app.utils.database import bcrypt
        if not mongo.db.users.find_one({'username': 'admin'}):
            pw_hash = bcrypt.generate_password_hash('admin_password_123').decode()
            mongo.db.users.insert_one({
                'username': 'admin',
                'password': pw_hash,
                'is_admin': True,
                'created_at': datetime.utcnow(),
                'socket_id': None,
                'current_room': None
            })

        yield app.test_client()

        # Limpiar después
        mongo.db.users.delete_many({})
        mongo.db.rooms.delete_many({})
        mongo.db.messages.delete_many({})


@pytest.fixture
def app_context(app):
    """
    Contexto de aplicación para tests que lo necesiten
    """
    with app.app_context():
        yield app


@pytest.fixture
def admin_user(client, app):
    """
    Retorna el usuario admin creado en la fixture client
    Ya existe en MongoDB con is_admin=True
    
    Returns:
        dict: {
            'username': 'admin',
            'token': 'eyJ...',
            'is_admin': True
        }
    """
    with app.app_context():
        # Obtener token del admin que ya existe
        response = client.post('/auth/login', json={
            'username': 'admin',
            'password': 'admin_password_123'
        })

        if response.status_code != 200:
            raise ValueError(f"No se pudo obtener token de admin: {response.data}")

        data = json.loads(response.data)

        return {
            'username': 'admin',
            'token': data['token'],
            'is_admin': True
        }

@pytest.fixture
def regular_user(client, app):
    """
    Crea un usuario regular y retorna su token
    
    Returns:
        dict: {
            'username': 'user1',
            'token': 'eyJ...',
            'is_admin': False
        }
    """
    with app.app_context():
        response = client.post('/auth/register', json={
            'username': 'user1',
            'password': 'user_password_123'
        })
        
        data = json.loads(response.data)
        
        return {
            'username': 'user1',
            'password': 'user_password_123',
            'token': data['token'],
            'is_admin': data['user']['is_admin']
        }


@pytest.fixture
def multiple_users(client):
    """
    Crea múltiples usuarios para tests
    
    Returns:
        list: Lista de usuarios con tokens
    """
    users = []
    
    for i in range(5):
        username = f'user{i}'
        password = f'password_{i}'
        
        response = client.post('/auth/register', json={
            'username': username,
            'password': password
        })
        
        data = json.loads(response.data)
        
        users.append({
            'username': username,
            'password': password,
            'token': data['token'],
            'is_admin': data['user']['is_admin']
        })
    
    return users


@pytest.fixture
def public_room(client, admin_user):
    """
    Crea una sala pública para tests
    
    Returns:
        dict: Información de la sala
    """
    response = client.post(
        '/rooms',
        headers={'Authorization': f'Bearer {admin_user["token"]}'},
        json={
            'name': 'TestRoom',
            'description': 'Test room',
            'is_private': False
        }
    )
    
    data = json.loads(response.data)
    return data['room']


@pytest.fixture
def private_room(client, admin_user):
    """
    Crea una sala privada con PIN para tests
    
    Returns:
        dict: Información de la sala con PIN
    """
    response = client.post(
        '/rooms',
        headers={'Authorization': f'Bearer {admin_user["token"]}'},
        json={
            'name': 'PrivateRoom',
            'description': 'Private test room',
            'is_private': True,
            'pin': '1234'
        }
    )
    
    data = json.loads(response.data)
    
    return {
        **data['room'],
        'pin': '1234'  # Incluir el PIN para verificación
    }


@pytest.fixture
def populated_room(client, admin_user):
    """
    Crea una sala pública y le añade usuarios
    
    Returns:
        dict: {
            'room': {...},
            'users': [...]
        }
    """
    # Crear sala
    room_response = client.post(
        '/rooms',
        headers={'Authorization': f'Bearer {admin_user["token"]}'},
        json={'name': 'PopulatedRoom', 'is_private': False}
    )
    
    room = json.loads(room_response.data)['room']
    
    # Crear y añadir usuarios
    users = []
    for i in range(3):
        user_response = client.post('/auth/register', json={
            'username': f'popuser{i}',
            'password': f'pass{i}'
        })
        
        user_data = json.loads(user_response.data)
        
        # Unir usuario a sala
        client.post(
            f'/rooms/{room["name"]}/join',
            headers={'Authorization': f'Bearer {user_data["token"]}'},
            json={}
        )
        
        users.append({
            'username': f'popuser{i}',
            'token': user_data['token']
        })
    
    return {
        'room': room,
        'users': users
    }


@pytest.fixture
def sample_token(client):
    """
    Obtiene un token JWT válido para tests
    
    Returns:
        str: Token JWT válido
    """
    response = client.post('/auth/register', json={
        'username': 'tokenuser',
        'password': 'tokenpass123'
    })
    
    data = json.loads(response.data)
    return data['token']


@pytest.fixture
def invalid_token():
    """
    Proporciona un token JWT inválido
    
    Returns:
        str: Token inválido
    """
    return 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.invalid'


@pytest.fixture
def expired_token():
    """
    Proporciona un token JWT expirado
    
    Returns:
        str: Token expirado
    """
    # Simulación de token expirado (en tests reales se usaría JWT con fecha expirada)
    return 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjB9.expired'


@pytest.fixture
def auth_headers(sample_token):
    """
    Headers con autenticación para requests
    
    Returns:
        dict: Headers con Authorization Bearer
    """
    return {'Authorization': f'Bearer {sample_token}'}


@pytest.fixture
def content_type_json():
    """
    Headers con Content-Type JSON
    
    Returns:
        dict: Headers
    """
    return {'Content-Type': 'application/json'}


# Marcadores personalizados para pytest
def pytest_configure(config):
    """Registra marcadores personalizados"""
    config.addinivalue_line(
        "markers", "slow: marca tests que son lentos"
    )
    config.addinivalue_line(
        "markers", "integration: marca tests de integración"
    )
    config.addinivalue_line(
        "markers", "unit: marca tests unitarios"
    )
    config.addinivalue_line(
        "markers", "socket: marca tests de WebSocket"
    )
    config.addinivalue_line(
        "markers", "security: marca tests de seguridad"
    )


# Hooks para logging de tests
def pytest_runtest_logreport(report):
    """Hook para reporting de tests"""
    if report.when == "call":
        if report.outcome == "failed":
            print(f"\n[FAIL] {report.nodeid}")
            print(f"   {report.longrepr}")
        elif report.outcome == "passed":
            print(f"[PASS] {report.nodeid}")


# Configuración de timeout para tests
def pytest_configure(config):
    """Añade timeout a todos los tests"""
    config.addinivalue_line(
        "markers", "timeout(seconds): marque el test con un timeout"
    )


# Fixture para manejo de errores en tests
@pytest.fixture
def assert_error_response():
    """
    Utilidad para verificar respuestas de error
    
    Returns:
        function: Función de validación
    """
    def _assert_error(response, expected_status=None, error_msg=None):
        if expected_status:
            assert response.status_code == expected_status, \
                f"Expected status {expected_status}, got {response.status_code}"
        
        data = json.loads(response.data)
        assert 'error' in data, f"Expected 'error' in response, got {data}"
        
        if error_msg:
            assert error_msg.lower() in data['error'].lower(), \
                f"Expected '{error_msg}' in error message, got '{data['error']}'"
        
        return data
    
    return _assert_error


# Fixture para manejo de respuestas exitosas
@pytest.fixture
def assert_success_response():
    """
    Utilidad para verificar respuestas exitosas
    
    Returns:
        function: Función de validación
    """
    def _assert_success(response, expected_status=200, required_fields=None):
        assert response.status_code == expected_status, \
            f"Expected status {expected_status}, got {response.status_code}"
        
        data = json.loads(response.data)
        
        if required_fields:
            for field in required_fields:
                assert field in data, f"Expected '{field}' in response, got {data}"
        
        return data
    
    return _assert_success


# Limpieza después de todos los tests
def pytest_sessionfinish(session, exitstatus):
    """
    Hook ejecutado al finalizar la sesión de tests
    """
    # Limpiar recursos si es necesario
    pass
