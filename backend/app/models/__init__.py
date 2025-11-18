# app/models/__init__.py
"""
Models Package

Este paquete contiene todos los modelos de datos de la aplicación.
Los modelos son clases que encapsulan la lógica de acceso a datos
y las operaciones sobre las colecciones de MongoDB.

Cada modelo representa una entidad del dominio:
- UserModel: Usuarios del sistema (autenticados y anónimos)
- RoomModel: Salas de chat
- MessageModel: Mensajes enviados en las salas

Los modelos NO se instancian directamente en la mayoría de casos.
En su lugar, se inicializan una vez y se reutilizan en toda la app.
"""

from app.models.user import UserModel
from app.models.room import RoomModel
from app.models.message import MessageModel

# Variable global para almacenar instancias de modelos
_user_model = None
_room_model = None
_message_model = None


def init_models(mongo, bcrypt):
    global _user_model, _room_model, _message_model
    
    _user_model = UserModel(mongo, bcrypt)
    _room_model = RoomModel(mongo)
    _message_model = MessageModel(mongo)
    
    return _user_model, _room_model, _message_model


def get_user_model():
    if _user_model is None:
        raise RuntimeError()
    return _user_model


def get_room_model():
    if _room_model is None:
        raise RuntimeError()
    return _room_model


def get_message_model():
    if _message_model is None:
        raise RuntimeError()
    return _message_model