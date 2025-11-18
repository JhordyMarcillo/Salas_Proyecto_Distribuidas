# app/routes/__init__.py
"""
Routes Package

Este paquete contiene todas las rutas HTTP (endpoints REST) de la aplicación.
Las rutas están organizadas en Blueprints por funcionalidad:
- auth: Autenticación (registro, login, etc.)
- rooms: Operaciones CRUD de salas
- upload: Subida y gestión de archivos

Los Blueprints son módulos que agrupan rutas relacionadas.
Esto hace que el código sea más organizado y escalable.

Estructura de URL:
- /auth/*       -> auth_bp (autenticación)
- /rooms/*      -> rooms_bp (gestión de salas)
- /upload/*     -> upload_bp (subida de archivos)
"""

from app.routes.auth import auth_bp
from app.routes.rooms import rooms_bp
from app.routes.upload import upload_bp

# Exportar todos los blueprints
__all__ = [
    'auth_bp',
    'rooms_bp',
    'upload_bp'
]


def register_blueprints(app):
    """
    Registra todos los blueprints en la aplicación Flask
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(upload_bp)
    
    print("[routes] Blueprints registrados correctamente")

