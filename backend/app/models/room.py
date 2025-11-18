# app/models/room.py
"""
Modelo de Sala (Room)
Maneja todas las operaciones relacionadas con salas de chat
"""

import uuid
import secrets
from datetime import datetime
from zoneinfo import ZoneInfo


class RoomModel:
    """
    Modelo para manejar operaciones de salas de chat
    """
    
    def __init__(self, mongo):
        """
        Inicializa el modelo con la conexión a MongoDB
        """
        self.rooms = mongo.db.rooms
    
    def create_room(self, name, description='', room_type='text', 
                   provided_pin=None, max_file_mb=10):
        """
        Crea una nueva sala de chat
        
        Args:
            name (str): Nombre único de la sala
            description (str): Descripción de la sala
            room_type (str): 'text' o 'multimedia'
            provided_pin (str|None): PIN personalizado o None para auto-generar
            max_file_mb (int): Tamaño máximo de archivo en MB
        
        Returns:
            dict: Documento de la sala creada
        
        Raises:
            ValueError: Si el tipo de sala es inválido o el PIN es inválido
        """
        # Validaciones
        if room_type not in ('text', 'multimedia'):
            raise ValueError("type inválido (usar 'text' o 'multimedia')")
        
        if self.exists(name):
            raise ValueError("room ya existe")
        
        # Generar o validar PIN
        if provided_pin is not None:
            pin_str = str(provided_pin).strip()
            if not pin_str.isdigit() or len(pin_str) < 4:
                raise ValueError("pin inválido (numérico y al menos 4 dígitos)")
            pin = pin_str
        else:
            # Auto-generar PIN de 6 dígitos
            pin = f"{secrets.randbelow(900000) + 100000}"
        
        room_id = str(uuid.uuid4())
        room_doc = {
            'id': room_id,
            'name': name,
            'description': description,
            'pin': pin,
            'type': room_type,
            'max_file_mb': max_file_mb,
            'created_at': datetime.now(ZoneInfo('America/Guayaquil'))
        }
        
        self.rooms.insert_one(room_doc)
        return room_doc
    
    def find_by_name(self, name):
        """
        Busca una sala por su nombre
        
        Args:
            name (str): Nombre de la sala
        
        Returns:
            dict | None: Documento de la sala o None
        """
        return self.rooms.find_one({"name": name})
    
    def find_by_id(self, room_id):
        """
        Busca una sala por su ID
        
        Args:
            room_id (str): ID de la sala
        
        Returns:
            dict | None: Documento de la sala o None
        """
        return self.rooms.find_one({"id": room_id})
    
    def list_all(self):
        """
        Lista todas las salas ordenadas por fecha de creación
        
        Returns:
            list: Lista de documentos de salas
        """
        return list(self.rooms.find({}).sort('created_at', 1))
    
    def exists(self, name):
        """
        Verifica si una sala existe
        
        Args:
            name (str): Nombre de la sala
        
        Returns:
            bool: True si existe
        """
        return self.rooms.find_one({"name": name}) is not None
    
    def verify_pin(self, room_name, provided_pin):
        """
        Verifica si el PIN es correcto para una sala
        
        Args:
            room_name (str): Nombre de la sala
            provided_pin (str): PIN proporcionado
        
        Returns:
            bool: True si el PIN es correcto o no se requiere PIN
        """
        room = self.find_by_name(room_name)
        if not room:
            return False
        
        required_pin = room.get("pin")
        if not required_pin:
            return True  # No requiere PIN
        
        return str(provided_pin) == str(required_pin)
    
    def get_type(self, room_name):
        """
        Obtiene el tipo de una sala (text o multimedia)
        
        Args:
            room_name (str): Nombre de la sala
        
        Returns:
            str: 'text' o 'multimedia', default 'text'
        """
        room = self.find_by_name(room_name)
        if not room:
            return 'text'
        return room.get('type', 'text')
    
    def allows_files(self, room_name):
        """
        Verifica si una sala permite subir archivos
        
        Args:
            room_name (str): Nombre de la sala
        
        Returns:
            bool: True si permite archivos (tipo multimedia)
        """
        return self.get_type(room_name) == 'multimedia'
    
    def get_max_file_size(self, room_name):
        """
        Obtiene el tamaño máximo de archivo permitido para una sala
        
        Args:
            room_name (str): Nombre de la sala
        
        Returns:
            int: Tamaño máximo en MB
        """
        room = self.find_by_name(room_name)
        if not room:
            return 10  # Default
        return room.get('max_file_mb', 10)
    
    def delete_room(self, room_name):
        """
        Elimina una sala
        
        Args:
            room_name (str): Nombre de la sala
        
        Returns:
            bool: True si se eliminó
        """
        result = self.rooms.delete_one({"name": room_name})
        return result.deleted_count > 0
    
    def update_description(self, room_name, new_description):
        """
        Actualiza la descripción de una sala
        
        Args:
            room_name (str): Nombre de la sala
            new_description (str): Nueva descripción
        
        Returns:
            dict | None: Sala actualizada o None
        """
        from pymongo import ReturnDocument
        return self.rooms.find_one_and_update(
            {"name": room_name},
            {"$set": {"description": new_description}},
            return_document=ReturnDocument.AFTER
        )
    
    def count_all(self):
        """
        Cuenta todas las salas
        
        Returns:
            int: Cantidad de salas
        """
        return self.rooms.count_documents({})