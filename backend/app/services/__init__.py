# app/services/__init__.py
"""
Services Package

Los servicios contienen la LÓGICA DE NEGOCIO de la aplicación.
A diferencia de los modelos (que solo acceden a datos), los servicios:
- Coordinan operaciones entre múltiples modelos
- Implementan reglas de negocio complejas
- Manejan integraciones con APIs externas (JWT, Cloudinary)
- Procesan y transforman datos

Diferencia entre Models y Services:
- Models: "¿CÓMO accedo a los datos?" (CRUD simple)
- Services: "¿QUÉ reglas de negocio aplico?" (lógica compleja)

"""

from app.services.jwt_service import JWTService
from app.services.cloudinary_service import CloudinaryService
from app.services.room_service import RoomService
from app.services.security_service import SecurityService

# Exportar todos los servicios
__all__ = [
    'JWTService',
    'CloudinaryService',
    'RoomService',
    'SecurityService'
]


"""
=============================================================================
CUÁNDO USAR CADA SERVICIO
=============================================================================

📝 JWTService
-------------
Cuando necesites:
- Crear tokens de autenticación
- Verificar tokens
- Crear refresh tokens
- Obtener información de tokens

Ejemplo:
    from app.services import JWTService
    
    token = JWTService.create_token('admin')
    username = JWTService.verify_token(token)


☁️ CloudinaryService
--------------------
Cuando necesites:
- Subir archivos a la nube
- Eliminar archivos
- Generar thumbnails
- Validar archivos antes de subirlos

Ejemplo:
    from app.services import CloudinaryService
    
    file = request.files['file']
    result = CloudinaryService.upload_file(file, username='admin')
    print(result['url'])


🏠 RoomService
--------------
Cuando necesites:
- Operaciones complejas con salas (múltiples modelos)
- Validar permisos de sala
- Obtener estadísticas de salas
- Eliminar sala con todos sus datos

Ejemplo:
    from app.services import RoomService
    
    can_join, error = RoomService.validate_join_request(
        'admin', 'General', '1234'
    )


🔒 SecurityService
------------------
Cuando necesites:
- Detectar encriptación en mensajes
- Validar archivos con esteganografía (OpenStego)
- Escanear patrones maliciosos
- Validar seguridad completa de mensajes con archivos

Ejemplo:
    from app.services import SecurityService
    
    # Detectar encriptación
    encryption = SecurityService.detect_encryption_in_text(message)
    
    # Verificar archivo
    stego = SecurityService.check_file_steganography('image.png')
    
    # Validación completa
    security = SecurityService.validate_message_security(
        message_text, file_info
    )


=============================================================================
PATRÓN DE USO TÍPICO
=============================================================================

En una ruta HTTP:
------------------
@app.route('/rooms/<room_name>/join', methods=['POST'])
@require_jwt_http
def join_room(username, room_name):
    # 1. Obtener datos del request
    data = request.get_json()
    pin = data.get('pin')
    
    # 2. Usar SERVICE para validar (lógica de negocio)
    can_join, error = RoomService.validate_join_request(username, room_name, pin)
    if not can_join:
        return jsonify({"error": error}), 403
    
    # 3. Usar MODEL para actualizar datos
    user_model = get_user_model()
    user_model.update_room(username, room_name)
    
    return jsonify({"msg": "Unido exitosamente"})


En un evento WebSocket:
------------------------
@socketio.on("upload_file")
@require_token_socket
def handle_upload(username, data):
    # 1. Validar con SERVICE
    file_size = data.get('file_size_mb')
    can_send, error = RoomService.can_send_file(username, data['room'], file_size)
    if not can_send:
        emit("error", {"msg": error})
        return
    
    # 2. Subir con SERVICE
    file = data.get('file')
    result = CloudinaryService.upload_file(file, username)
    
    # 3. Guardar con MODEL
    message_model = get_message_model()
    message_model.create_message(
        room=data['room'],
        username=username,
        file_url=result['url']
    )


=============================================================================
PRINCIPIO DE RESPONSABILIDAD ÚNICA
=============================================================================

❌ MAL (todo mezclado):
@app.route('/rooms', methods=['POST'])
def create_room():
    # Parsear datos
    # Validar JWT
    # Verificar admin
    # Validar PIN
    # Subir logo a Cloudinary
    # Crear sala en DB
    # Enviar notificación
    # Todo en una sola función = pesadilla de mantenimiento


✅ BIEN (separado en capas):
@app.route('/rooms', methods=['POST'])
@require_jwt_http        # Middleware: valida JWT
@require_admin           # Middleware: valida admin
def create_room(username):
    data = request.get_json()
    
    # Service: lógica de negocio
    result = RoomService.create_room_with_validations(data)
    
    # Service: subir archivo si hay
    if data.get('logo'):
        CloudinaryService.upload_file(data['logo'])
    
    return jsonify(result)

=============================================================================
"""