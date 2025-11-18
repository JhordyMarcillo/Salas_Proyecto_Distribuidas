# app/sockets/__init__.py
"""
Sockets Package

Este paquete contiene todos los eventos WebSocket de la aplicación.
Los eventos están organizados por funcionalidad:
- auth_events: Autenticación (connect, register, login, disconnect)
- room_events: Gestión de salas (join, leave, get_room_info)
- message_events: Mensajes (send_message, typing, delete_message)

WebSocket permite comunicación BIDIRECCIONAL en tiempo real:
- El servidor puede enviar datos al cliente sin que lo solicite
- Ideal para chat, notificaciones, actualizaciones en vivo
"""

from app.sockets.auth_events import register_auth_events
from app.sockets.room_events import register_room_events
from app.sockets.message_events import register_message_events

# Exportar funciones de registro
__all__ = [
    'register_auth_events',
    'register_room_events',
    'register_message_events',
    'register_all_socket_events'
]


def register_all_socket_events(socketio):
    """
    Registra TODOS los eventos WebSocket en la aplicación
    
    Args:
        socketio: Instancia de SocketIO
    
    Esta función debe llamarse en app/__init__.py:
        from app.sockets import register_all_socket_events
        register_all_socket_events(socketio)
    """
    register_auth_events(socketio)
    register_room_events(socketio)
    register_message_events(socketio)
    
    print("[sockets] Todos los eventos WebSocket registrados")

