# app/routes/auth.py
"""
Rutas HTTP para Autenticación
Endpoints REST para registro, login, refresh token, etc.
"""

from flask import Blueprint, request, jsonify
from app.middleware import require_jwt_http
from app.models import get_user_model
from app.services import JWTService

# Crear Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    POST /auth/register
    Registra un nuevo usuario
    
    Body:
        {
            "username": "nuevo_usuario",
            "password": "password123"
        }
    
    Response:
        {
            "msg": "Usuario creado exitosamente",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "user": {
                "username": "nuevo_usuario",
                "is_admin": false
            }
        }
    """
    data = request.get_json() or {}
    
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    
    # Validaciones básicas
    if not username or not password:
        return jsonify({'error': 'username y password son requeridos'}), 400
    
    if len(username) < 3:
        return jsonify({'error': 'username debe tener al menos 3 caracteres'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'password debe tener al menos 6 caracteres'}), 400
    
    # Validar caracteres permitidos en username
    if not username.isalnum() and '_' not in username:
        return jsonify({'error': 'username solo puede contener letras, números y guión bajo'}), 400
    
    user_model = get_user_model()
    
    # Verificar si el usuario ya existe
    if user_model.exists(username):
        return jsonify({'error': 'El usuario ya existe'}), 409
    
    try:
        # Crear usuario
        user_model.create_user(username, password, is_admin=False)
        
        # Generar token
        token = JWTService.create_token(username)
        
        print(f"[register] Usuario '{username}' registrado exitosamente")
        
        return jsonify({
            'msg': 'Usuario creado exitosamente',
            'token': token,
            'user': {
                'username': username,
                'is_admin': False
            }
        }), 201
        
    except Exception as e:
        print(f"[register error] {str(e)}")
        return jsonify({'error': f'Error al crear usuario: {str(e)}'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /auth/login
    Inicia sesión de un usuario
    
    Body:
        {
            "username": "admin",
            "password": "admin123"
        }
    
    Response:
        {
            "msg": "Login exitoso",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "user": {
                "username": "admin",
                "is_admin": true
            }
        }
    """
    data = request.get_json() or {}
    
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    
    # Validaciones básicas
    if not username or not password:
        return jsonify({'error': 'username y password son requeridos'}), 400
    
    user_model = get_user_model()
    
    # Buscar usuario
    user = user_model.find_by_username(username)
    if not user:
        return jsonify({'error': 'Credenciales inválidas'}), 401
    
    # Verificar contraseña
    if not user_model.verify_password(user, password):
        return jsonify({'error': 'Credenciales inválidas'}), 401
    
    # Generar token
    token = JWTService.create_token(username)
    
    print(f"[login] Usuario '{username}' inició sesión")
    
    return jsonify({
        'msg': 'Login exitoso',
        'token': token,
        'user': {
            'username': username,
            'is_admin': user.get('is_admin', False),
            'created_at': user.get('created_at').isoformat() if user.get('created_at') else None
        }
    }), 200


@auth_bp.route('/me', methods=['GET'])
@require_jwt_http
def get_current_user(username):
    """
    GET /auth/me
    Obtiene información del usuario autenticado
    
    Headers:
        Authorization: Bearer <token>
    
    Response:
        {
            "username": "admin",
            "is_admin": true,
            "current_room": "General",
            "created_at": "2025-01-15T10:30:00"
        }
    """
    user_model = get_user_model()
    user = user_model.find_by_username(username)
    
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    return jsonify({
        'username': user.get('username'),
        'is_admin': user.get('is_admin', False),
        'current_room': user.get('current_room'),
        'created_at': user.get('created_at').isoformat() if user.get('created_at') else None
    }), 200


@auth_bp.route('/verify', methods=['POST'])
def verify_token():
    """
    POST /auth/verify
    Verifica si un token es válido
    
    Body:
        {
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
    
    Response:
        {
            "valid": true,
            "username": "admin",
            "expires_at": "2025-01-16T10:30:00"
        }
        
        O si es inválido:
        {
            "valid": false,
            "error": "Token expirado"
        }
    """
    data = request.get_json() or {}
    token = data.get('token')
    
    if not token:
        return jsonify({'error': 'Token requerido'}), 400
    
    try:
        username = JWTService.verify_token(token)
        expiration = JWTService.get_token_expiration(token)
        
        return jsonify({
            'valid': True,
            'username': username,
            'expires_at': expiration.isoformat() if expiration else None
        }), 200
        
    except ValueError as e:
        error_msg = 'Token inválido'
        if str(e) == 'token_expired':
            error_msg = 'Token expirado'
        
        return jsonify({
            'valid': False,
            'error': error_msg
        }), 401


@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """
    POST /auth/refresh
    Genera un nuevo token usando un refresh token
    
    Body:
        {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
    
    Response:
        {
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
    """
    data = request.get_json() or {}
    refresh_token = data.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'error': 'refresh_token requerido'}), 400
    
    try:
        # Verificar refresh token
        username = JWTService.verify_refresh_token(refresh_token)
        
        # Generar nuevos tokens
        new_token = JWTService.create_token(username)
        new_refresh_token = JWTService.create_refresh_token(username)
        
        return jsonify({
            'token': new_token,
            'refresh_token': new_refresh_token
        }), 200
        
    except ValueError as e:
        error_msg = 'Refresh token inválido'
        if str(e) == 'token_expired':
            error_msg = 'Refresh token expirado'
        
        return jsonify({'error': error_msg}), 401


@auth_bp.route('/logout', methods=['POST'])
@require_jwt_http
def logout(username):
    """
    POST /auth/logout
    Cierra sesión del usuario (limpia socket_id y current_room)
    
    Headers:
        Authorization: Bearer <token>
    
    Response:
        {
            "msg": "Sesión cerrada exitosamente"
        }
    """
    user_model = get_user_model()
    
    # Limpiar socket_id y current_room
    from app.utils.database import mongo
    mongo.db.users.update_one(
        {"username": username},
        {"$set": {"socket_id": None, "current_room": None}}
    )
    
    print(f"[logout] Usuario '{username}' cerró sesión")
    
    return jsonify({'msg': 'Sesión cerrada exitosamente'}), 200


@auth_bp.route('/change-password', methods=['POST'])
@require_jwt_http
def change_password(username):
    """
    POST /auth/change-password
    Cambia la contraseña del usuario autenticado
    
    Headers:
        Authorization: Bearer <token>
    
    Body:
        {
            "current_password": "old_password",
            "new_password": "new_password"
        }
    
    Response:
        {
            "msg": "Contraseña actualizada exitosamente"
        }
    """
    data = request.get_json() or {}
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'current_password y new_password requeridos'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'La nueva contraseña debe tener al menos 6 caracteres'}), 400
    
    user_model = get_user_model()
    user = user_model.find_by_username(username)
    
    # Verificar contraseña actual
    if not user_model.verify_password(user, current_password):
        return jsonify({'error': 'Contraseña actual incorrecta'}), 401
    
    # Actualizar contraseña
    from app.utils.database import bcrypt, mongo
    new_hash = bcrypt.generate_password_hash(new_password).decode()
    
    mongo.db.users.update_one(
        {"username": username},
        {"$set": {"password": new_hash}}
    )
    
    print(f"[change-password] Usuario '{username}' cambió su contraseña")
    
    return jsonify({'msg': 'Contraseña actualizada exitosamente'}), 200


@auth_bp.route('/users', methods=['GET'])
@require_jwt_http
def list_users(username):
    """
    GET /auth/users
    Lista todos los usuarios (solo muestra info básica)
    
    Headers:
        Authorization: Bearer <token>
    
    Query Params:
        ?online=true  # Solo usuarios online
    
    Response:
        {
            "users": [
                {
                    "username": "admin",
                    "is_admin": true,
                    "current_room": "General",
                    "created_at": "2025-01-15T10:30:00"
                }
            ],
            "total": 10
        }
    """
    only_online = request.args.get('online', 'false').lower() == 'true'
    
    from app.utils.database import mongo
    
    query = {}
    if only_online:
        query['current_room'] = {"$ne": None}
    
    users = list(mongo.db.users.find(
        query,
        {
            "_id": 0, 
            "password": 0,  # No incluir contraseña
            "socket_id": 0  # No incluir socket_id
        }
    ))
    
    # Formatear fechas
    for user in users:
        if user.get('created_at'):
            user['created_at'] = user['created_at'].isoformat()
    
    return jsonify({
        'users': users,
        'total': len(users)
    }), 200


@auth_bp.route('/users/<target_username>', methods=['DELETE'])
@require_jwt_http
def delete_user(username, target_username):
    """
    DELETE /auth/users/<username>
    Elimina un usuario (solo admin o el mismo usuario)
    
    Headers:
        Authorization: Bearer <token>
    
    Response:
        {
            "msg": "Usuario eliminado exitosamente"
        }
    """
    user_model = get_user_model()
    
    # Verificar permisos
    if username != target_username:
        # Si no es el mismo usuario, debe ser admin
        if not user_model.is_admin(username):
            return jsonify({'error': 'No tienes permiso para eliminar este usuario'}), 403
    
    # No permitir eliminar al admin principal
    if target_username == 'admin':
        return jsonify({'error': 'No se puede eliminar el usuario admin principal'}), 403
    
    # Verificar que el usuario existe
    if not user_model.exists(target_username):
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    # Eliminar usuario
    from app.utils.database import mongo
    mongo.db.users.delete_one({"username": target_username})
    
    # Opcional: Eliminar mensajes del usuario
    # message_model = get_message_model()
    # message_model.delete_user_messages(target_username)
    
    print(f"[delete-user] Usuario '{target_username}' eliminado por '{username}'")
    
    return jsonify({'msg': 'Usuario eliminado exitosamente'}), 200


# Manejo de errores
@auth_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'No autorizado'}), 401


@auth_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Error interno del servidor'}), 500
