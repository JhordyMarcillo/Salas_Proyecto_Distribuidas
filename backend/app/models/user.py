# app/models/user.py
"""
Modelo de Usuario
Maneja todas las operaciones relacionadas con usuarios en MongoDB
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from pymongo import ReturnDocument


class UserModel:
    """
    Modelo para manejar operaciones de usuarios
    No instancies esta clase, usa métodos estáticos
    """
    
    def __init__(self, mongo, bcrypt):
        """
        Inicializa el modelo con las dependencias necesarias
        """
        self.users = mongo.db.users
        self.bcrypt = bcrypt
    
    def create_user(self, username, password, is_admin=False):
        """
        Crea un nuevo usuario en la base de datos
        
        Args:
            username (str): Nombre de usuario único
            password (str): Contraseña en texto plano (será hasheada)
            is_admin (bool): Si el usuario tiene privilegios de admin
        
        Returns:
            dict: Documento del usuario creado
        """
        pw_hash = self.bcrypt.generate_password_hash(password).decode()
        user_doc = {
            "username": username,
            "password": pw_hash,
            "created_at": datetime.now(ZoneInfo('America/Guayaquil')),
            "current_room": None,
            "socket_id": None,
            "is_admin": is_admin
        }
        self.users.insert_one(user_doc)
        return user_doc
    
    def find_by_username(self, username):
        """
        Busca un usuario por su nombre de usuario
        
        Args:
            username (str): Nombre de usuario a buscar
        
        Returns:
            dict | None: Documento del usuario o None si no existe
        """
        return self.users.find_one({"username": username})
    
    def find_by_socket_id(self, socket_id):
        """
        Busca un usuario por su socket_id
        
        Args:
            socket_id (str): ID del socket
        
        Returns:
            dict | None: Documento del usuario o None
        """
        return self.users.find_one({"socket_id": socket_id})
    
    def verify_password(self, user, password):
        """
        Verifica si la contraseña es correcta para un usuario
        
        Args:
            user (dict): Documento del usuario
            password (str): Contraseña en texto plano
        
        Returns:
            bool: True si la contraseña es correcta
        """
        return self.bcrypt.check_password_hash(user["password"], password)
    
    def update_socket(self, username, socket_id):
        """
        Actualiza el socket_id y last_login del usuario
        
        Args:
            username (str): Nombre de usuario
            socket_id (str): Nuevo socket ID
        
        Returns:
            dict | None: Usuario actualizado o None
        """
        return self.users.find_one_and_update(
            {"username": username},
            {"$set": {
                "socket_id": socket_id, 
                "last_login": datetime.utcnow()
            }},
            return_document=ReturnDocument.AFTER
        )
    
    def update_room(self, username, room_name, socket_id=None):
        """
        Actualiza la sala actual del usuario
        
        Args:
            username (str): Nombre de usuario
            room_name (str): Nombre de la sala (o None para limpiar)
            socket_id (str): Opcionalmente actualizar socket_id también
        
        Returns:
            dict | None: Usuario actualizado o None
        """
        update_data = {"current_room": room_name}
        if socket_id:
            update_data["socket_id"] = socket_id
        
        return self.users.find_one_and_update(
            {"username": username},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )
    
    def clear_socket(self, socket_id):
        """
        Limpia el socket_id y current_room de un usuario
        Útil para cuando se desconecta
        
        Args:
            socket_id (str): Socket ID a limpiar
        
        Returns:
            dict | None: Usuario actualizado o None
        """
        return self.users.find_one_and_update(
            {"socket_id": socket_id},
            {"$set": {
                "socket_id": None, 
                "current_room": None
            }},
            return_document=ReturnDocument.AFTER
        )
    
    def exists(self, username):
        """
        Verifica si un usuario existe
        
        Args:
            username (str): Nombre de usuario
        
        Returns:
            bool: True si existe
        """
        return self.users.find_one({"username": username}) is not None
    
    def count_all(self):
        """
        Cuenta todos los usuarios en la base de datos
        
        Returns:
            int: Cantidad de usuarios
        """
        return self.users.count_documents({})
    
    def count_in_room(self, room_name):
        """
        Cuenta usuarios en una sala específica
        
        Args:
            room_name (str): Nombre de la sala
        
        Returns:
            int: Cantidad de usuarios en la sala
        """
        return self.users.count_documents({"current_room": room_name})
    
    def create_anonymous_user(self, nickname, room_name, socket_id):
        """
        Crea un usuario anónimo temporal
        
        Args:
            nickname (str): Apodo del usuario anónimo
            room_name (str): Sala a la que se une
            socket_id (str): Socket ID del usuario
        
        Returns:
            dict: Usuario anónimo creado
        """
        import uuid
        anon_username = f"anon_{uuid.uuid4().hex[:8]}"
        
        user_doc = {
            "username": anon_username,
            "nickname": nickname,
            "is_anonymous": True,
            "created_at": datetime.utcnow(),
            "current_room": room_name,
            "socket_id": socket_id
        }
        self.users.insert_one(user_doc)
        return user_doc
    
    def delete_anonymous_user(self, username):
        """
        Elimina un usuario anónimo
        
        Args:
            username (str): Username del usuario anónimo
        
        Returns:
            bool: True si se eliminó
        """
        result = self.users.delete_one({"username": username})
        return result.deleted_count > 0
    
    def is_admin(self, username):
        """
        Verifica si un usuario es administrador
        
        Args:
            username (str): Nombre de usuario
        
        Returns:
            bool: True si es admin
        """
        user = self.users.find_one({"username": username})
        return user and user.get("is_admin", False)
    
    def nickname_in_use(self, nickname, room_name):
        """
        Verifica si un nickname ya está en uso en una sala
        
        Args:
            nickname (str): Nickname a verificar
            room_name (str): Sala donde verificar
        
        Returns:
            bool: True si ya está en uso
        """
        return self.users.find_one({
            "current_room": room_name, 
            "nickname": nickname
        }) is not None
    
    def device_in_room(self, socket_id):
        """
        Verifica si un dispositivo (socket) ya está en alguna sala
        
        Args:
            socket_id (str): Socket ID a verificar
        
        Returns:
            dict | None: Usuario si está en una sala, None si no
        """
        return self.users.find_one({
            "socket_id": socket_id, 
            "current_room": {"$ne": None}
        })