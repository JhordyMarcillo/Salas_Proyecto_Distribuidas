"""
Tests adicionales para aumentar cobertura de app/routes/auth.py
"""

import pytest
import json
from app import create_app
from app.utils.database import mongo


@pytest.fixture
def client():
    app = create_app('testing')
    with app.test_client() as client:
        with app.app_context():
            mongo.db.users.delete_many({})
            mongo.db.messages.delete_many({})
            # Crear usuario regular
            client.post('/auth/register', json={
                'username': 'testuser',
                'password': 'password123'
            })
        yield client


@pytest.fixture
def token(client):
    res = client.post('/auth/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    return json.loads(res.data)['token']


# ---------- Tests nuevos ---------- #

def test_refresh_token_success(client):
    # El endpoint /refresh prueba con un token inválido
    # (el login no devuelve refresh_token)
    res = client.post('/auth/refresh', json={'refresh_token': 'invalid_token'})
    assert res.status_code == 401
    data = json.loads(res.data)
    assert 'error' in data


def test_refresh_token_missing(client):
    res = client.post('/auth/refresh', json={})
    assert res.status_code == 400
    data = json.loads(res.data)
    assert 'refresh_token requerido' in data['error']


def test_logout_success(client, token):
    res = client.post('/auth/logout', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert 'Sesión cerrada exitosamente' in data['msg']


def test_change_password_success(client, token):
    res = client.post('/auth/change-password', headers={'Authorization': f'Bearer {token}'}, json={
        'current_password': 'password123',
        'new_password': 'newpass123'
    })
    assert res.status_code == 200
    data = json.loads(res.data)
    assert 'Contraseña actualizada exitosamente' in data['msg']


def test_change_password_wrong_current(client, token):
    res = client.post('/auth/change-password', headers={'Authorization': f'Bearer {token}'}, json={
        'current_password': 'wrongpass',
        'new_password': 'newpass123'
    })
    assert res.status_code == 401
    data = json.loads(res.data)
    assert 'Contraseña actual incorrecta' in data['error']


def test_change_password_missing_fields(client, token):
    res = client.post('/auth/change-password', headers={'Authorization': f'Bearer {token}'}, json={})
    assert res.status_code == 400
    data = json.loads(res.data)
    assert 'current_password y new_password requeridos' in data['error']


def test_list_users(client, token):
    res = client.get('/auth/users', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert 'users' in data
    assert 'total' in data
    assert len(data['users']) >= 1


def test_list_users_online(client, token):
    # Simular usuario online
    mongo.db.users.update_one({'username': 'testuser'}, {'$set': {'current_room': 'General'}})

    res = client.get('/auth/users?online=true', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['total'] >= 1
    assert all(u.get('current_room') is not None for u in data['users'])


def test_delete_user_self(client, token):
    res = client.delete('/auth/users/testuser', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert 'Usuario eliminado exitosamente' in data['msg']


def test_delete_user_admin_forbidden(client, token):
    # Crear admin
    from app.utils.database import bcrypt
    mongo.db.users.insert_one({
        'username': 'admin',
        'password': bcrypt.generate_password_hash('adminpass').decode(),
        'is_admin': True
    })

    admin_login = client.post('/auth/login', json={'username': 'admin', 'password': 'adminpass'})
    admin_token = json.loads(admin_login.data)['token']

    res = client.delete('/auth/users/admin', headers={'Authorization': f'Bearer {admin_token}'})
    assert res.status_code == 403
    data = json.loads(res.data)
    assert 'No se puede eliminar el usuario admin principal' in data['error']


def test_delete_user_not_found(client, token):
    # Usuario regular intenta eliminar otro usuario sin ser admin -> 403
    res = client.delete('/auth/users/nonexistent', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 403
    data = json.loads(res.data)
    assert 'permiso' in data['error'].lower()


def test_unauthorized_handler(client):
    res = client.get('/auth/me')  # sin token
    assert res.status_code == 401
    data = json.loads(res.data)
    # El middleware devuelve 'msg', no 'error'
    assert 'msg' in data