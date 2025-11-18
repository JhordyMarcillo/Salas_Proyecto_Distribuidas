# app/services/security_service.py
"""
Servicio de Seguridad
Valida encriptación, detecta esteganografía y analiza seguridad de archivos
"""

import re
import hashlib
import math
from typing import Tuple, Dict, List


class SecurityService:
    """
    Servicio para validación de seguridad de mensajes y archivos
    Detecta encriptación, esteganografía y contenido potencialmente malicioso
    """
    
    # Patrones de encriptación común
    ENCRYPTION_PATTERNS = {
        'base64': r'^[A-Za-z0-9+/]*={0,2}$',
        'hex': r'^[0-9a-fA-F]+$',
        'ascii_armor': r'-----BEGIN.*-----',
        'pgp_key': r'-----BEGIN PGP.*KEY.*-----',
        'openssl': r'-----BEGIN.*ENCRYPTED.*-----',
    }
    
    # Extensiones comúnmente usadas en esteganografía
    STEGANOGRAPHY_EXTENSIONS = {
        'png', 'jpg', 'jpeg', 'bmp', 'gif',  # Imágenes (contienen datos ocultos)
        'wav', 'mp3', 'flac',                 # Audio (esteganografía de audio)
        'mp4', 'avi', 'mov'                   # Video (esteganografía de video)
    }
    
    # Extensiones sospechosas para esteganografía
    OPENSTEGO_INDICATORS = {
        '.png', '.bmp', '.wav'  # Formatos típicos de OpenStego
    }
    
    @classmethod
    def detect_encryption_in_text(cls, text: str) -> Dict[str, any]:
        """
        Detecta patrones de encriptación en texto
        
        Args:
            text (str): Texto a analizar
        
        Returns:
            dict: {
                'is_encrypted': bool,
                'encryption_types': list,
                'confidence': float (0-1),
                'details': str
            }
        
        Ejemplo:
            result = SecurityService.detect_encryption_in_text(message)
            if result['is_encrypted']:
                print(f"Posible encriptación: {result['encryption_types']}")
        """
        if not text or len(text) < 8:
            return {
                'is_encrypted': False,
                'encryption_types': [],
                'confidence': 0.0,
                'details': 'Texto muy corto para análisis'
            }
        
        detected_types = []
        scores = []
        
        # 1. Detectar Base64
        if cls._is_likely_base64(text):
            detected_types.append('base64')
            scores.append(0.7)
        
        # 2. Detectar Hex (encriptación hexadecimal)
        if cls._is_likely_hex(text):
            detected_types.append('hexadecimal')
            scores.append(0.6)
        
        # 3. Detectar PGP/GPG
        if 'BEGIN PGP' in text or 'BEGIN ENCRYPTED' in text:
            detected_types.append('pgp_encrypted')
            scores.append(0.95)
        
        # 4. Detectar OpenSSL
        if 'BEGIN ENCRYPTED' in text or 'BEGIN CERTIFICATE' in text:
            detected_types.append('openssl_encrypted')
            scores.append(0.9)
        
        # 5. Analizar entropía (medida de aleatoriedad)
        entropy = cls._calculate_entropy(text)
        if entropy > 6.0:  # Alta entropía = probablemente encriptado
            detected_types.append('high_entropy')
            scores.append(0.65)
        
        # Calcular confianza promedio
        confidence = sum(scores) / len(scores) if scores else 0.0
        
        return {
            'is_encrypted': confidence > 0.5,
            'encryption_types': detected_types,
            'confidence': round(confidence, 2),
            'entropy': round(entropy, 2),
            'details': f"Se detectaron {len(detected_types)} indicadores de encriptación"
        }
    
    @classmethod
    def check_file_steganography(cls, filename: str, file_data: bytes = None) -> Dict[str, any]:
        """
        Verifica si un archivo podría contener esteganografía
        
        Args:
            filename (str): Nombre del archivo
            file_data (bytes): Datos del archivo (opcional, para análisis profundo)
        
        Returns:
            dict: {
                'has_steganography_risk': bool,
                'file_type': str,
                'risk_level': str (low, medium, high),
                'openstego_indicators': list,
                'analysis': str,
                'recommendations': list
            }
        
        Ejemplo:
            result = SecurityService.check_file_steganography('image.png')
            if result['risk_level'] == 'high':
                print("Archivo con riesgo de esteganografía")
        """
        if not filename:
            return {
                'has_steganography_risk': False,
                'risk_level': 'unknown',
                'analysis': 'Nombre de archivo vacío'
            }
        
        # Obtener extensión
        extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        result = {
            'filename': filename,
            'extension': extension,
            'has_steganography_risk': False,
            'risk_level': 'low',
            'openstego_indicators': [],
            'recommendations': []
        }
        
        # 1. Verificar si es extensión típica de esteganografía
        if extension in cls.STEGANOGRAPHY_EXTENSIONS:
            result['has_steganography_risk'] = True
            result['openstego_indicators'].append(
                f"Extensión '{extension}' es típica para esteganografía"
            )
            result['risk_level'] = 'medium'
        
        # 2. Verificar extensiones OpenStego comunes
        if f'.{extension}' in cls.OPENSTEGO_INDICATORS:
            result['openstego_indicators'].append(
                f"Extensión '{extension}' es indicador de OpenStego"
            )
            # Solo marcar como high risk si hay otros indicadores sospechosos
            # Los archivos normales PNG/BMP/WAV no deberían ser rechazados
            # result['risk_level'] = 'high'  # Comentado: demasiado restrictivo
        
        # 3. Análisis de datos si se proporciona
        if file_data:
            # Verificar magic numbers (firmas de archivo)
            magic = cls._check_file_magic(file_data[:8])
            result['file_signature'] = magic
            
            # Analizar entropía del archivo
            file_entropy = cls._calculate_entropy(file_data.decode('latin-1'))
            result['file_entropy'] = round(file_entropy, 2)
            
            # Detectar anomalías
            if cls._has_suspicious_metadata(file_data):
                result['openstego_indicators'].append(
                    "Metadatos sospechosos detectados"
                )
                result['risk_level'] = 'high'
        
        # Recomendaciones
        if result['has_steganography_risk']:
            result['recommendations'].append(
                "Archivo con potencial para contener datos esteganografados"
            )
            result['recommendations'].append(
                "Se recomienda escaneo adicional si se sospecha de contenido malicioso"
            )
        
        result['analysis'] = f"Riesgo de esteganografía: {result['risk_level']}"
        
        return result
    
    @classmethod
    def validate_message_security(cls, message_text: str, file_info: Dict = None) -> Dict[str, any]:
        """
        Validación completa de seguridad de un mensaje
        
        Args:
            message_text (str): Contenido del mensaje
            file_info (dict): Información del archivo adjunto (opcional)
        
        Returns:
            dict: {
                'is_safe': bool,
                'security_flags': {
                    'has_encryption': bool,
                    'has_steganography_risk': bool,
                    'has_malicious_patterns': bool,
                    'has_suspicious_content': bool
                },
                'risk_level': str (low, medium, high),
                'issues': list,
                'recommendations': list
            }
        """
        issues = []
        flags = {
            'has_encryption': False,
            'has_steganography_risk': False,
            'has_malicious_patterns': False,
            'has_suspicious_content': False
        }
        
        # 1. Verificar encriptación en texto
        if message_text:
            encryption_check = cls.detect_encryption_in_text(message_text)
            if encryption_check['is_encrypted']:
                flags['has_encryption'] = True
                issues.append(
                    f"Posible encriptación detectada: {encryption_check['encryption_types']}"
                )
        
        # 2. Verificar archivo
        recommendations = []
        if file_info:
            stego_check = cls.check_file_steganography(
                file_info.get('filename', ''),
                file_info.get('data')
            )
            if stego_check['has_steganography_risk']:
                flags['has_steganography_risk'] = True
                issues.append(
                    f"Riesgo de esteganografía: {stego_check['risk_level']}"
                )
            recommendations.extend(stego_check.get('recommendations', []))
        
        # 3. Detectar patrones maliciosos
        if cls._has_malicious_patterns(message_text):
            flags['has_malicious_patterns'] = True
            issues.append("Patrones potencialmente maliciosos detectados")
        
        # Determinar nivel de riesgo
        risk_level = 'low'
        if any(flags.values()):
            if flags['has_encryption'] and flags['has_steganography_risk']:
                risk_level = 'high'
            elif flags['has_malicious_patterns']:
                risk_level = 'high'
            else:
                risk_level = 'medium'
        
        is_safe = risk_level == 'low'
        
        return {
            'is_safe': is_safe,
            'security_flags': flags,
            'risk_level': risk_level,
            'issues': issues,
            'recommendations': recommendations
        }
    
    @classmethod
    def _is_likely_base64(cls, text: str, min_length: int = 12) -> bool:
        """
        Verifica si el texto parece ser Base64
        
        Args:
            text (str): Texto a verificar
            min_length (int): Longitud mínima para considerarlo Base64
        
        Returns:
            bool: True si parece Base64
        """
        if len(text) < min_length:
            return False
        
        # Remover espacios y saltos de línea
        cleaned = text.replace(' ', '').replace('\n', '').replace('\r', '')
        
        # Verificar patrón Base64
        if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', cleaned):
            return False
        
        # Verificar que es múltiplo de 4 (caracteres de relleno)
        if len(cleaned) % 4 != 0:
            return False
        
        return True
    
    @classmethod
    def _is_likely_hex(cls, text: str, min_length: int = 20) -> bool:
        """
        Verifica si el texto parece ser hexadecimal
        
        Args:
            text (str): Texto a verificar
            min_length (int): Longitud mínima
        
        Returns:
            bool: True si parece hexadecimal
        """
        if len(text) < min_length:
            return False
        
        # Remover espacios
        cleaned = text.replace(' ', '').replace(':', '').replace('-', '')
        
        # Verificar que son solo caracteres hexadecimales
        if not re.match(r'^[0-9a-fA-F]+$', cleaned):
            return False
        
        # Debe ser par (2 caracteres por byte)
        if len(cleaned) % 2 != 0:
            return False
        
        return True
    
    @classmethod
    def _calculate_entropy(cls, data: str) -> float:
        """
        Calcula la entropía de Shannon de datos
        Alta entropía = datos probablemente encriptados o comprimidos
        
        Args:
            data (str): Datos a analizar
        
        Returns:
            float: Valor de entropía (0-8)
        """
        if not data:
            return 0.0
        
        # Contar frecuencia de cada byte
        byte_counts = {}
        for byte in data:
            byte_counts[byte] = byte_counts.get(byte, 0) + 1
        
        # Calcular entropía de Shannon
        entropy = 0.0
        data_length = len(data)
        
        for count in byte_counts.values():
            probability = count / data_length
            entropy -= probability * math.log2(probability)
        
        return entropy
    
    @classmethod
    def _check_file_magic(cls, file_header: bytes) -> str:
        """
        Identifica tipo de archivo por su firma (magic number)
        
        Args:
            file_header (bytes): Primeros 8 bytes del archivo
        
        Returns:
            str: Tipo de archivo detectado
        """
        magic_signatures = {
            b'\x89PNG': 'PNG Image',
            b'\xFF\xD8\xFF': 'JPEG Image',
            b'BM': 'BMP Image',
            b'GIF87a': 'GIF Image',
            b'GIF89a': 'GIF Image',
            b'Rar!': 'RAR Archive',
            b'PK\x03\x04': 'ZIP Archive',
            b'\x7fELF': 'ELF Executable',
            b'MZ': 'PE Executable',
            b'\xFF\xFB': 'MP3 Audio',
            b'ID3': 'MP3 Audio',
            b'RIFF': 'WAVE/AVI',
        }
        
        for signature, file_type in magic_signatures.items():
            if file_header.startswith(signature):
                return file_type
        
        return 'Unknown'
    
    @classmethod
    def _has_suspicious_metadata(cls, file_data: bytes) -> bool:
        """
        Detecta metadatos sospechosos en archivos
        
        Args:
            file_data (bytes): Datos del archivo
        
        Returns:
            bool: True si contiene metadatos sospechosos
        """
        try:
            # Convertir a string para búsqueda
            file_str = file_data.decode('latin-1')
            
            # Buscar patrones de metadatos sospechosos
            suspicious_patterns = [
                'hidden',
                'encrypted',
                'steganography',
                'secret',
                'obfuscated',
                'exif',
                'xmp'
            ]
            
            for pattern in suspicious_patterns:
                if pattern.lower() in file_str.lower():
                    return True
            
            return False
        except:
            return False
    
    @classmethod
    def _has_malicious_patterns(cls, text: str) -> bool:
        """
        Detecta patrones potencialmente maliciosos en texto
        
        Args:
            text (str): Texto a verificar
        
        Returns:
            bool: True si contiene patrones maliciosos
        """
        if not text:
            return False
        
        # Patrones maliciosos comunes
        malicious_patterns = [
            r'<script[^>]*>',  # JavaScript inline
            r'javascript:',     # Protocolo javascript
            r'eval\s*\(',       # Funciones eval
            r'exec\s*\(',       # Funciones exec
            r'__import__',      # Importación dinámica Python
            r'os\.system',      # Comandos del sistema
            r'subprocess\.',    # Procesos en Python
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def get_security_summary(cls, 
                            message_text: str = None, 
                            file_info: Dict = None) -> Dict[str, any]:
        """
        Genera un resumen de seguridad completo
        
        Args:
            message_text (str): Contenido del mensaje
            file_info (dict): Información del archivo
        
        Returns:
            dict: Resumen completo de seguridad
        """
        security_check = cls.validate_message_security(message_text, file_info)
        
        return {
            'message_security': security_check,
            'timestamp': cls._get_timestamp(),
            'summary': {
                'total_issues': len(security_check['issues']),
                'requires_review': not security_check['is_safe'],
                'risk_level': security_check['risk_level']
            }
        }
    
    @classmethod
    def _get_timestamp(cls) -> str:
        """Obtiene timestamp actual en ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'
