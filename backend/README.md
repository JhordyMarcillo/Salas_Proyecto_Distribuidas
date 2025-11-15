# Salas Proyecto Distribuidas - Backend

Backend para sistema de salas de chat en tiempo real desarrollado con Flask, SocketIO y MongoDB. Permite registro de usuarios, autenticación JWT, gestión de salas y mensajería en tiempo real.

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.8+** (recomendado 3.9 o superior)
- **MongoDB** (versión 4.0 o superior)
  - Puedes instalarlo localmente o usar MongoDB Atlas (cloud)
- **pip** (gestor de paquetes de Python)
- **Git** (para clonar el repositorio)

## 🚀 Instalación y Configuración

### Paso 1: Clonar el repositorio

```bash
cd Salas_Proyecto_Distribuidas/backend
```

### Paso 2: Crear un entorno virtual (recomendado)

Es recomendable usar un entorno virtual para aislar las dependencias del proyecto:

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Paso 3: Instalar dependencias

```bash
pip install -r requirements.txt
```

Esto instalará las siguientes dependencias:
- `flask==2.2.3` - Framework web
- `flask-cors==3.1.1` - Soporte CORS
- `flask-pymongo==2.3.0` - Integración con MongoDB
- `flask-bcrypt==1.0.1` - Encriptación de contraseñas
- `flask-socketio==5.3.0` - WebSockets
- `pymongo==4.2.0` - Driver de MongoDB
- `pyjwt==2.10.1` - Tokens JWT

### Paso 4: Configurar MongoDB

**Opción A: MongoDB Local**

1. Asegúrate de que MongoDB esté corriendo en tu máquina:
   ```bash
   # Windows (si MongoDB está en el PATH)
   mongod
   
   # O verifica que el servicio esté corriendo
   ```

2. MongoDB se conectará automáticamente a: `mongodb://localhost:27017/Proyecto_Distribuidas`

**Opción B: MongoDB Atlas (Cloud)**

1. Crea una cuenta en [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Crea un cluster y obtén la cadena de conexión
3. Configura la variable de entorno `MONGO_URI` (ver Paso 5)

### Paso 5: Configurar variables de entorno (opcional)

El servidor funciona con valores por defecto, pero puedes personalizar la configuración mediante variables de entorno:

**Windows (PowerShell):**
```powershell
$env:MONGO_URI="mongodb://localhost:27017/Proyecto_Distribuidas"
$env:JWT_SECRET="tu_secreto_super_seguro_aqui"
$env:JWT_EXPIRE_HOURS="24"
```

**Windows (CMD):**
```cmd
set MONGO_URI=mongodb://localhost:27017/Proyecto_Distribuidas
set JWT_SECRET=tu_secreto_super_seguro_aqui
set JWT_EXPIRE_HOURS=24
```

**Linux/Mac:**
```bash
export MONGO_URI="mongodb://localhost:27017/Proyecto_Distribuidas"
export JWT_SECRET="tu_secreto_super_seguro_aqui"
export JWT_EXPIRE_HOURS="24"
```

**Variables disponibles:**
- `MONGO_URI`: URI de conexión a MongoDB (default: `mongodb://localhost:27017/Proyecto_Distribuidas`)
- `JWT_SECRET`: Secreto para firmar tokens JWT (default: `TOKEN_SUPER_SECRETO_SEGURO`)
- `JWT_EXPIRE_HOURS`: Horas de expiración del token (default: `20`)

### Paso 6: Levantar el servidor

```bash
python server.py
```

El servidor se iniciará en:
- **URL:** `http://localhost:5000`
- **WebSocket:** `ws://localhost:5000/socket.io/`

Deberías ver un mensaje indicando que el servidor está corriendo. Si es la primera vez, se creará automáticamente un usuario administrador:
- **Usuario:** `admin`
- **Contraseña:** `admin123`

## 📡 API y Eventos WebSocket

### Endpoints HTTP REST

#### `GET /`
Página de bienvenida con información del servidor.

#### `GET /rooms`
Obtiene la lista de todas las salas disponibles.

**Respuesta:**
```json
{
  "rooms": [
    {
      "name": "sala1",
      "description": "Descripción de la sala",
      "created_at": "2024-01-01T12:00:00",
      "members": 3
    }
  ]
}
```

#### `POST /rooms`
Crea una nueva sala.

**Body:**
```json
{
  "name": "sala1",
  "description": "Descripción opcional"
}
```

**Respuesta:**
```json
{
  "msg": "room creado",
  "room": {
    "name": "sala1",
    "description": "Descripción opcional"
  }
}
```

#### `GET /rooms/<room>/messages`
Obtiene los últimos 100 mensajes de una sala.

**Respuesta:**
```json
{
  "messages": [
    {
      "username": "usuario1",
      "msg": "Hola mundo",
      "timestamp": "2024-01-01T12:00:00"
    }
  ]
}
```

### Eventos WebSocket

#### `connect`
Establece conexión WebSocket con el servidor.

**Ejemplo:**
```javascript
const socket = io('http://localhost:5000');
socket.on('connect', () => {
  console.log('Conectado');
});
```

#### `register`
Registra un nuevo usuario.

**Payload:**
```json
{
  "username": "nuevo_usuario",
  "password": "contraseña123"
}
```

**Respuestas:**
- `register_success`: `{ "msg": "usuario creado", "token": "<JWT_TOKEN>" }`
- `register_error`: `{ "msg": "mensaje de error" }`

#### `login`
Inicia sesión con un usuario existente.

**Payload:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Respuestas:**
- `login_success`: `{ "msg": "login correcto", "token": "<JWT_TOKEN>" }`
- `login_error`: `{ "msg": "credenciales inválidas" }`

#### `join`
Une al usuario a una sala (requiere token JWT).

**Payload:**
```json
{
  "token": "<JWT_TOKEN>",
  "room": "sala1"
}
```

**Respuestas:**
- `join_success`: `{ "room": "sala1" }`
- `join_error`: `{ "msg": "mensaje de error" }`
- `user_joined`: `{ "username": "usuario", "room": "sala1", "timestamp": "..." }` (broadcast a la sala)

#### `leave`
Sale de una sala (requiere token JWT).

**Payload:**
```json
{
  "token": "<JWT_TOKEN>",
  "room": "sala1"
}
```

**Respuestas:**
- `leave_success`: `{ "room": "sala1" }`
- `leave_error`: `{ "msg": "mensaje de error" }`
- `user_left`: `{ "username": "usuario", "room": "sala1", "timestamp": "..." }` (broadcast a la sala)

#### `send_message`
Envía un mensaje a una sala (requiere token JWT).

**Payload:**
```json
{
  "token": "<JWT_TOKEN>",
  "room": "sala1",
  "msg": "Hola a todos!"
}
```

**Respuestas:**
- `message`: `{ "room": "sala1", "username": "usuario", "msg": "Hola a todos!", "timestamp": "..." }` (broadcast a la sala)
- `msg_error`: `{ "msg": "mensaje de error" }`

#### `disconnect`
Se emite automáticamente cuando un cliente se desconecta.

**Eventos broadcast:**
- `user_disconnected`: `{ "username": "usuario", "timestamp": "...", "room": "sala1" }` (opcional)
- `status`: `{ "msg": "usuario desconectado" }`

## 🧪 Pruebas

### Usando el cliente HTML de prueba

El proyecto incluye un archivo `client.html` que puedes abrir en tu navegador para probar todas las funcionalidades:

1. Asegúrate de que el servidor esté corriendo
2. Abre `client.html` en tu navegador
3. Conecta al servidor (`http://localhost:5000`)
4. Prueba registro, login, unirse a salas y enviar mensajes

### Usando Postman

1. Conecta a WebSocket: `ws://localhost:5000/socket.io/?EIO=4&transport=websocket`
2. Envía el paquete inicial: `40`
3. Prueba los eventos:
   - `42["register", {"username":"user","password":"pass123"}]`
   - `42["login", {"username":"admin","password":"admin123"}]`
   - `42["join", {"token":"<JWT>","room":"sala1"}]`
   - `42["send_message", {"token":"<JWT>","room":"sala1","msg":"Hola!"}]`
   - `42["leave", {"token":"<JWT>","room":"sala1"}]`

## 🔒 Seguridad

- Las contraseñas se almacenan hasheadas con bcrypt
- La autenticación utiliza tokens JWT
- Los tokens tienen expiración configurable (default: 20 horas)
- Los usuarios solo pueden enviar mensajes a salas en las que están unidos
- Un usuario solo puede estar en una sala a la vez

## 📝 Notas

- El servidor crea automáticamente un usuario `admin` con contraseña `admin123` si la base de datos está vacía
- Los timestamps utilizan la zona horaria de Guayaquil (America/Guayaquil)
- El servidor corre en modo debug por defecto (útil para desarrollo)
- Para producción, desactiva el modo debug y configura un `JWT_SECRET` seguro

## 🐛 Solución de Problemas

### Error: "Cannot connect to MongoDB"
- Verifica que MongoDB esté corriendo
- Revisa la URI de conexión en `MONGO_URI`
- Si usas MongoDB Atlas, verifica que tu IP esté en la whitelist

### Error: "Port 5000 already in use"
- Cambia el puerto en `server.py` (línea 326): `socketio.run(app, debug=True, host="0.0.0.0", port=5001)`
- O cierra el proceso que está usando el puerto 5000

### Error: "ImportError: cannot import name 'url_quote' from 'werkzeug.urls'"
Este error ocurre por incompatibilidad entre Flask 2.2.3 y Werkzeug 3.0+. Solución:

```bash
# Desinstala las dependencias actuales
pip uninstall -y flask werkzeug

# Reinstala con las versiones correctas
pip install -r requirements.txt
```

O manualmente:
```bash
pip install werkzeug==2.2.3
```

### Error al instalar dependencias
- Asegúrate de estar usando Python 3.8+
- Actualiza pip: `python -m pip install --upgrade pip`
- Si tienes problemas de compatibilidad, reinstala todas las dependencias:
  ```bash
  pip uninstall -r requirements.txt -y
  pip install -r requirements.txt
  ```

## 📚 Estructura del Proyecto

```
backend/
├── server.py          # Servidor principal Flask + SocketIO
├── client.html        # Cliente de prueba HTML/JavaScript
├── requirements.txt   # Dependencias del proyecto
└── README.md         # Esta documentación
```

## 👥 Contribuir

Para contribuir al proyecto:
1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

[Especificar licencia si aplica]
