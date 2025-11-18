# app/services/jwt_service.py
"""
Servicio de JWT (JSON Web Tokens)
Maneja la creación, verificación y validación de tokens de autenticación
"""

import jwt
from datetime import datetime, timedelta
from flask import current_app


class JWTService:
    """
    Servicio para manejar tokens JWT
    Todos los métodos son estáticos, no necesitas instanciar la clase
    """
    
    @staticmethod
    def create_token(username: str, expires_hours: int = None) -> str:
        """
        Crea un token JWT para un usuario
        
        Args:
            username (str): Nombre de usuario que se incluirá en el token
            expires_hours (int): Horas de validez (usa config si no se especifica)
        
        Returns:
            str: Token JWT firmado
        
        Ejemplo:
            token = JWTService.create_token("admin")
            # Retorna: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        """
        if expires_hours is None:
            expires_hours = current_app.config['JWT_EXPIRE_HOURS']
        
        exp = datetime.utcnow() + timedelta(hours=expires_hours)
        payload = {
            "sub": username,      # Subject: el usuario
            "exp": exp,           # Expiration time
            "iat": datetime.utcnow(),  # Issued at
            "type": "access"      # Tipo de token
        }
        
        token = jwt.encode(
            payload, 
            current_app.config['JWT_SECRET'], 
            algorithm=current_app.config['JWT_ALGORITHM']
        )
        
        # Convertir a string si es necesario (versiones antiguas de PyJWT)
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        return token
    
    @staticmethod
    def verify_token(token: str) -> str:
        """
        Verifica y decodifica un token JWT
        
        Args:
            token (str): Token JWT a verificar
        
        Returns:
            str: Username del usuario autenticado
        
        Raises:
            ValueError: Si el token es inválido o expirado
                - "token_expired": Token válido pero expirado
                - "token_invalid": Token malformado o firma inválida
        
        Ejemplo:
            try:
                username = JWTService.verify_token(token)
                print(f"Usuario autenticado: {username}")
            except ValueError as e:
                if str(e) == "token_expired":
                    print("Token expirado, solicita uno nuevo")
                else:
                    print("Token inválido")
        """
        try:
            payload = jwt.decode(
                token, 
                current_app.config['JWT_SECRET'], 
                algorithms=[current_app.config['JWT_ALGORITHM']]
            )
            return payload["sub"]
        
        except jwt.ExpiredSignatureError:
            raise ValueError("token_expired")
        
        except jwt.InvalidTokenError:
            raise ValueError("token_invalid")
    
    @staticmethod
    def decode_token_unsafe(token: str) -> dict:
        """
        Decodifica un token SIN verificar la firma
        ⚠️ SOLO USAR PARA DEBUGGING - NO CONFÍES EN ESTOS DATOS
        
        Args:
            token (str): Token JWT
        
        Returns:
            dict: Payload del token (sin verificar)
        
        Ejemplo de uso (solo debug):
            payload = JWTService.decode_token_unsafe(token)
            print(f"Token expira en: {payload.get('exp')}")
        """
        return jwt.decode(
            token, 
            options={"verify_signature": False}
        )
    
    @staticmethod
    def get_token_expiration(token: str) -> datetime:
        """
        Obtiene la fecha de expiración de un token
        
        Args:
            token (str): Token JWT
        
        Returns:
            datetime: Fecha de expiración
        
        Raises:
            ValueError: Si el token es inválido
        """
        try:
            payload = JWTService.decode_token_unsafe(token)
            exp_timestamp = payload.get('exp')
            if exp_timestamp:
                return datetime.utcfromtimestamp(exp_timestamp)
            return None
        except Exception:
            raise ValueError("token_invalid")
    
    @staticmethod
    def is_token_expired(token: str) -> bool:
        """
        Verifica si un token está expirado (sin verificar firma)
        
        Args:
            token (str): Token JWT
        
        Returns:
            bool: True si está expirado
        """
        try:
            exp = JWTService.get_token_expiration(token)
            if exp:
                return datetime.utcnow() > exp
            return True
        except Exception:
            return True
    
    @staticmethod
    def create_refresh_token(username: str) -> str:
        """
        Crea un token de refresco con mayor duración
        
        Args:
            username (str): Nombre de usuario
        
        Returns:
            str: Refresh token JWT
        """
        exp = datetime.utcnow() + timedelta(days=30)
        payload = {
            "sub": username,
            "exp": exp,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        token = jwt.encode(
            payload, 
            current_app.config['JWT_SECRET'], 
            algorithm=current_app.config['JWT_ALGORITHM']
        )
        
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        return token
    
    @staticmethod
    def verify_refresh_token(token: str) -> str:
        """
        Verifica un refresh token
        
        Args:
            token (str): Refresh token
        
        Returns:
            str: Username
        
        Raises:
            ValueError: Si el token es inválido o no es tipo refresh
        """
        try:
            payload = jwt.decode(
                token, 
                current_app.config['JWT_SECRET'], 
                algorithms=[current_app.config['JWT_ALGORITHM']]
            )
            
            if payload.get('type') != 'refresh':
                raise ValueError("token_invalid")
            
            return payload["sub"]
        
        except jwt.ExpiredSignatureError:
            raise ValueError("token_expired")
        
        except jwt.InvalidTokenError:
            raise ValueError("token_invalid")
    
    @staticmethod
    def extract_username_from_token(token: str) -> str:
        """
        Extrae el username sin verificar (útil para logging)
        
        Args:
            token (str): Token JWT
        
        Returns:
            str: Username o "unknown" si falla
        """
        try:
            payload = JWTService.decode_token_unsafe(token)
            return payload.get('sub', 'unknown')
        except Exception:
            return 'unknown'