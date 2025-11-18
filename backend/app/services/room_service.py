# app/services/room_service.py
"""
Servicio de lógica de negocio para Salas
Contiene operaciones complejas que involucran múltiples modelos
"""

from app.models import get_user_model, get_room_model, get_message_model


class RoomService:
    """
    Servicio con lógica de negocio relacionada a salas
    Métodos que requieren coordinación entre modelos
    """
    
    @staticmethod
    def get_room_details_with_members(room_name):
        """
        Obtiene detalles completos de una sala incluyendo miembros
        """
        room_model = get_room_model()
        user_model = get_user_model()
        
        room = room_model.find_by_name(room_name)
        if not room:
            return None
        
        members_count = user_model.count_in_room(room_name)
        
        return {
            'id': room.get('id'),
            'name': room.get('name'),
            'description': room.get('description'),
            'type': room.get('type', 'text'),
            'members_count': members_count,
            'created_at': room.get('created_at').isoformat() if room.get('created_at') else None,
            'has_pin': bool(room.get('pin')),
            'max_file_mb': room.get('max_file_mb', 10)
        }
    
    @staticmethod
    def list_rooms_with_stats():
        
        room_model = get_room_model()
        user_model = get_user_model()
        message_model = get_message_model()
        
        rooms = room_model.list_all()
        result = []
        
        for room in rooms:
            name = room.get('name')
            result.append({
                'id': room.get('id'),
                'name': name,
                'description': room.get('description'),
                'type': room.get('type', 'text'),
                'members': user_model.count_in_room(name),
                'messages': message_model.count_room_messages(name),
                'created_at': room.get('created_at').isoformat() if room.get('created_at') else None
            })
        
        return result
    
    @staticmethod
    def validate_join_request(username, room_name, provided_pin):
        room_model = get_room_model()
        user_model = get_user_model()
        
        # 1. Verificar que la sala existe
        room = room_model.find_by_name(room_name)
        if not room:
            return False, "Sala no existe"
        
        # 2. Verificar PIN si es requerido
        if not room_model.verify_pin(room_name, provided_pin):
            return False, "PIN inválido"
        
        # 3. Verificar que el usuario existe
        user = user_model.find_by_username(username)
        if not user:
            return False, "Usuario no encontrado"
        
        # 4. El usuario puede unirse
        return True, None
    
    @staticmethod
    def can_send_file(username, room_name, file_size_mb):
        room_model = get_room_model()
        user_model = get_user_model()
        
        # 1. Verificar que el usuario está en la sala
        user = user_model.find_by_username(username)
        if not user or user.get('current_room') != room_name:
            return False, "No estás en esa sala"
        
        # 2. Verificar que la sala permite archivos
        if not room_model.allows_files(room_name):
            return False, "Esta sala no permite archivos (solo texto)"
        
        # 3. Verificar el tamaño del archivo
        max_size = room_model.get_max_file_size(room_name)
        if file_size_mb > max_size:
            return False, f"Archivo excede el límite de {max_size} MB"
        
        return True, None
    
    @staticmethod
    def delete_room_cascade(room_name):
        room_model = get_room_model()
        message_model = get_message_model()
        user_model = get_user_model()
        
        # Contar antes de eliminar
        messages_count = message_model.count_room_messages(room_name)
        users_count = user_model.count_in_room(room_name)
        
        # 1. Eliminar todos los mensajes
        messages_deleted = message_model.delete_room_messages(room_name)
        
        # 2. Limpiar usuarios que están en la sala
        # (actualizar current_room a None)
        from app.utils.database import mongo
        users_updated = mongo.db.users.update_many(
            {"current_room": room_name},
            {"$set": {"current_room": None}}
        )
        
        # 3. Eliminar la sala
        room_deleted = room_model.delete_room(room_name)
        
        return {
            'room_deleted': room_deleted,
            'messages_deleted': messages_deleted,
            'users_cleared': users_updated.modified_count
        }
    
    @staticmethod
    def get_room_summary(room_name):
        room_model = get_room_model()
        user_model = get_user_model()
        message_model = get_message_model()
        
        room = room_model.find_by_name(room_name)
        if not room:
            return None
        
        # Obtener últimos mensajes
        recent_messages = message_model.get_room_messages(room_name, limit=10)
        
        return {
            'room': {
                'id': room.get('id'),
                'name': room.get('name'),
                'description': room.get('description'),
                'type': room.get('type', 'text'),
                'created_at': room.get('created_at').isoformat() if room.get('created_at') else None
            },
            'stats': {
                'total_members': user_model.count_in_room(room_name),
                'total_messages': message_model.count_room_messages(room_name)
            },
            'recent_messages': message_model.format_messages_for_api(recent_messages)
        }