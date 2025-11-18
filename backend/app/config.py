"""
Configuración de la aplicación Flask
Define diferentes ambientes: desarrollo, testing, producción
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env
load_dotenv()


class Config:
    """Configuración base para todos los ambientes"""
    
    # Flask
    DEBUG = False
    TESTING = False
    
    # MongoDB
    MONGO_URI = os.getenv(
        'MONGO_URI',
        'mongodb://localhost:27017/salas_distribuidas'
    )
    
    # JWT
    JWT_SECRET = os.getenv(
        'JWT_SECRET',
        'tu_clave_secreta_super_segura_cambiar_en_produccion'
    )
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRE_HOURS = 24
    JWT_REFRESH_EXPIRE_DAYS = 30
    
    # Cloudinary (para subida de archivos)
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME', '')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY', '')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET', '')
    
    # Límites de archivo
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS = {
        'jpg', 'jpeg', 'png', 'gif', 'webp',
        'mp4', 'mov', 'avi',
        'pdf', 'doc', 'docx',
        'txt', 'csv', 'xlsx'
    }
    
    # CORS
    CORS_ORIGINS = ['*']
    
    # WebSocket
    SOCKETIO_ASYNC_MODE = 'eventlet'
    
    # Logging
    LOG_LEVEL = 'INFO'


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'
    
    # Claves menos seguras en desarrollo (SOLO PARA DESARROLLO)
    JWT_SECRET = os.getenv(
        'JWT_SECRET',
        'secret_development_key_123456789'
    )


class TestingConfig(Config):
    """Configuración para testing"""
    TESTING = True
    DEBUG = True
    
    # Base de datos de prueba
    MONGO_URI = 'mongodb://localhost:27017/salas_distribuidas_test'
    
    # JWT más simple para testing
    JWT_SECRET = 'secret_testing_key'
    JWT_EXPIRE_HOURS = 1


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'WARNING'
    
    # En producción, SIEMPRE debe estar configurado por variable de entorno
    MONGO_URI = os.getenv('MONGO_URI')
    JWT_SECRET = os.getenv('JWT_SECRET')
    
    def __init__(self):
        """Validar configuración en producción"""
        super().__init__()
        
        # Solo validar si realmente estamos en producción
        if os.getenv('FLASK_ENV') == 'production':
            if not self.MONGO_URI:
                raise ValueError('MONGO_URI debe estar configurada en producción')
            if not self.JWT_SECRET or len(self.JWT_SECRET) < 32:
                raise ValueError('JWT_SECRET debe estar configurada en producción con al menos 32 caracteres')


# Mapeo de configuraciones por nombre
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
