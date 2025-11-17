# Salas Proyecto Distribuidas - Backend

Backend para sistema de salas de chat en tiempo real desarrollado con Flask, SocketIO y MongoDB. Permite registro de usuarios, autenticación JWT, gestión de salas y mensajería en tiempo real.

Este documento describe cómo instalar y ejecutar el backend, las variables de entorno importantes, los endpoints HTTP y eventos WebSocket disponibles, así como observaciones de seguridad y problemas conocidos detectados en `server.py`.

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.8+** (recomendado 3.9 o superior)
- **MongoDB** (versión 4.0 o superior)
  - Puedes instalarlo localmente o usar MongoDB Atlas (cloud)
- **pip** (gestor de paquetes de Python)
- **Git** (para clonar el repositorio)

## 🚀 Instalación y Configuración

### Paso 1: Clonar el repositorio

```powershell
cd path\to\Salas_Proyecto_Distribuidas\backend
```

### Paso 2: Crear un entorno virtual (recomendado)

Es recomendable usar un entorno virtual para aislar las dependencias del proyecto:

**Windows:**
```powershell
python -m venv venv
venv\Scripts\Activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Paso 3: Instalar dependencias

```powershell
pip install -r requirements.txt
```

Dependencias relevantes (ver `requirements.txt`). El servidor usa `flask-socketio` en modo `eventlet`, por lo que también necesitas `eventlet` y la librería `cloudinary` si quieres subir archivos a Cloudinary. Ejemplo de paquetes importantes:
- `flask`
- `flask-cors`
- `flask-pymongo`
- `flask-bcrypt`
- `flask-socketio`
- `eventlet`
- `pymongo`
- `pyjwt`
- `cloudinary` (opcional, para uploads)

Si ves errores de incompatibilidad con `werkzeug`, sigue la nota de solución de problemas más abajo.

### Paso 4: Configurar MongoDB

**Opción A: MongoDB Local**

1. Asegúrate de que MongoDB esté corriendo en tu máquina:
   ```powershell
   # Windows (si MongoDB está en el PATH)
   mongod
   ```

2. MongoDB se conectará automáticamente a: `mongodb://localhost:27017/Proyecto_Distribuidas`

**Opción B: MongoDB Atlas (Cloud)**

1. Crea una cuenta en https://www.mongodb.com/cloud/atlas
2. Crea un cluster y obtén la cadena de conexión
3. Configura la variable de entorno `MONGO_URI` (ver Paso 5)

### Paso 5: Configurar variables de entorno (recomendado)

El servidor tiene valores por defecto codificados en `server.py`, pero es inseguro dejar credenciales en el código. Se recomienda configurar las siguientes variables de entorno antes de ejecutar el servidor.

**Windows (PowerShell):**
```powershell
$env:MONGO_URI = "mongodb://localhost:27017/Proyecto_Distribuidas"
$env:JWT_SECRET = "tu_secreto_super_seguro_aqui"
$env:JWT_EXPIRE_HOURS = "24"
$env:CLOUDINARY_CLOUD_NAME = "<tu_cloud_name>"
$env:CLOUDINARY_API_KEY = "<tu_api_key>"
$env:CLOUDINARY_API_SECRET = "<tu_api_secret>"
```

**Linux/Mac:**
```bash
export MONGO_URI="mongodb://localhost:27017/Proyecto_Distribuidas"
export JWT_SECRET="tu_secreto_super_seguro_aqui"
export JWT_EXPIRE_HOURS="24"
export CLOUDINARY_CLOUD_NAME="<tu_cloud_name>"
export CLOUDINARY_API_KEY="<tu_api_key>"
export CLOUDINARY_API_SECRET="<tu_api_secret>"
```

- **`MONGO_URI`**: URI de conexión a MongoDB (default codificado: `mongodb://localhost:27017/Proyecto_Distribuidas`).
- **`JWT_SECRET`**: Secreto para firmar tokens JWT (default en código: `TOKEN_SUPER_SECRETO_SEGURO`) — cámbialo siempre en producción.
- **`JWT_EXPIRE_HOURS`**: Horas de expiración del token (default en código: `20`).
- **`CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`**: Configuración para subir archivos a Cloudinary. Si no están definidos, las funcionalidades de upload fallarán o el servidor intentará usar valores codificados en `server.py` (no recomendado).

Nota: Actualmente `server.py` contiene credenciales de Cloudinary y valores por defecto en el código. Es crítico mover esas credenciales a variables de entorno antes de desplegar en cualquier entorno público.

### Paso 6: Levantar el servidor

```powershell
# activar virtualenv (Windows)
venv\Scripts\Activate
# ejecutar
python server.py
```

El servidor se iniciará en:
- **URL:** `http://localhost:5000`
- **WebSocket:** `ws://localhost:5000/socket.io/`

En la primera ejecución, si la colección de usuarios está vacía, `server.py` crea automáticamente un usuario administrador:
- **Usuario:** `admin`
- **Contraseña:** `admin123`

IMPORTANTE: Cambia la contraseña del admin y el `JWT_SECRET` antes de exponer el servicio.

## 📡 API y Eventos WebSocket

### Endpoints HTTP REST

- **`GET /`**: Página de bienvenida con información del servidor.

- **`GET /rooms`**: Lista todas las salas. Respuesta contiene `id`, `name`, `description`, `type`, `created_at` e `members`.

- **`POST /rooms`** (admin): Crea una sala nueva. Requiere token JWT en header `Authorization: Bearer <token>`. Body JSON esperado:
  - `name` (string, requerido)
  - `description` (opcional)
  - `pin` (opcional, si no se proporciona se genera uno)
  - `type` (`text` o `multimedia`)
  - `max_file_mb` (opcional)

- **`GET /rooms/<room>/messages`**: Obtiene últimos 100 mensajes de la sala `<room>`.

### Eventos WebSocket (resumen)

- **`connect`**: Conexión inicial. El servidor emite `status`.

- **`register`**: Registra un usuario. Payload: `{ "username": "user", "password": "pass" }`. Respuestas: `register_success`, `register_error`.

- **`login`**: Login de usuario. Payload: `{ "username": "user", "password": "pass" }`. Respuestas: `login_success` (incluye `token`), `login_error`.

- **`join`**: Unir a sala. El servidor exige un token JWT para la mayoría de flujos. Payload habitual: `{ "token": "<JWT>", "room": "room_name", "pin": "optional" }`.
  - Respuestas: `join_success`, `join_error`, y el evento `user_joined` broadcast en la sala.
  - Atención: `server.py` contiene lógica para joins anónimos pero, en la versión actual, el flujo para anónimos es efectivamente inalcanzable porque el handler retorna error si `token` no está presente. Ver 'Problemas conocidos' abajo.

- **`leave`**: Abandonar sala. Payload: `{ "token": "<JWT>", "room": "room_name" }`. Respuestas: `leave_success`, `leave_error`, y `user_left` broadcast.

- **`send_message`**: Enviar mensaje o archivo. Payload: `{ "token": "<JWT>", "room": "room_name", "msg": "texto opcional", "file_url": "url opcional", "original_filename": "opcional" }`.
  - Respuestas: `message` (broadcast) o `msg_error`.

- **`disconnect`**: Evento automático. El servidor limpia `socket_id`, elimina usuarios anónimos y emite `user_disconnected` y `status`.

## 🧪 Pruebas

### Cliente de prueba

Hay un `client.html` en el directorio `backend` que sirve para pruebas manuales (conectar, registrar, logear, unirse a salas y enviar mensajes).

### Usando herramientas (Postman / wscat)

1. Conecta a WebSocket: `ws://localhost:5000/socket.io/?EIO=4&transport=websocket`
2. Para probar eventos raw con el protocolo socket.io (poco amigable desde Postman) usa un cliente socket.io o abre `client.html`.

Ejemplos de eventos via socket.io (desde un cliente JS):
```javascript
socket.emit('register', { username: 'user', password: 'pass123' });
socket.emit('login', { username: 'admin', password: 'admin123' });
socket.emit('join', { token: '<JWT>', room: 'sala1' });
socket.emit('send_message', { token: '<JWT>', room: 'sala1', msg: 'Hola!' });
socket.emit('leave', { token: '<JWT>', room: 'sala1' });
```

## 🔒 Seguridad

- **Contraseñas**: se almacenan hasheadas con `bcrypt`.
- **Autenticación**: JWT firmado con `JWT_SECRET`. Cambia el secreto en producción.
- **Expiración**: tokens expiran (valor por defecto: 20 horas en código).
- **Control de acceso**: el servidor verifica que el usuario que envía mensajes esté en la sala correspondiente.
- **Riesgos detectados**: el código contiene credenciales de Cloudinary incrustadas. Mover estas credenciales a variables de entorno.

## 📝 Notas

- El servidor crea automáticamente un usuario `admin` con contraseña `admin123` si la colección `users` está vacía.
- Los timestamps usan la zona horaria `America/Guayaquil`.
- El servidor corre en `debug=True` en `server.py`. Para producción, desactivar debug y usar un servidor WSGI apropiado.

## 🐛 Problemas conocidos y recomendaciones

1. **Join anónimo inalcanzable**: `server.py` contiene lógica para permitir joins anónimos (inserta usuarios con `is_anonymous`) pero el handler `ws_join` retorna un error si `token` no está presente antes de esa lógica. Resultado: el flujo anónimo actualmente no se ejecuta.
   - Recomendación: decidir si se quiere soporte de joins anónimos y reordenar la lógica del handler `join` para permitir la rama anónima (p. ej. si `room_id` + `pin` + `nickname` están presentes, hacer el flujo anónimo; si `token` está presente, validar token normal).

2. **Credenciales hardcodeadas de Cloudinary**: `CLOUDINARY_*` están definidas en `server.py`. Esto es inseguro. Moverlas a variables de entorno y cargar con `os.getenv(...)`.

3. **Dependencia en `eventlet`**: `SocketIO` se inicia con `async_mode='eventlet'`. Asegúrate de tener `eventlet` instalado y usarlo en producción si se mantiene esa configuración.

4. **Validaciones y mensajes de error**: añadir más validaciones y códigos estandarizados (p. ej. `code` en eventos de error) mejora la interoperabilidad del cliente.

5. **Limpieza de sockets**: `disconnect` borra usuarios anónimos y limpia `socket_id` para usuarios registrados; revisar que no quede estado inconsistente si un cliente reconecta.

### Fragmento de fix sugerido para `join` anónimo (ejemplo conceptual)
```python
# Pseudocódigo: comprobar si payload contiene room_id/pin/nickname -> flujo anon
# else: intentar validar token -> flujo autenticado
```

Si quieres, puedo aplicar un parche a `server.py` para:
- mover las credenciales a `os.getenv(...)`;
- arreglar el flujo de `ws_join` para soportar joins anónimos correctamente;
- añadir logs y mensajes de error consistentes.

## 🧰 Solución de Problemas (resumen)

- **Cannot connect to MongoDB**: verifica MongoDB y `MONGO_URI`.
- **Port 5000 ocupado**: cambia el puerto en `server.py` o libera el puerto.
- **ImportError url_quote**: incompatibilidad `Werkzeug`. Si ocurre, instala `werkzeug==2.2.3` o usa el `requirements.txt` correcto.

## 📚 Estructura del Proyecto

```
backend/
├── server.py          # Servidor principal Flask + SocketIO
├── client.html        # Cliente de prueba HTML/JavaScript
├── requirements.txt   # Dependencias del proyecto
└── README-back.md     # Esta documentación (actualizada)
```

## 👥 Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Especificar licencia si aplica.
