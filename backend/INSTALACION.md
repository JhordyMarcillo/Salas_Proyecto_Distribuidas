# 🚀 GUÍA DE INSTALACIÓN Y CONFIGURACIÓN

## Requisitos Previos

- Python 3.8+
- MongoDB 4.0+ (local o Atlas cloud)
- pip y venv

## 1️⃣ Instalación Inicial

### Paso 1: Crear entorno virtual
```powershell
python -m venv venv
venv\Scripts\Activate
```

### Paso 2: Instalar dependencias
```powershell
pip install -r requirements.txt
```

### Paso 3: Configurar variables de entorno

Crear archivo `.env` en la raíz del proyecto:

```bash
# Ambiente (development, testing, production)
FLASK_ENV=development

# MongoDB
MONGO_URI=mongodb://localhost:27017/salas_distribuidas

# JWT (cambiar a una clave segura en producción)
JWT_SECRET=tu_clave_secreta_super_segura_cambiar_en_produccion

# Cloudinary (opcional para uploads)
CLOUDINARY_CLOUD_NAME=tu_cloud_name
CLOUDINARY_API_KEY=tu_api_key
CLOUDINARY_API_SECRET=tu_api_secret
```

## 2️⃣ Configuración de MongoDB

### Opción A: MongoDB Local
```powershell
# Instalar MongoDB Community Edition
# https://www.mongodb.com/try/download/community

# Verificar que está corriendo
mongosh
# Salir con exit
```

### Opción B: MongoDB Atlas (Cloud)
```
1. Ir a https://www.mongodb.com/cloud/atlas
2. Crear cuenta gratuita
3. Crear cluster
4. Obtener connection string: mongodb+srv://user:pass@cluster.mongodb.net/...
5. Copiar en MONGO_URI del .env
```

## 3️⃣ Ejecutar la Aplicación

### Desarrollo
```powershell
python run.py
```

El servidor estará disponible en `http://localhost:5000`

### Testing
```powershell
python -m pytest tests/ -v
```

### Producción
```powershell
FLASK_ENV=production python run.py
```

⚠️ En producción:
- Cambiar `JWT_SECRET` a una clave segura (64+ caracteres)
- Configurar HTTPS
- Usar variables de entorno para todas las credenciales
- Configurar MongoDB con autenticación

## 4️⃣ Estructuras de Base de Datos

### Colecciones creadas automáticamente

#### users
```json
{
  "_id": ObjectId,
  "username": "admin",
  "password": "hashed_password",
  "is_admin": true,
  "is_anonymous": false,
  "created_at": ISODate,
  "current_room": "General",
  "socket_id": "sid123",
  "last_login": ISODate
}
```

#### rooms
```json
{
  "_id": ObjectId,
  "id": "uuid",
  "name": "General",
  "description": "Sala de discusión general",
  "type": "multimedia",
  "pin": "123456",
  "max_file_mb": 10,
  "created_at": ISODate
}
```

#### messages
```json
{
  "_id": ObjectId,
  "room": "General",
  "username": "admin",
  "nickname": null,
  "msg": "Hola a todos!",
  "timestamp": ISODate,
  "file_url": null,
  "original_filename": null
}
```

## 5️⃣ Troubleshooting

### Error: `Connection refused to MongoDB`
- Verificar que MongoDB está corriendo: `mongosh`
- Verificar `MONGO_URI` en `.env`
- Verificar que MongoDB escucha en `localhost:27017`

### Error: `ModuleNotFoundError: No module named 'app'`
- Verificar que estás en la carpeta correcta: `backend/`
- Verificar que `app/` existe y tiene `__init__.py`

### Error: `RuntimeError` en modelos
- Verificar que `init_models()` se llamó en `create_app()`
- Ver `app/__init__.py` línea 26

### Error: Port 5000 en uso
```powershell
# Ver qué está usando el puerto
netstat -ano | findstr :5000

# O cambiar puerto en run.py
socketio.run(app, port=5001)
```

## 6️⃣ Endpoints de Prueba

### Autenticación
```bash
# Registrar
POST http://localhost:5000/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "password": "password123"
}

# Login
POST http://localhost:5000/auth/login
{
  "username": "testuser",
  "password": "password123"
}

# Obtener token del usuario actual (requiere autenticación)
GET http://localhost:5000/auth/me
Authorization: Bearer <token>
```

### Salas
```bash
# Listar todas las salas
GET http://localhost:5000/rooms

# Crear sala (solo admin)
POST http://localhost:5000/rooms
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Sala Nueva",
  "description": "Una sala nueva",
  "type": "multimedia",
  "max_file_mb": 10
}

# Obtener detalles de una sala
GET http://localhost:5000/rooms/General

# Obtener mensajes de una sala
GET http://localhost:5000/rooms/General/messages?limit=50
```

### Upload de archivos
```bash
# Subir archivo
POST http://localhost:5000/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

[file]: <archivo a subir>
room: General

# Validar archivo antes de subirlo
POST http://localhost:5000/upload/validate
Authorization: Bearer <token>
Content-Type: application/json

{
  "filename": "imagen.jpg",
  "size_bytes": 1024000,
  "room": "General"
}
```

## 7️⃣ WebSocket Events (Cliente → Servidor)

```javascript
// Conectar con autenticación
socket = io('http://localhost:5000', {
  auth: { token: 'eyJ...' }
});

// Registrarse
socket.emit('register', {
  username: 'newuser',
  password: 'password123'
});

// Login
socket.emit('login', {
  username: 'admin',
  password: 'admin123'
});

// Unirse a una sala
socket.emit('join', {
  token: 'eyJ...',
  room: 'General',
  pin: '123456'  // Si requiere
});

// Enviar mensaje
socket.emit('send_message', {
  token: 'eyJ...',
  room: 'General',
  msg: 'Hola!',
  file_url: null,
  original_filename: null
});

// Obtener mensajes
socket.emit('get_messages', {
  token: 'eyJ...',
  room: 'General',
  limit: 50
});

// Salir de una sala
socket.emit('leave', {
  token: 'eyJ...',
  room: 'General'
});

// Notificar que está escribiendo
socket.emit('typing', {
  token: 'eyJ...',
  room: 'General',
  is_typing: true
});
```

## 8️⃣ WebSocket Events (Servidor → Cliente)

```javascript
// Conexión establecida
socket.on('status', (data) => {
  console.log(data.msg);  // "Conexión WebSocket establecida"
});

// Nuevo usuario en sala
socket.on('user_joined', (data) => {
  console.log(`${data.username} se unió a ${data.room}`);
});

// Nuevo mensaje
socket.on('message', (data) => {
  console.log(`${data.nickname || data.username}: ${data.msg}`);
});

// Lista de mensajes
socket.on('messages_list', (data) => {
  console.log(`${data.count} mensajes en ${data.room}`);
});

// Usuario escribiendo
socket.on('user_typing', (data) => {
  console.log(`${data.nickname} está escribiendo...`);
});

// Error
socket.on('error', (data) => {
  console.error(data.msg);
});
```

## 9️⃣ Variables de Entorno Disponibles

| Variable | Default | Descripción |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | Ambiente (development, testing, production) |
| `MONGO_URI` | `mongodb://localhost:27017/...` | Conexión a MongoDB |
| `JWT_SECRET` | `secret_development...` | Clave para firmar JWT |
| `JWT_EXPIRE_HOURS` | `24` | Horas de validez del token |
| `CLOUDINARY_CLOUD_NAME` | `` | Cloud name de Cloudinary |
| `CLOUDINARY_API_KEY` | `` | API key de Cloudinary |
| `CLOUDINARY_API_SECRET` | `` | API secret de Cloudinary |

## 🔟 Seguridad en Producción

**ANTES de desplegar:**

- [ ] Cambiar `JWT_SECRET` a clave segura (64+ caracteres)
- [ ] Configurar `MONGO_URI` con autenticación
- [ ] Usar HTTPS con certificados válidos
- [ ] Whitelist de CORS configurado
- [ ] Secrets en variables de entorno (no en código)
- [ ] MongoDB con réplica set para transacciones
- [ ] Backups automáticos configurados
- [ ] Rate limiting implementado
- [ ] Logging centralizado (Splunk, DataDog, etc.)
- [ ] Monitoreo y alertas activos

---

¿Preguntas? Ver `README.md` o `ANALISIS_ERRORES.md`
