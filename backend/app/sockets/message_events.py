# app/sockets/message_events.py
"""
Eventos WebSocket de Mensajes
Maneja envío y recepción de mensajes en tiempo real
"""

from flask_socketio import emit
from app.middleware import require_token_socket
from app.models import get_user_model, get_room_model, get_message_model
from app.services import RoomService


def register_message_events(socketio):
    """
    Registra todos los eventos de mensajes en el socketio
    
    Args:
        socketio: Instancia de SocketIO
    """
    
    @socketio.on("send_message")
    @require_token_socket
    def handle_send_message(username, data):
        """
        Evento: send_message
        Envía un mensaje a una sala
        
        Data:
            {
                "token": "eyJ...",
                "room": "General",
                "msg": "Hola a todos!",
                "file_url": "https://...",          # Opcional
                "original_filename": "imagen.jpg"   # Opcional
            }
        
        Emite:
            - "message" a todos en la sala con el mensaje
            - "msg_error" si hay error
        """
        room = (data.get("room") or "").strip()
        msg = (data.get("msg") or "").strip()
        file_url = data.get("file_url")
        original_filename = data.get("original_filename")
        
        # Validaciones básicas
        if not msg and not file_url:
            emit("msg_error", {"msg": "msg o file_url requeridos"})
            return
        
        if not room:
            emit("msg_error", {"msg": "room requerido"})
            return
        
        user_model = get_user_model()
        room_model = get_room_model()
        message_model = get_message_model()
        
        # Verificar que el usuario está en la sala
        user = user_model.find_by_username(username)
        if not user or user.get("current_room") != room:
            emit("msg_error", {"msg": "no perteneces a esa sala"})
            return
        
        # Si hay archivo, verificar que la sala lo permite
        if file_url:
            if not room_model.allows_files(room):
                emit("msg_error", {
                    "msg": "esta sala no permite archivos (solo texto)"
                })
                return
        
        # Crear mensaje en la base de datos
        message = message_model.create_message(
            room=room,
            username=username,
            msg=msg,
            nickname=user.get("nickname"),
            file_url=file_url,
            original_filename=original_filename
        )
        
        # Formatear mensaje para enviar
        formatted_message = message_model.format_message_for_emit(message)
        
        # Enviar a todos en la sala
        emit("message", formatted_message, room=room)
        
        # Log
        if file_url:
            print(f"[msg-file] [{room}] {user.get('nickname') or username}: {original_filename}")
        else:
            print(f"[msg] [{room}] {user.get('nickname') or username}: {msg}")
    
    
    @socketio.on("get_messages")
    @require_token_socket
    def handle_get_messages(username, data):
        """
        Evento: get_messages
        Obtiene mensajes de una sala
        
        Data:
            {
                "token": "eyJ...",
                "room": "General",
                "limit": 50  # Opcional, default 100
            }
        
        Emite:
            - "messages_list" con los mensajes
        """
        room = (data.get("room") or "").strip()
        limit = data.get("limit", 100)
        
        if not room:
            emit("error", {"msg": "room requerido"})
            return
        
        # Validar límite
        if limit > 500:
            limit = 500
        
        message_model = get_message_model()
        
        # Obtener mensajes
        messages = message_model.get_room_messages(room, limit=limit)
        formatted_messages = message_model.format_messages_for_api(messages)
        
        emit("messages_list", {
            "room": room,
            "messages": formatted_messages,
            "count": len(formatted_messages)
        })
    
    
    @socketio.on("typing")
    @require_token_socket
    def handle_typing(username, data):
        """
        Evento: typing
        Notifica que un usuario está escribiendo
        
        Data:
            {
                "token": "eyJ...",
                "room": "General",
                "is_typing": true
            }
        
        Emite:
            - "user_typing" a todos en la sala (excepto al emisor)
        """
        room = (data.get("room") or "").strip()
        is_typing = data.get("is_typing", False)
        
        if not room:
            return
        
        user_model = get_user_model()
        user = user_model.find_by_username(username)
        
        # Verificar que está en la sala
        if not user or user.get("current_room") != room:
            return
        
        # Notificar a los demás
        emit("user_typing", {
            "username": username,
            "nickname": user.get("nickname"),
            "room": room,
            "is_typing": is_typing
        }, room=room, include_self=False)
    
    
    @socketio.on("delete_message")
    @require_token_socket
    def handle_delete_message(username, data):
        """
        Evento: delete_message
        Elimina un mensaje (solo el autor o admin)
        
        Data:
            {
                "token": "eyJ...",
                "message_id": "abc123",
                "room": "General"
            }
        
        Emite:
            - "message_deleted" a todos en la sala
            - "error" si no tiene permisos
        """
        message_id = data.get("message_id")
        room = data.get("room")
        
        if not message_id or not room:
            emit("error", {"msg": "message_id y room requeridos"})
            return
        
        user_model = get_user_model()
        
        # Obtener el mensaje
        from app.utils.database import mongo
        from bson.objectid import ObjectId
        
        try:
            message = mongo.db.messages.find_one({"_id": ObjectId(message_id)})
        except:
            emit("error", {"msg": "ID de mensaje inválido"})
            return
        
        if not message:
            emit("error", {"msg": "Mensaje no encontrado"})
            return
        
        # Verificar permisos (autor del mensaje o admin)
        is_author = message.get("username") == username
        is_admin = user_model.is_admin(username)
        
        if not is_author and not is_admin:
            emit("error", {"msg": "No tienes permiso para eliminar este mensaje"})
            return
        
        # Eliminar mensaje
        mongo.db.messages.delete_one({"_id": ObjectId(message_id)})
        
        # Notificar a todos
        emit("message_deleted", {
            "message_id": message_id,
            "room": room,
            "deleted_by": username
        }, room=room)
        
        print(f"[delete-message] {username} eliminó mensaje {message_id} en {room}")
    
    
    @socketio.on("search_messages")
    @require_token_socket
    def handle_search_messages(username, data):
        """
        Evento: search_messages
        Busca mensajes en una sala
        
        Data:
            {
                "token": "eyJ...",
                "room": "General",
                "search_term": "hola"
            }
        
        Emite:
            - "search_results" con los mensajes encontrados
        """
        room = (data.get("room") or "").strip()
        search_term = (data.get("search_term") or "").strip()
        
        if not room or not search_term:
            emit("error", {"msg": "room y search_term requeridos"})
            return
        
        message_model = get_message_model()
        
        # Buscar mensajes
        messages = message_model.search_messages(room, search_term)
        formatted_messages = message_model.format_messages_for_api(messages)
        
        emit("search_results", {
            "room": room,
            "search_term": search_term,
            "results": formatted_messages,
            "count": len(formatted_messages)
        })
    
    
    print("[sockets] Eventos de mensajes registrados")