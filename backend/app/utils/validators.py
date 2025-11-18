"""
Validadores personalizados
Funciones para validar datos de entrada en toda la aplicación
"""

import re
from flask import current_app


class ValidationError(Exception):
    """Excepción personalizada para errores de validación"""
    pass


class Validators:
    """Clase con métodos estáticos para validación"""
    
    @staticmethod
    def validate_username(username):
        """
        Valida un nombre de usuario
        
        Args:
            username (str): Nombre de usuario a validar
        
        Raises:
            ValidationError: Si el formato es inválido
        
        Returns:
            str: Username validado y limpio
        """
        if not username:
            raise ValidationError("username no puede estar vacío")
        
        username = username.strip()
        
        if len(username) < 3:
            raise ValidationError("username debe tener al menos 3 caracteres")
        
        if len(username) > 50:
            raise ValidationError("username no puede exceder 50 caracteres")
        
        # Solo letras, números y guión bajo
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError(
                "username solo puede contener letras, números y guión bajo"
            )
        
        return username
    
    @staticmethod
    def validate_password(password):
        """
        Valida una contraseña
        
        Args:
            password (str): Contraseña a validar
        
        Raises:
            ValidationError: Si no cumple requisitos de seguridad
        
        Returns:
            str: Password validado
        """
        if not password:
            raise ValidationError("password no puede estar vacío")
        
        if len(password) < 6:
            raise ValidationError("password debe tener al menos 6 caracteres")
        
        if len(password) > 128:
            raise ValidationError("password no puede exceder 128 caracteres")
        
        return password
    
    @staticmethod
    def validate_email(email):
        """
        Valida un correo electrónico
        
        Args:
            email (str): Email a validar
        
        Raises:
            ValidationError: Si el formato es inválido
        
        Returns:
            str: Email validado en minúsculas
        """
        if not email:
            raise ValidationError("email no puede estar vacío")
        
        email = email.strip().lower()
        
        # Regex básico para email
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            raise ValidationError("email tiene formato inválido")
        
        if len(email) > 255:
            raise ValidationError("email no puede exceder 255 caracteres")
        
        return email
    
    @staticmethod
    def validate_room_name(room_name):
        """
        Valida un nombre de sala de chat
        
        Args:
            room_name (str): Nombre de sala a validar
        
        Raises:
            ValidationError: Si el formato es inválido
        
        Returns:
            str: Room name validado
        """
        if not room_name:
            raise ValidationError("room_name no puede estar vacío")
        
        room_name = room_name.strip()
        
        if len(room_name) < 2:
            raise ValidationError("room_name debe tener al menos 2 caracteres")
        
        if len(room_name) > 100:
            raise ValidationError("room_name no puede exceder 100 caracteres")
        
        # Permitir letras, números, espacios, guión y guión bajo
        if not re.match(r'^[a-zA-Z0-9\s_-]+$', room_name):
            raise ValidationError(
                "room_name solo puede contener letras, números, espacios, guión y guión bajo"
            )
        
        return room_name
    
    @staticmethod
    def validate_pin(pin):
        """
        Valida un PIN de sala
        
        Args:
            pin (str|int): PIN a validar
        
        Raises:
            ValidationError: Si el PIN es inválido
        
        Returns:
            str: PIN validado como string
        """
        if pin is None:
            return None  # PIN es opcional
        
        pin_str = str(pin).strip()
        
        if not pin_str.isdigit():
            raise ValidationError("PIN debe contener solo dígitos")
        
        if len(pin_str) < 4:
            raise ValidationError("PIN debe tener al menos 4 dígitos")
        
        if len(pin_str) > 10:
            raise ValidationError("PIN no puede exceder 10 dígitos")
        
        return pin_str
    
    @staticmethod
    def validate_message(message):
        """
        Valida un mensaje de chat
        
        Args:
            message (str): Mensaje a validar
        
        Raises:
            ValidationError: Si el mensaje es inválido
        
        Returns:
            str: Mensaje validado
        """
        if not message:
            raise ValidationError("message no puede estar vacío")
        
        message = message.strip()
        
        if len(message) > 5000:
            raise ValidationError("message no puede exceder 5000 caracteres")
        
        return message
    
    @staticmethod
    def validate_filename(filename):
        """
        Valida un nombre de archivo
        
        Args:
            filename (str): Nombre de archivo a validar
        
        Raises:
            ValidationError: Si el nombre es inválido
        
        Returns:
            str: Nombre de archivo validado
        """
        if not filename:
            raise ValidationError("filename no puede estar vacío")
        
        filename = filename.strip()
        
        if len(filename) > 255:
            raise ValidationError("filename no puede exceder 255 caracteres")
        
        # Verificar que tiene extensión
        if '.' not in filename:
            raise ValidationError("filename debe tener extensión")
        
        # Obtener extensión
        extension = filename.rsplit('.', 1)[1].lower()
        
        # Validar que la extensión está permitida
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', set())
        
        if allowed_extensions and extension not in allowed_extensions:
            raise ValidationError(
                f"extensión no permitida: .{extension}"
            )
        
        # No permitir caracteres peligrosos
        if re.search(r'[<>:"|?*\x00-\x1f]', filename):
            raise ValidationError("filename contiene caracteres no permitidos")
        
        return filename
    
    @staticmethod
    def validate_description(description, max_length=500):
        """
        Valida una descripción
        
        Args:
            description (str): Descripción a validar
            max_length (int): Longitud máxima
        
        Raises:
            ValidationError: Si la descripción es inválida
        
        Returns:
            str: Descripción validada
        """
        if description is None:
            return ""
        
        description = str(description).strip()
        
        if len(description) > max_length:
            raise ValidationError(
                f"description no puede exceder {max_length} caracteres"
            )
        
        return description
    
    @staticmethod
    def validate_room_type(room_type):
        """
        Valida el tipo de sala
        
        Args:
            room_type (str): Tipo de sala ('text' o 'multimedia')
        
        Raises:
            ValidationError: Si el tipo es inválido
        
        Returns:
            str: Tipo de sala validado
        """
        if not room_type:
            return 'text'  # Default
        
        room_type = room_type.strip().lower()
        
        allowed_types = ['text', 'multimedia']
        
        if room_type not in allowed_types:
            raise ValidationError(
                f"room_type debe ser 'text' o 'multimedia', no '{room_type}'"
            )
        
        return room_type
    
    @staticmethod
    def validate_jwt_token(token):
        """
        Valida formato básico de un token JWT
        
        Args:
            token (str): Token JWT a validar
        
        Raises:
            ValidationError: Si el formato es inválido
        
        Returns:
            str: Token validado
        """
        if not token:
            raise ValidationError("token no puede estar vacío")
        
        token = token.strip()
        
        # JWT debe tener 3 partes separadas por puntos
        parts = token.split('.')
        
        if len(parts) != 3:
            raise ValidationError("formato de token inválido")
        
        return token
    
    @staticmethod
    def validate_file_size(file_size_bytes, max_mb=10):
        """
        Valida el tamaño de un archivo
        
        Args:
            file_size_bytes (int): Tamaño en bytes
            max_mb (int): Tamaño máximo permitido en MB
        
        Raises:
            ValidationError: Si el archivo excede el límite
        
        Returns:
            bool: True si es válido
        """
        max_bytes = max_mb * 1024 * 1024
        
        if file_size_bytes > max_bytes:
            raise ValidationError(
                f"archivo excede el límite de {max_mb} MB"
            )
        
        return True
    
    @staticmethod
    def sanitize_input(text):
        """
        Sanitiza un input removiendo espacios en blanco al inicio y final
        
        Args:
            text (str): Texto a sanitizar
        
        Returns:
            str: Texto sanitizado
        """
        if isinstance(text, str):
            return text.strip()
        return text
    
    @staticmethod
    def is_safe_string(text, max_length=1000):
        """
        Verifica que un string es seguro (no contiene caracteres peligrosos)
        
        Args:
            text (str): Texto a verificar
            max_length (int): Longitud máxima
        
        Returns:
            bool: True si es seguro
        """
        if not isinstance(text, str):
            return False
        
        if len(text) > max_length:
            return False
        
        # Verificar que no contenga caracteres de control (excepto espacios, enter, tab)
        for char in text:
            if ord(char) < 32 and char not in ('\n', '\t', '\r'):
                return False
        
        return True


# Funciones de utilidad rápidas
def validate_all(**kwargs):
    """
    Valida múltiples parámetros a la vez
    
    Raises:
        ValidationError: Con el primer error encontrado
    
    Ejemplo:
        validate_all(
            username=Validators.validate_username(data['username']),
            password=Validators.validate_password(data['password']),
            room_name=Validators.validate_room_name(data['room'])
        )
    """
    for key, value in kwargs.items():
        if isinstance(value, Exception):
            raise value
    return True
