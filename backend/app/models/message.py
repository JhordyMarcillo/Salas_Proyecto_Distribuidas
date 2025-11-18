# app/models/message.py
"""
Modelo de Mensaje
Maneja todas las operaciones relacionadas con mensajes en MongoDB
"""

from datetime import datetime
from zoneinfo import ZoneInfo


class MessageModel:
    """
    Modelo para manejar operaciones de mensajes
    """
    
    def __init__(self, mongo):
        """
        Inicializa el modelo con la conexión a MongoDB
        """
        self.messages = mongo.db.messages
    
    def create_message(self, room, username, msg='', 
                      nickname=None, file_url=None, original_filename=None,
                      security_flags=None):
        """
        Crea un nuevo mensaje en la base de datos
        
        Args:
            room (str): Nombre de la sala
            username (str): Username del remitente
            msg (str): Contenido del mensaje de texto
            nickname (str): Nickname (para usuarios anónimos)
            file_url (str): URL del archivo adjunto (opcional)
            original_filename (str): Nombre original del archivo (opcional)
            security_flags (dict): Indicadores de seguridad (opcional)
                {
                    'has_encryption': bool,
                    'has_steganography_risk': bool,
                    'has_malicious_patterns': bool,
                    'has_suspicious_content': bool,
                    'risk_level': str,
                    'issues': list
                }
        
        Returns:
            dict: Documento del mensaje creado
        """
        message_doc = {
            "room": room,
            "username": username,
            "nickname": nickname,
            "msg": msg,
            "timestamp": datetime.now(ZoneInfo('America/Guayaquil')),
            "file_url": file_url,
            "original_filename": original_filename,
            "security_flags": security_flags or {
                'has_encryption': False,
                'has_steganography_risk': False,
                'has_malicious_patterns': False,
                'has_suspicious_content': False,
                'risk_level': 'low',
                'issues': []
            }
        }
        
        self.messages.insert_one(message_doc)
        return message_doc
    
    def get_room_messages(self, room, limit=100):
        """
        Obtiene los últimos mensajes de una sala
        
        Args:
            room (str): Nombre de la sala
            limit (int): Cantidad máxima de mensajes (default 100)
        
        Returns:
            list: Lista de mensajes ordenados del más antiguo al más reciente
        """
        # Obtener los últimos N mensajes ordenados de más reciente a más antiguo
        docs = list(
            self.messages
            .find({"room": room})
            .sort("timestamp", -1)
            .limit(limit)
        )
        # Revertir para que queden del más antiguo al más reciente
        return list(reversed(docs))
    
    def count_room_messages(self, room):
        """
        Cuenta los mensajes en una sala
        
        Args:
            room (str): Nombre de la sala
        
        Returns:
            int: Cantidad de mensajes
        """
        return self.messages.count_documents({"room": room})
    
    def delete_room_messages(self, room):
        """
        Elimina todos los mensajes de una sala
        Útil cuando se elimina una sala
        
        Args:
            room (str): Nombre de la sala
        
        Returns:
            int: Cantidad de mensajes eliminados
        """
        result = self.messages.delete_many({"room": room})
        return result.deleted_count
    
    def delete_user_messages(self, username):
        """
        Elimina todos los mensajes de un usuario
        
        Args:
            username (str): Username del usuario
        
        Returns:
            int: Cantidad de mensajes eliminados
        """
        result = self.messages.delete_many({"username": username})
        return result.deleted_count
    
    def get_messages_with_files(self, room):
        """
        Obtiene solo los mensajes que tienen archivos adjuntos
        
        Args:
            room (str): Nombre de la sala
        
        Returns:
            list: Lista de mensajes con archivos
        """
        return list(
            self.messages
            .find({
                "room": room,
                "file_url": {"$ne": None}
            })
            .sort("timestamp", -1)
        )
    
    def search_messages(self, room, search_term):
        """
        Busca mensajes que contengan un término específico
        
        Args:
            room (str): Nombre de la sala
            search_term (str): Término a buscar
        
        Returns:
            list: Lista de mensajes que coinciden
        """
        return list(
            self.messages
            .find({
                "room": room,
                "msg": {"$regex": search_term, "$options": "i"}
            })
            .sort("timestamp", -1)
        )
    
    def get_messages_by_user(self, room, username):
        """
        Obtiene todos los mensajes de un usuario en una sala
        
        Args:
            room (str): Nombre de la sala
            username (str): Username del usuario
        
        Returns:
            list: Lista de mensajes del usuario
        """
        return list(
            self.messages
            .find({
                "room": room,
                "username": username
            })
            .sort("timestamp", -1)
        )
    
    def format_message_for_emit(self, message_doc):
        """
        Formatea un documento de mensaje para enviar por WebSocket
        
        Args:
            message_doc (dict): Documento de mensaje de MongoDB
        
        Returns:
            dict: Mensaje formateado para enviar al cliente
        """
        timestamp = message_doc.get("timestamp")
        timestamp_iso = timestamp.isoformat() if timestamp else None
        
        return {
            "room": message_doc.get("room"),
            "username": message_doc.get("username"),
            "nickname": message_doc.get("nickname"),
            "msg": message_doc.get("msg"),
            "timestamp": timestamp_iso,
            "file_url": message_doc.get("file_url"),
            "original_filename": message_doc.get("original_filename"),
            "security_flags": message_doc.get("security_flags", {
                'has_encryption': False,
                'has_steganography_risk': False,
                'has_malicious_patterns': False,
                'has_suspicious_content': False,
                'risk_level': 'low',
                'issues': []
            })
        }
    
    def format_messages_for_api(self, messages):
        """
        Formatea múltiples mensajes para respuesta HTTP
        
        Args:
            messages (list): Lista de documentos de mensajes
        
        Returns:
            list: Lista de mensajes formateados
        """
        formatted = []
        for msg in messages:
            ts = msg.get("timestamp")
            ts_iso = None
            if ts:
                ts_iso = ts.isoformat() + "Z"
            
            formatted.append({
                "username": msg.get("username"),
                "nickname": msg.get("nickname"),
                "msg": msg.get("msg"),
                "timestamp": ts_iso,
                "file_url": msg.get("file_url"),
                "original_filename": msg.get("original_filename"),
                "security_flags": msg.get("security_flags", {
                    'has_encryption': False,
                    'has_steganography_risk': False,
                    'has_malicious_patterns': False,
                    'has_suspicious_content': False,
                    'risk_level': 'low',
                    'issues': []
                })
            })
        
        return formatted