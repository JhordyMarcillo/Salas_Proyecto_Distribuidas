# 🔒 Documentación del Servicio de Seguridad

## Descripción General

El `SecurityService` es un módulo de seguridad que valida mensajes y archivos para detectar:

- **Encriptación** en texto de mensajes
- **Esteganografía** en archivos (especialmente OpenStego)
- **Patrones maliciosos** en contenido
- **Metadatos sospechosos** en archivos

---

## 📍 Ubicación

```
backend/app/services/security_service.py
```

---

## 🚀 Métodos Principales

### 1. `detect_encryption_in_text(text)`

Detecta patrones de encriptación en texto de mensajes.

**Parámetros:**
- `text` (str): Contenido del mensaje a analizar

**Retorna:**
```python
{
    'is_encrypted': bool,              # ¿Está encriptado?
    'encryption_types': list,          # Tipos detectados: ['base64', 'hex', 'pgp_encrypted', etc]
    'confidence': float,               # Confianza de 0.0 a 1.0
    'entropy': float,                  # Entropía de Shannon (0-8)
    'details': str                     # Descripción del análisis
}
```

**Ejemplo de uso:**
```python
from app.services import SecurityService

result = SecurityService.detect_encryption_in_text(message_content)
if result['is_encrypted']:
    print(f"⚠️ Encriptación detectada: {result['encryption_types']}")
    print(f"Confianza: {result['confidence']}")
```

**Patrones detectados:**
- ✅ Base64
- ✅ Hexadecimal
- ✅ PGP/GPG
- ✅ OpenSSL
- ✅ Alta entropía (datos aleatorios)

---

### 2. `check_file_steganography(filename, file_data=None)`

Verifica si un archivo podría contener esteganografía u OpenStego.

**Parámetros:**
- `filename` (str): Nombre del archivo
- `file_data` (bytes, opcional): Contenido del archivo para análisis profundo

**Retorna:**
```python
{
    'filename': str,                           # Nombre original
    'extension': str,                          # Extensión del archivo
    'has_steganography_risk': bool,            # ¿Tiene riesgo?
    'risk_level': str,                         # 'low', 'medium', 'high'
    'openstego_indicators': list,              # Indicadores encontrados
    'file_signature': str,                     # Tipo de archivo (PNG, JPEG, etc)
    'file_entropy': float,                     # Entropía del archivo
    'recommendations': list,                   # Recomendaciones de seguridad
    'analysis': str                            # Resumen del análisis
}
```

**Ejemplo de uso:**
```python
from app.services import SecurityService

result = SecurityService.check_file_steganography('image.png')
if result['risk_level'] == 'high':
    print(f"🚨 Riesgo ALTO detectado:")
    print(f"Indicadores: {result['openstego_indicators']}")
```

**Extensiones de alto riesgo:**
- `.png` - Formato típico OpenStego
- `.bmp` - Formato típico OpenStego
- `.wav` - Esteganografía de audio

**Niveles de riesgo:**
- **low**: Archivos de texto, documentos normales
- **medium**: Imágenes y videos (potencial para esteganografía)
- **high**: OpenStego indicators detectados

---

### 3. `validate_message_security(message_text, file_info=None)`

Validación **completa** de un mensaje (texto + archivo adjunto).

**Parámetros:**
- `message_text` (str): Contenido del mensaje
- `file_info` (dict, opcional): 
  ```python
  {
      'filename': str,
      'data': bytes  # Datos del archivo
  }
  ```

**Retorna:**
```python
{
    'is_safe': bool,                      # ¿Es seguro?
    'security_flags': {
        'has_encryption': bool,            # ¿Texto encriptado?
        'has_steganography_risk': bool,    # ¿Archivo con riesgo?
        'has_malicious_patterns': bool,    # ¿Patrones maliciosos?
        'has_suspicious_content': bool     # ¿Contenido sospechoso?
    },
    'risk_level': str,                    # 'low', 'medium', 'high'
    'issues': list,                       # Problemas detectados
    'recommendations': list               # Recomendaciones
}
```

**Ejemplo de uso:**
```python
from app.services import SecurityService

security = SecurityService.validate_message_security(
    message_text="Contenido del mensaje",
    file_info={
        'filename': 'archivo.png',
        'data': file_bytes
    }
)

if not security['is_safe']:
    print(f"⚠️ Riesgo: {security['risk_level']}")
    print(f"Problemas: {security['issues']}")
    print(f"Recomendaciones: {security['recommendations']}")
```

---

### 4. `get_security_summary(message_text=None, file_info=None)`

Genera un resumen completo de seguridad con timestamp.

**Retorna:**
```python
{
    'message_security': {...},    # Resultado de validate_message_security
    'timestamp': str,              # ISO format timestamp
    'summary': {
        'total_issues': int,       # Cantidad de problemas
        'requires_review': bool,   # ¿Necesita revisión manual?
        'risk_level': str          # 'low', 'medium', 'high'
    }
}
```

---

## 🔧 Integración en Routes

### En `routes/upload.py`

```python
from app.services import SecurityService, CloudinaryService

@upload_bp.route('', methods=['POST'])
@require_jwt_http
def upload_file(username):
    # ... código previo ...
    
    # Leer datos del archivo
    file_to_upload.seek(0)
    file_data = file_to_upload.read()
    file_to_upload.seek(0)
    
    # Validar seguridad
    security_check = SecurityService.check_file_steganography(
        file_to_upload.filename,
        file_data=file_data
    )
    
    # Rechazar si es alto riesgo
    if security_check['risk_level'] == 'high':
        return jsonify({
            'error': 'Archivo rechazado por riesgos de seguridad',
            'risk_level': security_check['risk_level'],
            'indicators': security_check['openstego_indicators']
        }), 403
    
    # Proceder con upload...
```

---

## 🔧 Integración en Sockets

### En `sockets/message_events.py`

```python
from app.services import SecurityService
from app.models import get_message_model

@socketio.on("message")
@require_token_socket
def handle_message(username, data):
    room = data.get('room')
    message_text = data.get('msg', '')
    file_info = data.get('file')  # Si hay archivo adjunto
    
    # Validar seguridad del mensaje completo
    security_check = SecurityService.validate_message_security(
        message_text, 
        file_info
    )
    
    # Guardar mensaje con información de seguridad
    message_model = get_message_model()
    message_model.create_message(
        room=room,
        username=username,
        msg=message_text,
        file_url=file_info.get('url') if file_info else None,
        original_filename=file_info.get('filename') if file_info else None,
        security_flags=security_check['security_flags']
    )
    
    # Emitir con advertencia si es necesario
    emit_data = {
        'username': username,
        'msg': message_text,
        'security_flags': security_check['security_flags']
    }
    
    if security_check['risk_level'] == 'high':
        emit_data['security_warning'] = True
        emit_data['security_issues'] = security_check['issues']
    
    emit("message", emit_data, room=room)
```

---

## 🛡️ Políticas de Seguridad

### Política Recomendada

| Tipo | Acción |
|------|--------|
| **Encriptación detectada** | ⚠️ Permitir con advertencia |
| **Riesgo esteganografía MEDIUM** | ⚠️ Permitir con advertencia |
| **Riesgo esteganografía HIGH** | 🚫 Rechazar |
| **Patrones maliciosos** | 🚫 Rechazar |
| **Entropía muy alta** | ⚠️ Permitir con advertencia |

---

## 📊 Indicadores OpenStego

El servicio detecta los siguientes indicadores de archivos OpenStego:

### Por Extensión
- `.png` - Formato PNG (muy usado en OpenStego)
- `.bmp` - Formato BMP (muy usado en OpenStego)
- `.wav` - Formato WAV (para audio)

### Por Contenido
- Metadatos sospechosos con palabras clave: "hidden", "encrypted", "steganography", "secret"
- Entropía anómala en secciones del archivo
- Firmas de archivo atípicas

---

## 🔍 Detección de Encriptación

El servicio analiza:

1. **Base64**: Patrón `[A-Za-z0-9+/]` con padding `=`
2. **Hexadecimal**: Solo dígitos 0-9 y A-F, longitud par
3. **PGP/GPG**: Headers `-----BEGIN PGP-----`
4. **OpenSSL**: Headers `-----BEGIN ENCRYPTED-----`
5. **Entropía de Shannon**: > 6.0 indica datos aleatorios/encriptados

---

## 🚨 Ejemplo Completo: Chat con Validación

```python
# En sockets/message_events.py

from app.services import SecurityService, CloudinaryService
from app.models import get_message_model

@socketio.on("send_message_with_file")
@require_token_socket
def handle_message_with_file(username, data):
    """
    Maneja mensajes con archivos adjuntos
    Valida seguridad antes de guardar
    """
    room = data.get('room')
    message_text = data.get('msg', '')
    file_url = data.get('file_url')
    filename = data.get('filename')
    
    # Si hay archivo, descargar para análisis
    file_data = None
    if file_url:
        try:
            import requests
            response = requests.get(file_url)
            file_data = response.content
        except:
            pass
    
    # Validación de seguridad COMPLETA
    security = SecurityService.validate_message_security(
        message_text,
        file_info={
            'filename': filename,
            'data': file_data
        } if filename else None
    )
    
    # Registrar en log
    if security['risk_level'] != 'low':
        print(f"[SECURITY] {username} en {room}")
        print(f"  Risk: {security['risk_level']}")
        print(f"  Issues: {security['issues']}")
    
    # RECHAZAR si es alto riesgo
    if security['risk_level'] == 'high':
        emit("error", {
            "msg": "Mensaje rechazado por riesgos de seguridad",
            "risk_level": security['risk_level'],
            "issues": security['issues']
        })
        return
    
    # GUARDAR en base de datos
    message_model = get_message_model()
    message_model.create_message(
        room=room,
        username=username,
        msg=message_text,
        file_url=file_url,
        original_filename=filename,
        security_flags=security['security_flags']
    )
    
    # ENVIAR a sala (con advertencia si es necesario)
    response = {
        'username': username,
        'msg': message_text,
        'file_url': file_url,
        'filename': filename,
        'security_flags': security['security_flags']
    }
    
    # Si hay advertencia, incluir
    if security['risk_level'] == 'medium':
        response['security_warning'] = True
        response['security_issues'] = security['issues']
    
    emit("message", response, room=room)
```

---

## 📝 Logs y Debugging

Para ver qué detecta el servicio:

```python
from app.services import SecurityService

# Test de encriptación
msg = "SGVsbG8gV29ybGQ="  # "Hello World" en Base64
result = SecurityService.detect_encryption_in_text(msg)
print(f"Encriptación: {result}")

# Test de archivo
result = SecurityService.check_file_steganography("image.png")
print(f"Esteganografía: {result}")

# Test completo
security = SecurityService.validate_message_security(
    message_text="Test message",
    file_info={'filename': 'image.png', 'data': b'...'}
)
print(f"Seguridad: {security}")
```

---

## ⚙️ Configuración Futura

Se pueden añadir:

- Integración con VirusTotal API
- Análisis MIME type avanzado
- Detección de malware con ClamAV
- Análisis de patrones de red sospechosos
- Machine Learning para detección de anomalías

---

## 📞 Soporte

Para dudas o mejoras al servicio de seguridad, revisa:

1. `backend/app/services/security_service.py` - Código fuente
2. `backend/DOCUMENTACION_SEGURIDAD.md` - Esta documentación
3. Tests en `backend/tests/` - Ejemplos de uso
