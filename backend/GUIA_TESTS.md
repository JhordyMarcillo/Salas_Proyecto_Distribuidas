# 🧪 Guía de Tests del Proyecto

## 📋 Índice
1. [Descripción general](#descripción-general)
2. [Requisitos](#requisitos)
3. [Estructura de tests](#estructura-de-tests)
4. [Cómo ejecutar tests](#cómo-ejecutar-tests)
5. [Tests por módulo](#tests-por-módulo)
6. [Cobertura](#cobertura)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Descripción General

El proyecto utiliza **pytest** para testing. Los tests cubren:
- ✅ Autenticación y JWT
- ✅ Gestión de salas
- ✅ Upload y validación de archivos
- ✅ Seguridad (encriptación, esteganografía)
- ✅ WebSocket eventos
- ✅ Manejo de errores

---

## 📦 Requisitos

Instalar pytest:
```bash
pip install pytest pytest-flask pytest-asyncio
```

En `requirements.txt`:
```
pytest>=7.0
pytest-flask>=1.2
pytest-asyncio>=0.20
```

---

## 📁 Estructura de Tests

```
backend/tests/
├── __init__.py                    # Configuración del paquete
├── test_auth.py                   # ✅ Tests de autenticación (291 líneas)
├── test_rooms.py                  # ✅ Tests de salas (NEW - 550 líneas)
├── test_upload.py                 # ✅ Tests de upload (NEW - 450 líneas)
├── test_security.py               # ✅ Tests de seguridad (NEW - 340 líneas)
└── test_sockets.py                # ✅ Tests de WebSocket (NEW - 500 líneas)

Total: ~2,131 líneas de tests
```

---

## 🚀 Cómo Ejecutar Tests

### Ejecutar todos los tests
```bash
cd backend/
pytest -v
```

### Ejecutar tests de un módulo específico
```bash
# Tests de autenticación
pytest tests/test_auth.py -v

# Tests de salas
pytest tests/test_rooms.py -v

# Tests de upload
pytest tests/test_upload.py -v

# Tests de seguridad
pytest tests/test_security.py -v

# Tests de WebSocket
pytest tests/test_sockets.py -v
```

### Ejecutar un test específico
```bash
pytest tests/test_auth.py::TestRegister::test_register_success -v
```

### Ejecutar con cobertura
```bash
pytest --cov=app --cov-report=html
```

### Ejecutar en modo watch (re-ejecutar cuando hay cambios)
```bash
pytest-watch tests/
```

### Ejecutar tests rápidos (saltar tests lentos)
```bash
pytest -m "not slow" -v
```

---

## 📊 Tests por Módulo

### 🔐 test_auth.py (Autenticación)

**Clases de test:**
- `TestRegister` - Registro de usuarios
- `TestLogin` - Login y obtención de tokens
- `TestTokenVerification` - Verificación de tokens JWT
- `TestAuthErrors` - Errores de autenticación

**Ejemplos:**
```bash
pytest tests/test_auth.py::TestRegister::test_register_success -v
pytest tests/test_auth.py::TestLogin -v
pytest tests/test_auth.py -v
```

**Cobertura:** Login, registro, JWT, validación

---

### 🏠 test_rooms.py (Gestión de Salas)

**Clases de test:**
- `TestCreateRoom` - Creación de salas
- `TestGetRooms` - Obtener información de salas
- `TestJoinRoom` - Unirse a salas
- `TestLeaveRoom` - Salir de salas
- `TestDeleteRoom` - Eliminar salas
- `TestRoomMembers` - Gestión de miembros
- `TestRoomMessages` - Obtener mensajes
- `TestUpdateRoom` - Actualizar salas

**Ejemplos:**
```bash
# Crear salas
pytest tests/test_rooms.py::TestCreateRoom -v

# Unirse a salas
pytest tests/test_rooms.py::TestJoinRoom::test_join_public_room -v

# Salas privadas
pytest tests/test_rooms.py::TestJoinRoom::test_join_private_room_with_correct_pin -v

# Todo el módulo
pytest tests/test_rooms.py -v
```

**Cobertura:** CRUD de salas, permisos, PINs, miembros, mensajes

---

### 📤 test_upload.py (Upload de Archivos)

**Clases de test:**
- `TestUploadValidation` - Validación de archivos
- `TestUploadSecurity` - Seguridad en uploads
- `TestUploadErrors` - Errores en uploads
- `TestDeleteFile` - Eliminación de archivos
- `TestThumbnail` - Generación de thumbnails
- `TestListFiles` - Listar archivos

**Ejemplos:**
```bash
# Validar archivos
pytest tests/test_upload.py::TestUploadValidation -v

# Seguridad
pytest tests/test_upload.py::TestUploadSecurity::test_reject_high_risk_steganography -v

# Deletar archivos
pytest tests/test_upload.py::TestDeleteFile::test_delete_own_file -v

# Todo
pytest tests/test_upload.py -v
```

**Cobertura:** Validación tipo/tamaño, esteganografía, encriptación, permisos

---

### 🔒 test_security.py (Seguridad)

**Clases de test:**
- `TestEncryptionDetection` - Detección de encriptación
- `TestSteganographyDetection` - Detección de esteganografía
- `TestCompleteMessageValidation` - Validación completa
- `TestSecuritySummary` - Resumen de seguridad
- `TestEntropyCalculation` - Cálculo de entropía
- `TestIntegrationScenarios` - Escenarios reales

**Ejemplos:**
```bash
# Encriptación
pytest tests/test_security.py::TestEncryptionDetection::test_detect_base64 -v

# Esteganografía
pytest tests/test_security.py::TestSteganographyDetection::test_openstego_wav -v

# Validación completa
pytest tests/test_security.py::TestCompleteMessageValidation -v

# Todo
pytest tests/test_security.py -v
```

**Cobertura:** Base64, Hex, PGP, OpenSSL, entropía, OpenStego indicators

---

### 🔌 test_sockets.py (WebSocket)

**Clases de test:**
- `TestAuthEvents` - Autenticación en WebSocket
- `TestMessageEvents` - Eventos de mensajes
- `TestRoomEvents` - Eventos de salas
- `TestErrorHandling` - Manejo de errores
- `TestFileUploadEvents` - Eventos de carga
- `TestPerformance` - Límites y rendimiento

**Ejemplos:**
```bash
# Autenticación
pytest tests/test_sockets.py::TestAuthEvents::test_connect_with_valid_token -v

# Mensajes
pytest tests/test_sockets.py::TestMessageEvents::test_send_message -v

# Detección de encriptación
pytest tests/test_sockets.py::TestMessageEvents::test_message_with_encryption_detection -v

# Rendimiento
pytest tests/test_sockets.py::TestPerformance -v

# Todo
pytest tests/test_sockets.py -v
```

**Cobertura:** Conexión, mensajes, salas, broadcast, encriptación, rate limiting

---

## 📈 Cobertura

### Ejecutar análisis de cobertura
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

Esto genera:
- Reporte en `htmlcov/index.html`
- Estadísticas en terminal

### Cobertura esperada
```
app/routes/        85%
app/models/        90%
app/services/      95%
app/sockets/       80%
app/middleware/    90%
app/utils/         85%
```

### Ver cobertura de un archivo específico
```bash
pytest --cov=app/services/security_service --cov-report=term-missing
```

---

## 🔧 Configuración de Pytest

Crear `pytest.ini` en `backend/`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    slow: tests que tardan más de 1 segundo
    integration: tests de integración
    unit: tests unitarios
```

Crear `conftest.py` en `backend/tests/`:
```python
import pytest
from app import create_app

@pytest.fixture(scope="session")
def app():
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    return app.test_client()
```

---

## 📝 Ejemplos de Ejecución

### 1. Ejecutar todos los tests
```bash
cd backend/
pytest -v
```

**Salida esperada:**
```
test_auth.py::TestRegister::test_register_success PASSED        [5%]
test_auth.py::TestRegister::test_register_invalid_username PASSED [10%]
...
test_rooms.py::TestCreateRoom::test_create_room_success PASSED   [50%]
...
test_security.py::TestEncryptionDetection::test_detect_base64 PASSED [80%]
...
==================== 150 passed in 12.34s ====================
```

### 2. Ejecutar solo tests de seguridad
```bash
pytest tests/test_security.py -v
```

### 3. Ejecutar con cobertura
```bash
pytest --cov=app --cov-report=html
# Abrir htmlcov/index.html en navegador
```

### 4. Ejecutar tests específicos
```bash
# Solo tests de autenticación
pytest tests/test_auth.py -v -k "register"

# Solo tests de WebSocket
pytest tests/test_sockets.py::TestMessageEvents -v
```

---

## 🐛 Troubleshooting

### Problema: `No module named 'pytest'`
**Solución:**
```bash
pip install pytest pytest-flask
```

### Problema: Tests fallan con error de MongoDB
**Solución:**
Asegurar que MongoDB esté corriendo:
```bash
# En Windows
mongod

# En Linux/Mac
brew services start mongodb-community
```

### Problema: Tests de WebSocket fallan
**Solución:**
```bash
pip install python-socketio python-engineio
```

### Problema: Tests lentos
**Solución:**
```bash
# Ejecutar solo tests rápidos
pytest -m "not slow" -v

# O ejecutar en paralelo
pip install pytest-xdist
pytest -n auto -v
```

### Problema: `ConnectionError: can't connect to Cloudinary`
**Solución:**
Los tests mockean Cloudinary automáticamente. Si sigue fallando, verificar `.env`:
```bash
# Usar configuración de testing en .env.test
cp .env.example .env.test
```

---

## ✅ Checklist de Tests

Antes de hacer commit:
- [ ] Todos los tests pasan: `pytest -v`
- [ ] Cobertura >= 80%: `pytest --cov=app`
- [ ] Sin warnings: `pytest -v --tb=short`
- [ ] Tests de seguridad pasan: `pytest tests/test_security.py -v`
- [ ] Tests de WebSocket pasan: `pytest tests/test_sockets.py -v`

---

## 📚 Documentación Adicional

- [pytest official docs](https://docs.pytest.org/)
- [pytest-flask docs](https://pytest-flask.readthedocs.io/)
- [Mocking en pytest](https://docs.pytest.org/en/stable/how-to-mock.html)
- [Fixtures pytest](https://docs.pytest.org/en/stable/how-to-use-fixtures.html)

---

## 🎓 Ejemplos Prácticos

### Crear nuevo test
```python
# tests/test_example.py
import pytest

class TestExample:
    def test_something(self, client, admin_token):
        response = client.get(
            '/endpoint',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
```

### Usar mocks
```python
from unittest.mock import patch

with patch('app.services.CloudinaryService.upload_file') as mock:
    mock.return_value = {'url': 'https://...'}
    # Tu código aquí
```

### Fixture personalizado
```python
@pytest.fixture
def populated_room(client, admin_token):
    response = client.post(
        '/rooms',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'name': 'Test', 'is_private': False}
    )
    return json.loads(response.data)['room']
```

---

## 📞 Contacto y Soporte

Para problemas o preguntas sobre tests:
1. Revisar documentación en `DOCUMENTACION_SEGURIDAD.md`
2. Ver ejemplos en cada archivo de test
3. Consultar issues en el repositorio

---

**Última actualización:** 17 de Noviembre, 2025
**Total de líneas de test:** ~2,131
**Cobertura objetivo:** 85%+
