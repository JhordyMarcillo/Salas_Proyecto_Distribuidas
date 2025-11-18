# app/routes/upload.py
"""
Rutas HTTP para subida de archivos
Maneja uploads a Cloudinary
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from app.middleware import require_jwt_http
from app.services import CloudinaryService, SecurityService

# Crear Blueprint
upload_bp = Blueprint('upload', __name__, url_prefix='/upload')


@upload_bp.route('', methods=['POST', 'OPTIONS'])
@cross_origin(origins="*")
@require_jwt_http
def upload_file(username):
    """
    POST /upload
    Sube un archivo a Cloudinary
    
    Headers:
        Authorization: Bearer <token>
        Content-Type: multipart/form-data
    
    Form Data:
        file: archivo a subir (requerido)
        room: nombre de la sala (opcional, para validaciones)
    
    Response:
        {
            "msg": "Archivo subido exitosamente",
            "url": "https://res.cloudinary.com/...",
            "filename": "documento.pdf",
            "public_id": "chat_uploads/admin/abc123",
            "format": "pdf",
            "size_mb": 2.5
        }
    """
    # 1. Verificar que Cloudinary está configurado
    if not CloudinaryService.is_configured():
        if not CloudinaryService.configure():
            return jsonify({
                'error': 'Servicio de upload no disponible. Contacta al administrador.'
            }), 503
    
    # 2. Verificar que hay archivo en la petición
    if 'file' not in request.files:
        return jsonify({'error': 'No se encontró el archivo. Usa el campo "file"'}), 400
    
    file_to_upload = request.files['file']
    
    # 3. Verificar que se seleccionó un archivo
    if file_to_upload.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    # 4. Validar tipo de archivo
    valid_type, type_error = CloudinaryService.validate_file_type(file_to_upload.filename)
    if not valid_type:
        return jsonify({'error': type_error}), 400
    
    # 4.5. Validar seguridad del archivo (esteganografía, encriptación)
    # Leer datos del archivo para análisis de seguridad
    file_to_upload.seek(0)
    file_data = file_to_upload.read()
    file_to_upload.seek(0)  # Resetear para upload posterior
    
    security_check = SecurityService.check_file_steganography(
        file_to_upload.filename,
        file_data=file_data
    )
    
    # Si el riesgo es alto, rechazar o advertir
    if security_check['risk_level'] == 'high':
        return jsonify({
            'error': 'Archivo rechazado por riesgos de seguridad',
            'details': security_check['openstego_indicators'],
            'risk_level': security_check['risk_level']
        }), 403
    
    # 5. Validar tamaño del archivo
    max_mb = 10  # Default
    
    # Si se especifica sala, usar su límite
    room_name = request.form.get('room')
    if room_name:
        from app.models import get_room_model
        room_model = get_room_model()
        max_mb = room_model.get_max_file_size(room_name)
    
    valid_size, size_error = CloudinaryService.validate_file_size(file_to_upload, max_mb=max_mb)
    if not valid_size:
        return jsonify({'error': size_error}), 400
    
    # 6. Subir archivo
    try:
        result = CloudinaryService.upload_file(file_to_upload, username=username)
        
        # Calcular tamaño en MB
        size_mb = round(result.get('bytes', 0) / (1024 * 1024), 2)
        
        print(f"[upload] {username} subió {result['filename']} ({size_mb}MB)")
        
        # Incluir información de seguridad en respuesta
        return jsonify({
            'msg': 'Archivo subido exitosamente',
            'url': result['url'],
            'filename': result['filename'],
            'public_id': result['public_id'],
            'format': result['format'],
            'size_mb': size_mb,
            'security_check': {
                'risk_level': security_check['risk_level'],
                'has_steganography_risk': security_check['has_steganography_risk'],
                'openstego_indicators': security_check['openstego_indicators']
            }
        }), 201
        
    except Exception as e:
        print(f"[upload error] {username}: {str(e)}")
        return jsonify({'error': f'Error al subir archivo: {str(e)}'}), 500


@upload_bp.route('/validate', methods=['POST'])
@require_jwt_http
def validate_file(username):
    """
    POST /upload/validate
    Valida un archivo ANTES de subirlo (útil para frontend)
    
    Headers:
        Authorization: Bearer <token>
    
    Body:
        {
            "filename": "documento.pdf",
            "size_bytes": 5242880,
            "room": "General"  # Opcional
        }
    
    Response:
        {
            "valid": true,
            "errors": []
        }
        
        O si hay errores:
        {
            "valid": false,
            "errors": [
                "Archivo excede el límite de 10 MB",
                "Tipo de archivo no permitido: .exe"
            ]
        }
    """
    data = request.get_json() or {}
    
    filename = data.get('filename')
    size_bytes = data.get('size_bytes')
    room_name = data.get('room')
    
    if not filename or size_bytes is None:
        return jsonify({'error': 'filename y size_bytes requeridos'}), 400
    
    errors = []
    
    # Validar tipo
    valid_type, type_error = CloudinaryService.validate_file_type(filename)
    if not valid_type:
        errors.append(type_error)
    
    # Validar tamaño
    max_mb = 10
    if room_name:
        from app.models import get_room_model
        room_model = get_room_model()
        max_mb = room_model.get_max_file_size(room_name)
    
    size_mb = size_bytes / (1024 * 1024)
    if size_mb > max_mb:
        errors.append(f"Archivo excede el límite de {max_mb} MB")
    
    return jsonify({
        'valid': len(errors) == 0,
        'errors': errors,
        'max_size_mb': max_mb
    }), 200


@upload_bp.route('/delete', methods=['POST'])
@require_jwt_http
def delete_file(username):
    """
    POST /upload/delete
    Elimina un archivo de Cloudinary
    
    Headers:
        Authorization: Bearer <token>
    
    Body:
        {
            "public_id": "chat_uploads/admin/abc123"
        }
    
    Response:
        {
            "msg": "Archivo eliminado exitosamente"
        }
    """
    data = request.get_json() or {}
    public_id = data.get('public_id')
    
    if not public_id:
        return jsonify({'error': 'public_id requerido'}), 400
    
    # Verificar que el archivo pertenece al usuario (seguridad)
    if not public_id.startswith(f"chat_uploads/{username}/"):
        from app.models import get_user_model
        user_model = get_user_model()
        if not user_model.is_admin(username):
            return jsonify({'error': 'No tienes permiso para eliminar este archivo'}), 403
    
    # Eliminar
    success = CloudinaryService.delete_file(public_id)
    
    if success:
        return jsonify({'msg': 'Archivo eliminado exitosamente'}), 200
    else:
        return jsonify({'error': 'No se pudo eliminar el archivo'}), 500


@upload_bp.route('/thumbnail', methods=['POST'])
@require_jwt_http
def generate_thumbnail(username):
    """
    POST /upload/thumbnail
    Genera URL de thumbnail para una imagen
    
    Headers:
        Authorization: Bearer <token>
    
    Body:
        {
            "public_id": "chat_uploads/admin/image123",
            "width": 200,
            "height": 200
        }
    
    Response:
        {
            "thumbnail_url": "https://res.cloudinary.com/...w_200,h_200..."
        }
    """
    data = request.get_json() or {}
    public_id = data.get('public_id')
    width = data.get('width', 200)
    height = data.get('height', 200)
    
    if not public_id:
        return jsonify({'error': 'public_id requerido'}), 400
    
    thumbnail_url = CloudinaryService.generate_thumbnail_url(
        public_id, 
        width=width, 
        height=height
    )
    
    if thumbnail_url:
        return jsonify({'thumbnail_url': thumbnail_url}), 200
    else:
        return jsonify({'error': 'No se pudo generar thumbnail'}), 500


@upload_bp.route('/list', methods=['GET'])
@require_jwt_http
def list_user_files(username):
    """
    GET /upload/list
    Lista todos los archivos subidos por el usuario
    
    Headers:
        Authorization: Bearer <token>
    
    Query Params:
        ?limit=50
    
    Response:
        {
            "files": [
                {
                    "public_id": "chat_uploads/admin/abc123",
                    "url": "https://...",
                    "format": "pdf",
                    "bytes": 1234567,
                    "created_at": "2025-01-15T10:30:00"
                }
            ],
            "total": 3
        }
    """
    limit = request.args.get('limit', 50, type=int)
    
    # Listar archivos del usuario
    folder = f"chat_uploads/{username}"
    files = CloudinaryService.list_files(folder, max_results=limit)
    
    return jsonify({
        'files': files,
        'total': len(files)
    }), 200


# Manejo de errores
@upload_bp.errorhandler(413)
def request_entity_too_large(error):
    """Archivo demasiado grande (configuración de Flask)"""
    return jsonify({'error': 'Archivo demasiado grande'}), 413


@upload_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Error interno del servidor'}), 500