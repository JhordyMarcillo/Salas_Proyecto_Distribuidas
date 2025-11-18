"""
Script de verificación - Valida que las variables de .env se cargan correctamente
Ejecuta: python verify_config.py
"""

import os
from dotenv import load_dotenv
from app.config import config

# Cargar variables
load_dotenv()

print("=" * 70)
print("🔍 VERIFICACIÓN DE CONFIGURACIÓN")
print("=" * 70)

# Variables del .env
print("\n📝 Variables desde .env:")
print(f"  MONGO_URI: {os.getenv('MONGO_URI')}")
print(f"  JWT_SECRET: {os.getenv('JWT_SECRET')[:20]}..." if os.getenv('JWT_SECRET') else "  JWT_SECRET: NO CONFIGURADA")
print(f"  CLOUDINARY_CLOUD_NAME: {os.getenv('CLOUDINARY_CLOUD_NAME')}")
print(f"  FLASK_ENV: {os.getenv('FLASK_ENV')}")

# Cargar configuración
config_name = os.getenv('FLASK_ENV', 'development')
print(f"\n⚙️  Ambiente seleccionado: {config_name}")

try:
    Config = config[config_name]
    app_config = Config()
    
    print("\n✅ Variables cargadas en la aplicación:")
    print(f"  MONGO_URI: {app_config.MONGO_URI}")
    print(f"  JWT_SECRET: {app_config.JWT_SECRET[:20]}...")
    print(f"  JWT_ALGORITHM: {app_config.JWT_ALGORITHM}")
    print(f"  JWT_EXPIRE_HOURS: {app_config.JWT_EXPIRE_HOURS}")
    print(f"  CLOUDINARY_CLOUD_NAME: {app_config.CLOUDINARY_CLOUD_NAME}")
    print(f"  CLOUDINARY_API_KEY: {app_config.CLOUDINARY_API_KEY[:10]}..." if app_config.CLOUDINARY_API_KEY else "  CLOUDINARY_API_KEY: VACÍA")
    print(f"  DEBUG: {app_config.DEBUG}")
    print(f"  TESTING: {app_config.TESTING}")
    
    print("\n" + "=" * 70)
    print("✅ CONFIGURACIÓN CORRECTA - Listo para usar!")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print("=" * 70)
