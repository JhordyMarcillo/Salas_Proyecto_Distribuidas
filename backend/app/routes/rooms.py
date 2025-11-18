# app/routes/rooms.py
"""
Rutas HTTP para manejo de Salas (Rooms)
Endpoints REST para crear, listar, eliminar salas
"""

from flask import Blueprint, request, jsonify
from app.middleware import require_jwt_http, require_admin
from app.models import get_room_model, get_user_model, get_message_model
from app.services import RoomService

# Crear Blueprint (agrupa rutas relacionadas)
rooms_bp = Blueprint('rooms', __name__, url_prefix='/rooms')


@rooms_bp.route('', methods=['GET'])
def list_rooms():
    """
    GET /rooms
    Lista todas las salas con estadísticas
    
    Response:
        {
            "rooms": [
                {
                    "id": "uuid",
                    "name": "General",
                    "description": "Sala principal",
                    "type": "multimedia",
                    "members": 5,
                    "messages": 120,
                    "created_at": "2025-01-15T10:30:00"
                }
            ]
        }
    """
    try:
        rooms = RoomService.list_rooms_with_stats()
        return jsonify({'rooms': rooms}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@rooms_bp.route('', methods=['POST'])
@require_jwt_http
@require_admin
def create_room(username):
    """
    POST /rooms
    Crea una nueva sala (solo administradores)
    
    Headers:
        Authorization: Bearer <token>
    
    Body:
        {
            "name": "Sala VIP",
            "description": "Solo miembros premium",
            "type": "multimedia",  # "text" o "multimedia"
            "pin": "123456",       # Opcional, se genera automático si no se proporciona
            "max_file_mb": 10      # Opcional, default 10MB
        }
    
    Response:
        {
            "msg": "room creado",
            "room": {
                "id": "uuid",
                "name": "Sala VIP",
                "description": "...",
                "type": "multimedia",
                "pin": "123456",
                "max_file_mb": 10
            }
        }
    """
    data = request.get_json() or {}
    
    name = (data.get('name') or '').strip()
    description = data.get('description') or ''
    provided_pin = data.get('pin')
    room_type = (data.get('type') or 'text').lower()
    max_file_mb = int(data.get('max_file_mb')) if data.get('max_file_mb') else 10
    
    # Validaciones
    if not name:
        return jsonify({'error': 'name requerido'}), 400
    
    try:
        room_model = get_room_model()
        
        # Crear sala (el modelo maneja validaciones internas)
        room = room_model.create_room(
            name=name,
            description=description,
            room_type=room_type,
            provided_pin=provided_pin,
            max_file_mb=max_file_mb
        )
        
        return jsonify({
            'msg': 'room creado',
            'room': {
                'id': room.get('id'),
                'name': room.get('name'),
                'description': room.get('description'),
                'type': room.get('type'),
                'pin': room.get('pin'),
                'max_file_mb': room.get('max_file_mb')
            }
        }), 201
        
    except ValueError as e:
        # Errores de validación del modelo
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        # Otros errores
        return jsonify({'error': f'Error creando sala: {str(e)}'}), 500


@rooms_bp.route('/<room_name>', methods=['GET'])
def get_room_details(room_name):
    """
    GET /rooms/<room_name>
    Obtiene detalles de una sala específica
    
    Response:
        {
            "id": "uuid",
            "name": "General",
            "description": "...",
            "type": "text",
            "members_count": 5,
            "created_at": "2025-01-15T10:30:00",
            "has_pin": true,
            "max_file_mb": 10
        }
    """
    details = RoomService.get_room_details_with_members(room_name)
    
    if not details:
        return jsonify({'error': 'Sala no encontrada'}), 404
    
    return jsonify(details), 200


@rooms_bp.route('/<room_name>/summary', methods=['GET'])
def get_room_summary(room_name):
    """
    GET /rooms/<room_name>/summary
    Obtiene resumen completo de una sala (detalles + estadísticas + mensajes recientes)
    
    Response:
        {
            "room": {...},
            "stats": {
                "total_members": 5,
                "total_messages": 120
            },
            "recent_messages": [...]
        }
    """
    summary = RoomService.get_room_summary(room_name)
    
    if not summary:
        return jsonify({'error': 'Sala no encontrada'}), 404
    
    return jsonify(summary), 200


@rooms_bp.route('/<room_name>/messages', methods=['GET'])
def get_room_messages(room_name):
    """
    GET /rooms/<room_name>/messages
    Obtiene los mensajes de una sala
    
    Query Params:
        ?limit=100  # Cantidad de mensajes (default 100)
    
    Response:
        {
            "messages": [
                {
                    "username": "admin",
                    "nickname": null,
                    "msg": "Hola!",
                    "timestamp": "2025-01-15T10:30:00Z",
                    "file_url": null,
                    "original_filename": null
                }
            ]
        }
    """
    limit = request.args.get('limit', 100, type=int)
    
    # Validar límite
    if limit > 500:
        return jsonify({'error': 'Límite máximo: 500 mensajes'}), 400
    
    message_model = get_message_model()
    messages = message_model.get_room_messages(room_name, limit=limit)
    formatted = message_model.format_messages_for_api(messages)
    
    return jsonify({'messages': formatted}), 200


@rooms_bp.route('/<room_name>', methods=['DELETE'])
@require_jwt_http
@require_admin
def delete_room(username, room_name):
    """
    DELETE /rooms/<room_name>
    Elimina una sala y todos sus datos relacionados (solo admin)
    
    Headers:
        Authorization: Bearer <token>
    
    Response:
        {
            "msg": "Sala eliminada exitosamente",
            "stats": {
                "room_deleted": true,
                "messages_deleted": 120,
                "users_cleared": 5
            }
        }
    """
    room_model = get_room_model()
    
    # Verificar que existe
    if not room_model.exists(room_name):
        return jsonify({'error': 'Sala no encontrada'}), 404
    
    # Eliminar en cascada
    stats = RoomService.delete_room_cascade(room_name)
    
    return jsonify({
        'msg': 'Sala eliminada exitosamente',
        'stats': stats
    }), 200


@rooms_bp.route('/<room_name>', methods=['PATCH'])
@require_jwt_http
@require_admin
def update_room(username, room_name):
    """
    PATCH /rooms/<room_name>
    Actualiza la descripción de una sala (solo admin)
    
    Headers:
        Authorization: Bearer <token>
    
    Body:
        {
            "description": "Nueva descripción"
        }
    
    Response:
        {
            "msg": "Sala actualizada",
            "room": {...}
        }
    """
    data = request.get_json() or {}
    new_description = data.get('description')
    
    if new_description is None:
        return jsonify({'error': 'description requerida'}), 400
    
    room_model = get_room_model()
    updated_room = room_model.update_description(room_name, new_description)
    
    if not updated_room:
        return jsonify({'error': 'Sala no encontrada'}), 404
    
    return jsonify({
        'msg': 'Sala actualizada',
        'room': {
            'name': updated_room.get('name'),
            'description': updated_room.get('description')
        }
    }), 200


@rooms_bp.route('/<room_name>/members', methods=['GET'])
def get_room_members(room_name):
    """
    GET /rooms/<room_name>/members
    Lista los miembros actualmente en una sala
    
    Response:
        {
            "room": "General",
            "members_count": 3,
            "members": [
                {
                    "username": "admin",
                    "nickname": null,
                    "is_anonymous": false
                },
                {
                    "username": "anon_abc123",
                    "nickname": "Invitado1",
                    "is_anonymous": true
                }
            ]
        }
    """
    room_model = get_room_model()
    
    # Verificar que la sala existe
    if not room_model.exists(room_name):
        return jsonify({'error': 'Sala no encontrada'}), 404
    
    # Obtener usuarios en la sala
    from app.utils.database import mongo
    users = list(mongo.db.users.find(
        {"current_room": room_name},
        {"_id": 0, "username": 1, "nickname": 1, "is_anonymous": 1}
    ))
    
    return jsonify({
        'room': room_name,
        'members_count': len(users),
        'members': users
    }), 200


@rooms_bp.route('/stats', methods=['GET'])
@require_jwt_http
def get_global_stats(username):
    """
    GET /rooms/stats
    Obtiene estadísticas globales del sistema
    
    Headers:
        Authorization: Bearer <token>
    
    Response:
        {
            "total_rooms": 5,
            "total_messages": 1250,
            "total_users_online": 12
        }
    """
    room_model = get_room_model()
    message_model = get_message_model()
    
    from app.utils.database import mongo
    
    total_rooms = room_model.count_all()
    total_messages = mongo.db.messages.count_documents({})
    users_online = mongo.db.users.count_documents({"current_room": {"$ne": None}})
    
    return jsonify({
        'total_rooms': total_rooms,
        'total_messages': total_messages,
        'total_users_online': users_online
    }), 200


# Manejo de errores específico del blueprint
@rooms_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Recurso no encontrado'}), 404


@rooms_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Error interno del servidor'}), 500