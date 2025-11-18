# app/middleware/__init__.py
"""
Middleware Package

Este paquete contiene todos los middlewares de la aplicación:
- Autenticación y autorización
- Validación de datos
- Rate limiting
- Logging de peticiones
- Manejo de errores

Los middlewares son funciones decoradoras que se ejecutan ANTES
de las rutas principales para validar, autenticar, o modificar
las peticiones.
"""

# Importar decoradores de autenticación
from app.middleware.auth import (
    require_jwt_http,          # Para rutas HTTP que requieren JWT
    require_token_socket,      # Para eventos WebSocket que requieren token
    require_admin,             # Para rutas HTTP que requieren rol admin
    require_admin_socket,      # Para eventos WebSocket que requieren admin
    optional_auth_http         # Para rutas HTTP con autenticación opcional
)

# Exportar todo lo que queremos que sea accesible desde otros módulos
__all__ = [
    'require_jwt_http',
    'require_token_socket',
    'require_admin',
    'require_admin_socket',
    'optional_auth_http'
]
