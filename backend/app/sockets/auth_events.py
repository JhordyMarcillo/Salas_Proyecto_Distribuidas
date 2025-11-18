# app/sockets/auth_events.py
"""
Eventos WebSocket de Autenticación
Maneja registro, login y conexión de usuarios via WebSocket
"""

from flask import request
from flask_socketio import emit
from app.models import get_user_model
from app.services import JWTService


def register_auth_events(socketio):
    """
    Registra todos los eventos de autenticación en el socketio
    
    Args:
        socketio: Instancia de SocketIO
    """
    
    @socketio.on("connect")
    def handle_connect(auth):
        """
        Evento: connect
        Se ejecuta cuando un cliente establece conexión WebSocket
        
        Auth (opcional):
            {"token": "eyJ..."}
        
        Nota: La conexión se acepta pero si se envía un token, se valida
        """
        from app.services.jwt_service import JWTService
        from app.models import get_user_model
        
        sid = request.sid
        token = None
        username = None
        is_authenticated = False
        
        if isinstance(auth, dict):
            token = auth.get("token")
        
        # Si se proporciona token, validarlo
        if token:
            try:
                username = JWTService.verify_token(token)
                is_authenticated = True
                user_model = get_user_model()
                user_model.update_socket(username, sid)
                print(f"[connect] sid={sid} user={username} (authenticated)")
            except ValueError as e:
                # Token inválido pero aceptamos conexión anónima
                print(f"[connect] sid={sid} token inválido: {str(e)}")
        else:
            print(f"[connect] sid={sid} (anonymous)")
        
        # Enviar confirmación de conexión
        emit("status", {
            "msg": "Conexión WebSocket establecida",
            "sid": sid,
            "authenticated": is_authenticated,
            "username": username
        })
    
    
    @socketio.on("register")
    def handle_register(data):
        """
        Evento: register
        Registra un nuevo usuario via WebSocket
        
        Data:
            {
                "username": "nuevo_usuario",
                "password": "password123"
            }
        
        Emite:
            - "register_success" si todo OK
            - "register_error" si hay error
        """
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""
        
        # Validaciones
        if not username or not password:
            emit("register_error", {"msg": "username y password requeridos"})
            return
        
        if len(username) < 3:
            emit("register_error", {"msg": "username debe tener al menos 3 caracteres"})
            return
        
        if len(password) < 6:
            emit("register_error", {"msg": "password debe tener al menos 6 caracteres"})
            return
        
        user_model = get_user_model()
        
        # Verificar si existe
        if user_model.exists(username):
            emit("register_error", {"msg": "usuario ya existe"})
            return
        
        try:
            # Crear usuario
            user_model.create_user(username, password, is_admin=False)
            
            # Generar token
            token = JWTService.create_token(username)
            
            print(f"[register] Usuario '{username}' registrado via WebSocket")
            
            emit("register_success", {
                "msg": "usuario creado",
                "token": token,
                "username": username
            })
            
        except Exception as e:
            print(f"[register error] {str(e)}")
            emit("register_error", {"msg": f"Error al crear usuario: {str(e)}"})
    
    
    @socketio.on("login")
    def handle_login(data):
        """
        Evento: login
        Inicia sesión de un usuario via WebSocket
        
        Data:
            {
                "username": "admin",
                "password": "admin123"
            }
        
        Emite:
            - "login_success" si las credenciales son correctas
            - "login_error" si hay error
        """
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""
        
        # Validaciones
        if not username or not password:
            emit("login_error", {"msg": "username y password requeridos"})
            return
        
        user_model = get_user_model()
        
        # Buscar usuario
        user = user_model.find_by_username(username)
        if not user:
            emit("login_error", {"msg": "credenciales inválidas"})
            return
        
        # Verificar contraseña
        if not user_model.verify_password(user, password):
            emit("login_error", {"msg": "credenciales inválidas"})
            return
        
        # Actualizar socket_id del usuario
        sid = request.sid
        user_model.update_socket(username, sid)
        
        # Generar token
        token = JWTService.create_token(username)
        
        print(f"[login] Usuario '{username}' inició sesión (sid={sid})")
        
        emit("login_success", {
            "msg": "login correcto",
            "token": token,
            "username": username,
            "is_admin": user.get("is_admin", False)
        })
    
    
    @socketio.on("disconnect")
    def handle_disconnect():
        """
        Evento: disconnect
        Se ejecuta cuando un cliente cierra la conexión WebSocket
        Limpia el socket_id y current_room del usuario
        """
        sid = request.sid
        user_model = get_user_model()
        
        # Buscar usuario por socket_id
        user = user_model.find_by_socket_id(sid)
        
        if user:
            username = user.get("username")
            is_anon = user.get("is_anonymous", False)
            current_room = user.get("current_room")
            
            from datetime import datetime
            from zoneinfo import ZoneInfo
            ts = datetime.now(ZoneInfo('America/Guayaquil'))
            
            # Si es usuario anónimo, eliminarlo
            if is_anon:
                nickname = user.get("nickname")
                user_model.delete_anonymous_user(username)
                
                # Notificar desconexión
                payload = {
                    "username": username,
                    "nickname": nickname,
                    "timestamp": ts.isoformat()
                }
                if current_room:
                    payload["room"] = current_room
                
                emit("user_disconnected", payload, broadcast=True)
                print(f"[disconnect] Usuario anónimo '{nickname}' eliminado (sid={sid})")
            else:
                # Usuario normal: limpiar socket_id y current_room
                user_model.clear_socket(sid)
                
                # Notificar desconexión
                emit("user_disconnected", {
                    "username": username,
                    "room": current_room,
                    "timestamp": ts.isoformat()
                }, broadcast=True)
                print(f"[disconnect] Usuario '{username}' desconectado (sid={sid})")
        else:
            print(f"[disconnect] Socket no asociado a usuario: {sid}")
    
    
    print("[sockets] Eventos de autenticación registrados")