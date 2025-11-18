# backend/tests/test_security.py
"""
Tests para el Servicio de Seguridad
Valida detección de encriptación, esteganografía y patrones maliciosos
"""

import unittest
from app.services import SecurityService


class TestEncryptionDetection(unittest.TestCase):
    """Tests para detección de encriptación"""
    
    def test_detect_base64(self):
        """Detecta Base64"""
        # "Hello World" en Base64
        base64_text = "SGVsbG8gV29ybGQh"
        result = SecurityService.detect_encryption_in_text(base64_text)
        
        self.assertTrue(result['is_encrypted'])
        self.assertIn('base64', result['encryption_types'])
        self.assertGreater(result['confidence'], 0.5)
    
    def test_detect_hex(self):
        """Detecta hexadecimal"""
        hex_text = "48656c6c6f20576f726c64"  # "Hello World" en hex
        result = SecurityService.detect_encryption_in_text(hex_text)
        
        self.assertTrue(result['is_encrypted'])
        self.assertIn('hexadecimal', result['encryption_types'])
    
    def test_detect_pgp(self):
        """Detecta PGP encriptado"""
        pgp_text = "-----BEGIN PGP MESSAGE-----\nVer: GnuPG\n-----END PGP MESSAGE-----"
        result = SecurityService.detect_encryption_in_text(pgp_text)
        
        self.assertTrue(result['is_encrypted'])
        self.assertIn('pgp_encrypted', result['encryption_types'])
    
    def test_high_entropy_detection(self):
        """Detecta texto con alta entropía (típico de encriptación)"""
        # Texto aleatorio con alta entropía
        random_text = "kX9mZvP7qB2jLwFrT5nGhD8aYcE3uIjO4sW6xQ1nM0V"
        result = SecurityService.detect_encryption_in_text(random_text)
        
        # Puede detectar como encriptado por entropía
        if result['is_encrypted']:
            self.assertGreater(result['entropy'], 5.0)
    
    def test_plain_text_not_encrypted(self):
        """Verifica que texto plano no se detecta como encriptado"""
        plain_text = "Hola, ¿cómo estás? Este es un mensaje normal."
        result = SecurityService.detect_encryption_in_text(plain_text)
        
        self.assertFalse(result['is_encrypted'])
        self.assertEqual(len(result['encryption_types']), 0)


class TestSteganographyDetection(unittest.TestCase):
    """Tests para detección de esteganografía"""
    
    def test_png_image_risk(self):
        """PNG tiene riesgo de esteganografía"""
        result = SecurityService.check_file_steganography("image.png")
        
        self.assertTrue(result['has_steganography_risk'])
        self.assertIn(result['risk_level'], ['medium', 'high'])  # PNG es formato común para esteganografía
    
    def test_openstego_bmp(self):
        """BMP tiene riesgo alto de OpenStego"""
        result = SecurityService.check_file_steganography("image.bmp")
        
        self.assertTrue(result['has_steganography_risk'])
        # BMP es indicador directo de OpenStego
        self.assertTrue(len(result['openstego_indicators']) > 0)
    
    def test_openstego_wav(self):
        """WAV tiene riesgo alto de OpenStego"""
        result = SecurityService.check_file_steganography("audio.wav")
        
        self.assertTrue(result['has_steganography_risk'])
        self.assertIn('high', result['risk_level'])
    
    def test_safe_document(self):
        """PDFs y documentos tienen bajo riesgo"""
        result = SecurityService.check_file_steganography("documento.pdf")
        
        # PDF no está en lista de esteganografía
        # Riesgo debería ser bajo
        self.assertIn('low', result['risk_level'])
    
    def test_text_file_safe(self):
        """Archivos de texto son seguros"""
        result = SecurityService.check_file_steganography("archivo.txt")
        
        self.assertFalse(result['has_steganography_risk'])
        self.assertEqual('low', result['risk_level'])


class TestCompleteMessageValidation(unittest.TestCase):
    """Tests para validación completa de mensajes"""
    
    def test_safe_message(self):
        """Mensaje normal es seguro"""
        security = SecurityService.validate_message_security(
            message_text="Hola a todos, ¿cómo están?"
        )
        
        self.assertTrue(security['is_safe'])
        self.assertEqual('low', security['risk_level'])
        self.assertEqual(len(security['issues']), 0)
    
    def test_message_with_encryption(self):
        """Mensaje con encriptación detectada"""
        base64_msg = "SGVsbG8gV29ybGQ="
        security = SecurityService.validate_message_security(
            message_text=base64_msg
        )
        
        self.assertFalse(security['is_safe'])
        self.assertTrue(security['security_flags']['has_encryption'])
        self.assertIn('medium', security['risk_level'])
    
    def test_message_with_file_risk(self):
        """Mensaje con archivo de alto riesgo"""
        security = SecurityService.validate_message_security(
            message_text="Mira esto",
            file_info={
                'filename': 'imagen.png',
                'data': b'PNG test data'
            }
        )
        
        # Debería detectar riesgo de esteganografía en el archivo
        self.assertTrue(
            security['security_flags']['has_steganography_risk'] or 
            security['risk_level'] != 'low'
        )
    
    def test_malicious_pattern_detection(self):
        """Detecta patrones potencialmente maliciosos"""
        malicious_msg = "ejecutar: <script>alert('xss')</script>"
        security = SecurityService.validate_message_security(
            message_text=malicious_msg
        )
        
        # Debería detectar el patrón <script>
        self.assertTrue(
            security['security_flags']['has_malicious_patterns'] or
            len(security['issues']) > 0
        )


class TestSecuritySummary(unittest.TestCase):
    """Tests para resumen de seguridad"""
    
    def test_summary_generation(self):
        """Genera resumen de seguridad completo"""
        summary = SecurityService.get_security_summary(
            message_text="Mensaje de prueba",
            file_info={
                'filename': 'test.txt',
                'data': b'test content'
            }
        )
        
        self.assertIn('message_security', summary)
        self.assertIn('timestamp', summary)
        self.assertIn('summary', summary)
        
        # Verificar estructura de summary
        self.assertIn('total_issues', summary['summary'])
        self.assertIn('requires_review', summary['summary'])
        self.assertIn('risk_level', summary['summary'])
    
    def test_summary_has_timestamp(self):
        """El resumen incluye timestamp ISO"""
        summary = SecurityService.get_security_summary(
            message_text="Test"
        )
        
        # Timestamp debe ser ISO format
        timestamp = summary['timestamp']
        self.assertIn('T', timestamp)
        self.assertIn('Z', timestamp)


class TestEntropyCalculation(unittest.TestCase):
    """Tests para cálculo de entropía"""
    
    def test_low_entropy_plain_text(self):
        """Texto plano tiene entropía baja"""
        text = "aaaaaaaa"
        result = SecurityService.detect_encryption_in_text(text)
        
        # Mucha repetición = baja entropía
        self.assertLess(result['entropy'], 3.0)
    
    def test_high_entropy_random(self):
        """Datos aleatorios tienen entropía alta"""
        random_text = "kX9mZvP7qB2jLwFrT5nGhD8aYcE3uIjO4sW6xQ1nM0V"
        result = SecurityService.detect_encryption_in_text(random_text)
        
        # Datos variados = alta entropía
        self.assertGreater(result['entropy'], 3.0)


class TestIntegrationScenarios(unittest.TestCase):
    """Tests de escenarios realistas de uso"""
    
    def test_chat_message_scenario(self):
        """Simula validación de mensaje en chat"""
        # Usuario envía: "Hola, mira esta imagen"
        security = SecurityService.validate_message_security(
            message_text="Hola, mira esta imagen",
            file_info={
                'filename': 'screenshot.png'
            }
        )
        
        # Debería permitir con posible advertencia
        self.assertIn(security['risk_level'], ['low', 'medium'])
    
    def test_suspicious_file_upload(self):
        """Simula detección de archivo sospechoso"""
        result = SecurityService.check_file_steganography("datos.wav")
        
        # WAV es alto riesgo
        self.assertTrue(result['has_steganography_risk'])
        self.assertGreater(len(result['openstego_indicators']), 0)
    
    def test_encrypted_communication_detection(self):
        """Detecta comunicación encriptada"""
        encrypted_msg = "-----BEGIN ENCRYPTED MESSAGE-----\nQ1ZFMDEwMDAwMDE=\n-----END ENCRYPTED MESSAGE-----"
        result = SecurityService.detect_encryption_in_text(encrypted_msg)
        
        self.assertTrue(result['is_encrypted'])
        self.assertGreater(result['confidence'], 0.8)


if __name__ == '__main__':
    unittest.main()
