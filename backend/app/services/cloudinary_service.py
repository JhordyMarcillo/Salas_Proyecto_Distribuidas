# app/services/cloudinary_service.py
"""
Servicio de Cloudinary
Maneja la subida, eliminación y gestión de archivos en Cloudinary
"""
import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import current_app


class CloudinaryService:
    """
    Servicio para interactuar con Cloudinary (almacenamiento de archivos)
    """
    
    _configured = False
    
    @classmethod
    def configure(cls) -> bool:
        """
        Configura Cloudinary con las credenciales de la aplicación
        Solo se ejecuta una vez (patrón singleton)
        
        Returns:
            bool: True si se configuró correctamente, False en caso contrario
        """
        if cls._configured:
            return True
        
        try:
            config = current_app.config
            
            # Verificar que todas las credenciales estén presentes
            if not all([
                config.get('CLOUDINARY_CLOUD_NAME'), 
                config.get('CLOUDINARY_API_KEY'), 
                config.get('CLOUDINARY_API_SECRET')
            ]):
                print("[warning] Cloudinary no configurado: faltan credenciales")
                return False
            
            # Configurar Cloudinary
            cloudinary.config(
                cloud_name=config['CLOUDINARY_CLOUD_NAME'],
                api_key=config['CLOUDINARY_API_KEY'],
                api_secret=config['CLOUDINARY_API_SECRET'],
                secure=True
            )
            
            cls._configured = True
            print("[info] Cloudinary configurado correctamente")
            return True
            
        except Exception as e:
            print(f"[error] Error configurando Cloudinary: {e}")
            cls._configured = False
            return False
    
    @classmethod
    def is_configured(cls) -> bool:
        """
        Verifica si Cloudinary está configurado
        
        Returns:
            bool: True si está configurado
        """
        return cls._configured
    
    @classmethod
    def upload_file(cls, file, username='anonymous', folder_prefix='chat_uploads'):
        """
        Sube un archivo a Cloudinary
        
        Args:
            file: Archivo a subir (desde request.files)
            username (str): Usuario que sube el archivo (para organizar carpetas)
            folder_prefix (str): Prefijo de la carpeta en Cloudinary
        
        Returns:
            dict: Información del archivo subido
                {
                    'url': 'https://...',
                    'filename': 'documento.pdf',
                    'public_id': 'chat_uploads/user/abc123',
                    'format': 'pdf',
                    'bytes': 1234567
                }
        
        Raises:
            Exception: Si Cloudinary no está configurado o falla la subida
        
        Ejemplo:
            file = request.files['file']
            result = CloudinaryService.upload_file(file, username='admin')
            print(f"URL: {result['url']}")
        """
        if not cls._configured:
            if not cls.configure():
                raise Exception("Cloudinary no está configurado correctamente")
        
        # Crear carpeta específica para el usuario
        folder = f"{folder_prefix}/{username}"
        
        # Subir archivo (auto-detecta el tipo)
        upload_result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type="auto",  # Detecta automáticamente: image, video, raw
            use_filename=True,      # Preserva el nombre del archivo
            unique_filename=True    # Evita sobrescribir archivos
        )
        
        # Retornar información relevante
        return {
            'url': upload_result.get('secure_url') or upload_result.get('url'),
            'filename': upload_result.get('original_filename', file.filename),
            'public_id': upload_result.get('public_id'),
            'format': upload_result.get('format'),
            'bytes': upload_result.get('bytes'),
            'resource_type': upload_result.get('resource_type')
        }
    
    @classmethod
    def delete_file(cls, public_id, resource_type='auto'):
        """
        Elimina un archivo de Cloudinary
        
        Args:
            public_id (str): ID público del archivo en Cloudinary
            resource_type (str): Tipo de recurso ('image', 'video', 'raw', 'auto')
        
        Returns:
            bool: True si se eliminó correctamente
        
        Ejemplo:
            CloudinaryService.delete_file('chat_uploads/user/abc123')
        """
        if not cls._configured:
            if not cls.configure():
                return False
        
        try:
            result = cloudinary.uploader.destroy(
                public_id, 
                resource_type=resource_type
            )
            return result.get('result') == 'ok'
        except Exception as e:
            print(f"[error] Error eliminando archivo de Cloudinary: {e}")
            return False
    
    @classmethod
    def get_file_info(cls, public_id):
        """
        Obtiene información de un archivo en Cloudinary
        
        Args:
            public_id (str): ID público del archivo
        
        Returns:
            dict | None: Información del archivo o None si no existe
        """
        if not cls._configured:
            if not cls.configure():
                return None
        
        try:
            return cloudinary.api.resource(public_id)
        except Exception as e:
            print(f"[error] Error obteniendo info del archivo: {e}")
            return None
    
    @classmethod
    def list_files(cls, folder='chat_uploads', max_results=100):
        """
        Lista archivos en una carpeta de Cloudinary
        
        Args:
            folder (str): Carpeta a listar
            max_results (int): Máximo de resultados
        
        Returns:
            list: Lista de archivos
        """
        if not cls._configured:
            if not cls.configure():
                return []
        
        try:
            result = cloudinary.api.resources(
                type='upload',
                prefix=folder,
                max_results=max_results
            )
            return result.get('resources', [])
        except Exception as e:
            print(f"[error] Error listando archivos: {e}")
            return []
    
    @classmethod
    def generate_thumbnail_url(cls, public_id, width=200, height=200):
        """
        Genera URL de thumbnail para una imagen
        
        Args:
            public_id (str): ID público de la imagen
            width (int): Ancho del thumbnail
            height (int): Alto del thumbnail
        
        Returns:
            str: URL del thumbnail
        
        Ejemplo:
            thumb_url = CloudinaryService.generate_thumbnail_url(
                'chat_uploads/user/image123',
                width=150,
                height=150
            )
        """
        if not cls._configured:
            if not cls.configure():
                return None
        
        return cloudinary.CloudinaryImage(public_id).build_url(
            width=width,
            height=height,
            crop='fill',
            quality='auto',
            fetch_format='auto'
        )
    
    @classmethod
    def validate_file_size(cls, file, max_mb=10):
        """
        Valida el tamaño de un archivo antes de subirlo
        
        Args:
            file: Archivo a validar
            max_mb (int): Tamaño máximo en MB
        
        Returns:
            tuple: (bool, str) - (es_válido, mensaje_error)
        
        Ejemplo:
            valid, error = CloudinaryService.validate_file_size(file, max_mb=5)
            if not valid:
                return jsonify({"error": error}), 400
        """
        try:
            # Intentar obtener el tamaño del archivo
            file.seek(0, 2)  # Ir al final del archivo
            size_bytes = file.tell()
            file.seek(0)  # Volver al inicio
            
            max_bytes = max_mb * 1024 * 1024
            
            if size_bytes > max_bytes:
                return False, f"Archivo excede el límite de {max_mb} MB"
            
            return True, None
            
        except Exception as e:
            return False, f"Error validando archivo: {str(e)}"
    
    @classmethod
    def validate_file_type(cls, filename, allowed_extensions=None):
        """
        Valida la extensión de un archivo
        
        Args:
            filename (str): Nombre del archivo
            allowed_extensions (set): Extensiones permitidas
                Default: imágenes, videos, PDFs, documentos
        
        Returns:
            tuple: (bool, str) - (es_válido, mensaje_error)
        
        Ejemplo:
            valid, error = CloudinaryService.validate_file_type(
                'documento.pdf',
                allowed_extensions={'pdf', 'doc', 'docx'}
            )
        """
        if allowed_extensions is None:
            # Extensiones por defecto
            allowed_extensions = {
                'jpg', 'jpeg', 'png', 'gif', 'webp',  # Imágenes
                'mp4', 'mov', 'avi',                   # Videos
                'pdf', 'doc', 'docx',                  # Documentos
                'txt', 'csv', 'xlsx'                   # Archivos de texto/datos
            }
        
        if '.' not in filename:
            return False, "Archivo sin extensión"
        
        extension = filename.rsplit('.', 1)[1].lower()
        
        if extension not in allowed_extensions:
            return False, f"Tipo de archivo no permitido: .{extension}"
        
        return True, None