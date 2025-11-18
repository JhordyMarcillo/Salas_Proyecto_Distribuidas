"""
Tests para rutas de upload de archivos
Prueba subida, validación y seguridad de archivos
"""

import pytest
import json
import io
from unittest.mock import patch, MagicMock
from app import create_app
from app.utils.database import mongo


@pytest.fixture
def app():
    """Crea una app con configuración de testing"""
    app = create_app('testing')
    
    with app.app_context():
        # Limpiar la base de datos antes de cada test
        mongo.db.users.delete_many({})
        mongo.db.rooms.delete_many({})
        mongo.db.messages.delete_many({})
        
        yield app
        
        # Limpiar después de cada test
        mongo.db.users.delete_many({})
        mongo.db.rooms.delete_many({})
        mongo.db.messages.delete_many({})


@pytest.fixture
def client(app):
    """Cliente para hacer requests HTTP"""
    return app.test_client()


@pytest.fixture
def auth_token(client, app):
    """Token de autenticación para tests"""
    response = client.post('/auth/register', json={
        'username': 'testuser',
        'password': 'password123'
    })
    
    data = json.loads(response.data)
    return data['token']


class TestUploadValidation:
    """Tests para validación de archivos antes de upload"""
    
    def test_validate_pdf_file(self, client, auth_token):
        """Valida archivo PDF exitosamente"""
        response = client.post(
            '/upload/validate',
            headers={'Authorization': f'Bearer {auth_token}'},
            json={
                'filename': 'documento.pdf',
                'size_bytes': 1048576  # 1MB
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['valid'] == True
        assert len(data['errors']) == 0
    
    def test_validate_invalid_extension(self, client, auth_token):
        """Rechaza archivo con extensión no permitida"""
        response = client.post(
            '/upload/validate',
            headers={'Authorization': f'Bearer {auth_token}'},
            json={
                'filename': 'programa.exe',
                'size_bytes': 1048576
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['valid'] == False
        assert len(data['errors']) > 0
    
    def test_validate_file_too_large(self, client, auth_token):
        """Rechaza archivo que excede tamaño máximo"""
        response = client.post(
            '/upload/validate',
            headers={'Authorization': f'Bearer {auth_token}'},
            json={
                'filename': 'archivo_grande.pdf',
                'size_bytes': 15728640  # 15MB (más que el máximo)
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['valid'] == False
        assert any('excede' in error.lower() for error in data['errors'])
    
    def test_validate_missing_filename(self, client, auth_token):
        """Retorna error si falta filename"""
        response = client.post(
            '/upload/validate',
            headers={'Authorization': f'Bearer {auth_token}'},
            json={
                'size_bytes': 1048576
            }
        )
        
        assert response.status_code == 400
    
    def test_validate_missing_size(self, client, auth_token):
        """Retorna error si falta size_bytes"""
        response = client.post(
            '/upload/validate',
            headers={'Authorization': f'Bearer {auth_token}'},
            json={
                'filename': 'documento.pdf'
            }
        )
        
        assert response.status_code == 400
    
    def test_validate_requires_auth(self, client):
        """Requiere autenticación"""
        response = client.post(
            '/upload/validate',
            json={
                'filename': 'documento.pdf',
                'size_bytes': 1048576
            }
        )
        
        assert response.status_code == 401


class TestUploadSecurity:
    """Tests para validación de seguridad de archivos"""
    
    def test_reject_high_risk_steganography(self, client, auth_token):
        """Rechaza archivo con alto riesgo de esteganografía"""
        # Crear un archivo PNG mock
        file_data = b'PNG mock data'
        file = (io.BytesIO(file_data), 'image.png')
        
        with patch('app.services.SecurityService.check_file_steganography') as mock_security:
            mock_security.return_value = {
                'risk_level': 'high',
                'has_steganography_risk': True,
                'openstego_indicators': ['OpenStego signature detected']
            }
            
            with patch('app.services.CloudinaryService.is_configured', return_value=True):
                response = client.post(
                    '/upload',
                    headers={'Authorization': f'Bearer {auth_token}'},
                    data={'file': file}
                )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'rechazado' in data['error'].lower()
        assert data['risk_level'] == 'high'
    
    def test_allow_medium_risk_with_warning(self, client, auth_token):
        """Permite archivo con riesgo medio (con advertencia)"""
        file_data = b'PNG image data'
        file = (io.BytesIO(file_data), 'image.png')
        
        with patch('app.services.SecurityService.check_file_steganography') as mock_security:
            mock_security.return_value = {
                'risk_level': 'medium',
                'has_steganography_risk': True,
                'openstego_indicators': ['PNG format used in steganography']
            }
            
            with patch('app.services.CloudinaryService.is_configured', return_value=True):
                with patch('app.services.CloudinaryService.validate_file_type', return_value=(True, None)):
                    with patch('app.services.CloudinaryService.validate_file_size', return_value=(True, None)):
                        with patch('app.services.CloudinaryService.upload_file') as mock_upload:
                            mock_upload.return_value = {
                                'url': 'https://example.com/image.png',
                                'filename': 'image.png',
                                'public_id': 'chat_uploads/testuser/abc123',
                                'format': 'png',
                                'bytes': 1024,
                                'resource_type': 'image'
                            }
                            
                            response = client.post(
                                '/upload',
                                headers={'Authorization': f'Bearer {auth_token}'},
                                data={'file': file}
                            )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'security_check' in data
        assert data['security_check']['risk_level'] == 'medium'
    
    def test_allow_low_risk_file(self, client, auth_token):
        """Permite archivo con bajo riesgo"""
        file_data = b'PDF document data'
        file = (io.BytesIO(file_data), 'documento.pdf')
        
        with patch('app.services.SecurityService.check_file_steganography') as mock_security:
            mock_security.return_value = {
                'risk_level': 'low',
                'has_steganography_risk': False,
                'openstego_indicators': []
            }
            
            with patch('app.services.CloudinaryService.is_configured', return_value=True):
                with patch('app.services.CloudinaryService.validate_file_type', return_value=(True, None)):
                    with patch('app.services.CloudinaryService.validate_file_size', return_value=(True, None)):
                        with patch('app.services.CloudinaryService.upload_file') as mock_upload:
                            mock_upload.return_value = {
                                'url': 'https://example.com/documento.pdf',
                                'filename': 'documento.pdf',
                                'public_id': 'chat_uploads/testuser/pdf123',
                                'format': 'pdf',
                                'bytes': 2048,
                                'resource_type': 'raw'
                            }
                            
                            response = client.post(
                                '/upload',
                                headers={'Authorization': f'Bearer {auth_token}'},
                                data={'file': file}
                            )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['security_check']['risk_level'] == 'low'


class TestUploadErrors:
    """Tests para manejo de errores en upload"""
    
    def test_upload_no_file_in_request(self, client, auth_token):
        """Retorna error si no hay archivo en request"""
        response = client.post(
            '/upload',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'no se encontró' in data['error'].lower()
    
    def test_upload_empty_filename(self, client, auth_token):
        """Retorna error si el filename está vacío"""
        file = (io.BytesIO(b''), '')
        
        response = client.post(
            '/upload',
            headers={'Authorization': f'Bearer {auth_token}'},
            data={'file': file}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'no se seleccionó' in data['error'].lower()
    
    def test_upload_cloudinary_not_configured(self, client, auth_token):
        """Retorna error si Cloudinary no está configurado"""
        file = (io.BytesIO(b'test'), 'test.pdf')
        
        with patch('app.services.CloudinaryService.is_configured', return_value=False):
            with patch('app.services.CloudinaryService.configure', return_value=False):
                response = client.post(
                    '/upload',
                    headers={'Authorization': f'Bearer {auth_token}'},
                    data={'file': file}
                )
        
        assert response.status_code == 503
    
    def test_upload_requires_auth(self, client):
        """Requiere autenticación"""
        file = (io.BytesIO(b'test'), 'test.pdf')
        
        response = client.post(
            '/upload',
            data={'file': file}
        )
        
        assert response.status_code == 401


class TestDeleteFile:
    """Tests para eliminación de archivos"""
    
    def test_delete_own_file(self, client, auth_token):
        """Usuario puede eliminar su propio archivo"""
        with patch('app.services.CloudinaryService.delete_file', return_value=True):
            response = client.post(
                '/upload/delete',
                headers={'Authorization': f'Bearer {auth_token}'},
                json={'public_id': 'chat_uploads/testuser/abc123'}
            )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'eliminado' in data['msg'].lower()
    
    def test_delete_other_user_file_fails(self, client, auth_token):
        """Usuario no puede eliminar archivo de otro usuario"""
        response = client.post(
            '/upload/delete',
            headers={'Authorization': f'Bearer {auth_token}'},
            json={'public_id': 'chat_uploads/otherusername/abc123'}
        )
        
        assert response.status_code == 403
    
    def test_delete_missing_public_id(self, client, auth_token):
        """Retorna error si falta public_id"""
        response = client.post(
            '/upload/delete',
            headers={'Authorization': f'Bearer {auth_token}'},
            json={}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'public_id' in data['error'].lower()
    
    def test_delete_requires_auth(self, client):
        """Requiere autenticación"""
        response = client.post(
            '/upload/delete',
            json={'public_id': 'chat_uploads/testuser/abc123'}
        )
        
        assert response.status_code == 401


class TestThumbnail:
    """Tests para generación de thumbnails"""
    
    def test_generate_thumbnail(self, client, auth_token):
        """Genera thumbnail de imagen"""
        with patch('app.services.CloudinaryService.generate_thumbnail_url') as mock_thumb:
            mock_thumb.return_value = 'https://example.com/image_thumb.jpg'
            
            response = client.post(
                '/upload/thumbnail',
                headers={'Authorization': f'Bearer {auth_token}'},
                json={
                    'public_id': 'chat_uploads/testuser/image123',
                    'width': 200,
                    'height': 200
                }
            )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'thumbnail_url' in data
    
    def test_thumbnail_with_custom_dimensions(self, client, auth_token):
        """Genera thumbnail con dimensiones personalizadas"""
        with patch('app.services.CloudinaryService.generate_thumbnail_url') as mock_thumb:
            mock_thumb.return_value = 'https://example.com/image_custom.jpg'
            
            response = client.post(
                '/upload/thumbnail',
                headers={'Authorization': f'Bearer {auth_token}'},
                json={
                    'public_id': 'chat_uploads/testuser/image123',
                    'width': 150,
                    'height': 150
                }
            )
        
        assert response.status_code == 200
        # Verificar que se llamó con los parámetros correctos
        mock_thumb.assert_called_once()
        call_kwargs = mock_thumb.call_args[1]
        assert call_kwargs['width'] == 150
        assert call_kwargs['height'] == 150
    
    def test_thumbnail_missing_public_id(self, client, auth_token):
        """Retorna error si falta public_id"""
        response = client.post(
            '/upload/thumbnail',
            headers={'Authorization': f'Bearer {auth_token}'},
            json={'width': 200}
        )
        
        assert response.status_code == 400
    
    def test_thumbnail_requires_auth(self, client):
        """Requiere autenticación"""
        response = client.post(
            '/upload/thumbnail',
            json={'public_id': 'chat_uploads/testuser/image123'}
        )
        
        assert response.status_code == 401


class TestListFiles:
    """Tests para listar archivos del usuario"""
    
    def test_list_user_files(self, client, auth_token):
        """Lista archivos del usuario"""
        mock_files = [
            {
                'public_id': 'chat_uploads/testuser/file1',
                'url': 'https://example.com/file1.pdf',
                'format': 'pdf',
                'bytes': 1024
            },
            {
                'public_id': 'chat_uploads/testuser/file2',
                'url': 'https://example.com/file2.jpg',
                'format': 'jpg',
                'bytes': 2048
            }
        ]
        
        with patch('app.services.CloudinaryService.list_files', return_value=mock_files):
            response = client.get(
                '/upload/list',
                headers={'Authorization': f'Bearer {auth_token}'}
            )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['files']) == 2
        assert data['total'] == 2
    
    def test_list_files_empty(self, client, auth_token):
        """Retorna lista vacía si no hay archivos"""
        with patch('app.services.CloudinaryService.list_files', return_value=[]):
            response = client.get(
                '/upload/list',
                headers={'Authorization': f'Bearer {auth_token}'}
            )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['files'] == []
        assert data['total'] == 0
    
    def test_list_files_with_limit(self, client, auth_token):
        """Respeta parámetro limit"""
        with patch('app.services.CloudinaryService.list_files') as mock_list:
            mock_list.return_value = []
            
            response = client.get(
                '/upload/list?limit=10',
                headers={'Authorization': f'Bearer {auth_token}'}
            )
        
        assert response.status_code == 200
        # Verificar que se llamó con limit=10
        mock_list.assert_called_once()
        call_args = mock_list.call_args
        assert call_args[1]['max_results'] == 10
    
    def test_list_files_requires_auth(self, client):
        """Requiere autenticación"""
        response = client.get('/upload/list')
        
        assert response.status_code == 401
