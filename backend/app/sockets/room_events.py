# app/sockets/room_events.py
"""
Eventos WebSocket de Salas
Maneja unirse, salir y gestión de salas en tiempo real
"""

from flask import request
from flask_socketio import emit, join_room, leave_room
from datetime import datetime
from zoneinfo import ZoneInfo
from app.middleware import require_token_socket
from app.models import get_user_model, get_room_model
from app.services import JWTService, RoomService


def register_room_events(socketio):
    """
    Registra todos los eventos de salas en el socketio
    
    Args:
        socketio: Instancia de SocketIO
    """
    
    @socketio.on("join")
    def handle_join(data):
        """
        Evento: join
        Une a un usuario a una sala de chat
        
        Data:
            {
                "token": "eyJ...",           # Token JWT (requerido)
                "room": "General",           # Nombre de la sala (requerido)
                "pin": "123456"              # PIN de la sala (si requiere)
            }
        
        Emite:
            - "join_success" al usuario que se une
            - "user_joined" a todos en la sala
            - "join_error" si hay error
        """
        sid = request.sid
        token = data.get("token")
        room_name = (data.get("room") or "").strip()
        provided_pin = (data.get("pin") or "").strip()
        
        # 1. Validar que se proporcione el nombre de sala
        if not room_name:
            emit("join_error", {"msg": "Nombre de sala (room) requerido"})
            return
        
        room_model = get_room_model()
        user_model = get_user_model()
        
        # 2. Verificar que la sala existe
        room_doc = room_model.find_by_name(room_name)
        if not room_doc:
            emit("join_error", {"msg": "Sala no existe"})
            return
        
        # 3. Verificar PIN si es requerido
        if not room_model.verify_pin(room_name, provided_pin):
            emit("join_error", {"msg": "PIN inválido"})
            return
        
        # 4. Validar token de autenticación
        if not token:
            emit("join_error", {
                "code": "no_token", 
                "msg": "Token de autenticación requerido"
            })
            return
        
        try:
            username = JWTService.verify_token(token)
        except ValueError as e:
            code = "token_invalid"
            if str(e) == "token_expired":
                code = "token_expired"
            emit("join_error", {
                "code": code, 
                "msg": "Token inválido o expirado"
            })
            return
        
        # 5. Actualizar usuario en la base de datos
        user_model.update_room(username, room_name, socket_id=sid)
        
        # 6. Unir al usuario a la sala de WebSocket
        join_room(room_name)
        
        # 7. Confirmar al usuario
        emit("join_success", {"room": room_name})
        
        # 8. Notificar a todos en la sala
        ts = datetime.now(ZoneInfo('America/Guayaquil'))
        emit("user_joined", {
            "username": username,
            "room": room_name,
            "timestamp": ts.isoformat()
        }, room=room_name)
        
        emit("status", {
            "msg": f"{username} se unió a {room_name}"
        }, room=room_name)
        
        print(f"[join] {username} -> {room_name}")
    
    
    @socketio.on("leave")
    @require_token_socket
    def handle_leave(username, data):
        """
        Evento: leave
        Saca a un usuario de una sala
        
        Data:
            {
                "token": "eyJ...",
                "room": "General"
            }
        
        Emite:
            - "leave_success" al usuario
            - "user_left" a todos en la sala
            - "leave_error" si hay error
        """
        room = (data.get("room") or "").strip()
        
        if not room:
            emit("leave_error", {"msg": "room requerido"})
            return
        
        user_model = get_user_model()
        user = user_model.find_by_username(username)
        
        if not user:
            emit("leave_error", {"msg": "Usuario no encontrado"})
            return
        
        # Verificar que el usuario está en esa sala
        if user.get("current_room") != room:
            emit("leave_error", {"msg": "no estás en esa sala"})
            return
        
        # Si es usuario anónimo, eliminarlo completamente
        if user.get("is_anonymous"):
            nickname = user.get("nickname")
            user_model.delete_anonymous_user(username)
            
            leave_room(room)
            emit("leave_success", {"room": room})
            
            ts = datetime.now(ZoneInfo('America/Guayaquil'))
            payload = {
                "username": username,
                "nickname": nickname,
                "room": room,
                "timestamp": ts.isoformat()
            }
            emit("user_left", payload, room=room)
            emit("status", {
                "msg": f"{nickname} salió de {room}"
            }, room=room)
            
            print(f"[leave] {username} (anon: {nickname}) <- {room}")
        else:
            # Usuario normal: limpiar current_room
            user_model.update_room(username, None)
            
            leave_room(room)
            emit("leave_success", {"room": room})
            
            ts = datetime.now(ZoneInfo('America/Guayaquil'))
            emit("user_left", {
                "username": username,
                "room": room,
                "timestamp": ts.isoformat()
            }, room=room)
            emit("status", {
                "msg": f"{username} salió de {room}"
            }, room=room)
            
            print(f"[leave] {username} <- {room}")
    
    
    @socketio.on("get_room_info")
    @require_token_socket
    def handle_get_room_info(username, data):
        """
        Evento: get_room_info
        Obtiene información de una sala en tiempo real
        
        Data:
            {
                "token": "eyJ...",
                "room": "General"
            }
        
        Emite:
            - "room_info" con los detalles de la sala
        """
        room_name = (data.get("room") or "").strip()
        
        if not room_name:
            emit("error", {"msg": "room requerido"})
            return
        
        # Obtener información completa de la sala
        room_info = RoomService.get_room_details_with_members(room_name)
        
        if not room_info:
            emit("error", {"msg": "Sala no encontrada"})
            return
        
        emit("room_info", room_info)
    
    
    @socketio.on("list_rooms")
    def handle_list_rooms(data):
        """
        Evento: list_rooms
        Lista todas las salas disponibles (no requiere autenticación)
        
        Emite:
            - "rooms_list" con la lista de salas
        """
        rooms = RoomService.list_rooms_with_stats()
        emit("rooms_list", {"rooms": rooms})
    
    
    @socketio.on("get_members")
    @require_token_socket
    def handle_get_members(username, data):
        """
        Evento: get_members
        Obtiene la lista de miembros en una sala
        
        Data:
            {
                "token": "eyJ...",
                "room": "General"
            }
        
        Emite:
            - "members_list" con los miembros
        """
        room_name = (data.get("room") or "").strip()
        
        if not room_name:
            emit("error", {"msg": "room requerido"})
            return
        
        room_model = get_room_model()
        
        # Verificar que la sala existe
        if not room_model.exists(room_name):
            emit("error", {"msg": "Sala no encontrada"})
            return
        
        # Obtener usuarios en la sala
        from app.utils.database import mongo
        users = list(mongo.db.users.find(
            {"current_room": room_name},
            {"_id": 0, "username": 1, "nickname": 1, "is_anonymous": 1}
        ))
        
        emit("members_list", {
            "room": room_name,
            "members": users,
            "count": len(users)
        })
    
    
    print("[sockets] Eventos de salas registrados")