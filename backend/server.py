# server.py
import os
import uuid
import secrets
import jwt
import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.utils import cloudinary_url
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from functools import wraps
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS, cross_origin
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit, join_room, leave_room
from pymongo import ReturnDocument
import requests
from io import BytesIO
from time import time

CLOUDINARY_CLOUD_NAME = "dsfazlofc"
CLOUDINARY_API_KEY = "375549546746736"
CLOUDINARY_API_SECRET = "2pvXZo07QeUjClYKqHgFBoMjoVI"

MONGO_URI = "mongodb://localhost:27017/Proyecto_Distribuidas"
JWT_SECRET = "TOKEN_SUPER_SECRETO_SEGURO"   
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 20

MAX_FILE_SIZE_MB = 10

app = Flask(__name__)
app.config["MONGO_URI"] = MONGO_URI
CORS(app)

mongo = PyMongo(app)
bcrypt = Bcrypt(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

users = mongo.db.users
messages = mongo.db.messages
rooms = mongo.db.rooms

CLOUDINARY_CONFIGURED = False
try:
    if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
        cloudinary.config(
            cloud_name=CLOUDINARY_CLOUD_NAME,
            api_key=CLOUDINARY_API_KEY,
            api_secret=CLOUDINARY_API_SECRET,
            secure=True
        )
        CLOUDINARY_CONFIGURED = True
        print("[info] Cloudinary configurado (desde variables en server.py)")
    else:
        print("[warning] Cloudinary no configurado: revisa las variables en server.py")
except Exception as e:
    CLOUDINARY_CONFIGURED = False
    print("[warning] Error configurando Cloudinary:", e)

def create_token(username: str):
    exp = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {"sub": username, "exp": exp, "iat": datetime.utcnow()}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    if isinstance(token, bytes):
        token = token.decode()
    return token

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise ValueError("token_expired")
    except jwt.InvalidTokenError:
        raise ValueError("token_invalid")

def seed_if_empty():
    if users.count_documents({}) == 0:
        pw = bcrypt.generate_password_hash("admin123").decode()
        users.insert_one({
            "username": "admin",
            "password": pw,
            "created_at": datetime.now(ZoneInfo('America/Guayaquil')),
            "current_room": None,
            "socket_id": None,
            "is_admin": True
        })
        print("[seed] creado usuario 'admin' (password: admin123)")

seed_if_empty()

@socketio.on("connect")
def ws_connect(auth):
    sid = request.sid
    token = None
    if isinstance(auth, dict):
        token = auth.get("token")
    print(f"[connect] sid={sid} conectado, auth_token_present={bool(token)}")
    emit("status", {"msg": "Conexión WebSocket establecida"})

def require_token(func):
    @wraps(func)
    def wrapper(data):
        token = data.get("token")
        username = None

        if token:
            try:
                username = verify_token(token)
            except ValueError as e:
                code = "token_invalid"
                if str(e) == "token_expired":
                    code = "token_expired"
                emit("error", {"code": code, "msg": "Token inválido o expirado"})
                return
        else:
            sid = request.sid
            u = users.find_one({"socket_id": sid})
            if not u:
                emit("error", {"code": "no_token", "msg": "token requerido o registra sesión anónima antes"})
                return
            username = u.get("username")

        return func(username, data)
    return wrapper

def require_jwt_http(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({"msg": "Formato de token inválido. Usar 'Bearer <token>'"}), 401

        if not token:
            return jsonify({"msg": "Token de autorización requerido"}), 401
        
        try:
            username = verify_token(token)
        except ValueError as e:
            code = "token_invalid"
            if str(e) == "token_expired":
                code = "token_expired"
            return jsonify({"code": code, "msg": "Token inválido o expirado"}), 401

        return f(username, *args, **kwargs)
    return decorated_function

@socketio.on("register")
def ws_register(data):
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        emit("register_error", {"msg": "username y password requeridos"})
        return

    if users.find_one({"username": username}):
        emit("register_error", {"msg": "usuario ya existe"})
        return

    pw_hash = bcrypt.generate_password_hash(password).decode()
    users.insert_one({
        "username": username,
        "password": pw_hash,
        "created_at": datetime.utcnow(),
        "current_room": None,
        "socket_id": None,
        "is_admin": False
    })
    token = create_token(username)
    emit("register_success", {"msg": "usuario creado", "token": token})
    print(f"[register] {username} creado")

@socketio.on("login")
def ws_login(data):
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        emit("login_error", {"msg": "username y password requeridos"})
        return

    user = users.find_one({"username": username})
    if not user or not bcrypt.check_password_hash(user["password"], password):
        emit("login_error", {"msg": "credenciales inválidas"})
        return

    token = create_token(username)
    sid = request.sid
    users.find_one_and_update(
        {"username": username},
        {"$set": {"socket_id": sid, "last_login": datetime.utcnow()}},
        return_document=ReturnDocument.AFTER
    )
    emit("login_success", {"msg": "login correcto", "token": token, "is_admin": user.get("is_admin", False)})
    print(f"[login] {username} inició sesión (sid={sid})")

@socketio.on("join")
# En server.py

@socketio.on("join")
def ws_join(data):
    sid = request.sid
    token = data.get("token")
    room_name = (data.get("room") or "").strip()
    provided_pin = (data.get("pin") or "").strip()

    # 1. VALIDAR LA SALA Y EL PIN PRIMERO
    if not room_name:
        emit("join_error", {"msg": "Nombre de sala (room) requerido"})
        return

    room_doc = rooms.find_one({"name": room_name})
    if not room_doc:
        emit("join_error", {"msg": "Sala no existe"})
        return

    required_pin = room_doc.get("pin")
    if required_pin:
        if not provided_pin:
            emit("join_error", {"msg": "PIN requerido para esta sala"})
            return
        # Comparamos como strings
        if str(provided_pin) != str(required_pin): 
            emit("join_error", {"msg": "PIN inválido"})
            return
    
    # 2. SI EL PIN ES CORRECTO (o no se requiere), validar el token
    if not token:
        # Esto ahora es un error, ya que no manejamos anónimos
        emit("join_error", {"code": "no_token", "msg": "Token de autenticación requerido"})
        return

    try:
        username = verify_token(token)
    except ValueError as e:
        code = "token_invalid"
        if str(e) == "token_expired":
            code = "token_expired"
        emit("join_error", {"code": code, "msg": "Token inválido o expirado"})
        return

    # 3. UNIR AL USUARIO
    updated = users.find_one_and_update(
        {"username": username},
        {"$set": {"current_room": room_name, "socket_id": sid}},
        return_document=ReturnDocument.AFTER
    )
    if not updated:
         emit("join_error", {"msg": "Error: Usuario no encontrado en la DB"})
         return

    join_room(room_name)
    emit("join_success", {"room": room_name})
    ts = datetime.now(ZoneInfo('America/Guayaquil'))
    emit("user_joined", {"username": username, "room": room_name, "timestamp": ts.isoformat()}, room=room_name)
    emit("status", {"msg": f"{username} se unió a {room_name}"}, room=room_name)
    print(f"[join] {username} -> {room_name} (PIN verificado)")

    room_id = (data.get("room_id") or "").strip()
    pin = (data.get("pin") or "").strip()
    nickname = (data.get("nickname") or "").strip()
    if not room_id or not pin or not nickname:
        emit("join_error", {"msg": "room_id, pin y nickname son requeridos para acceso anónimo"})
        return

    room_doc = rooms.find_one({"id": room_id})
    if not room_doc:
        emit("join_error", {"msg": "room_id inválido"})
        return

    required_pin = str(room_doc.get("pin") or "")
    if required_pin and pin != required_pin:
        emit("join_error", {"msg": "pin inválido"})
        return

    room_name = room_doc.get("name")

    existing_nick = users.find_one({"current_room": room_name, "nickname": nickname})
    if existing_nick:
        emit("join_error", {"msg": "nickname ya en uso en esta sala"})
        return

    already_on_device = users.find_one({"socket_id": sid, "current_room": {"$ne": None}})
    if already_on_device:
        emit("join_error", {"msg": f"este dispositivo ya está en la sala {already_on_device.get('current_room')}"})
        return

    anon_username = f"anon_{uuid.uuid4().hex[:8]}"
    users.insert_one({
        "username": anon_username,
        "nickname": nickname,
        "is_anonymous": True,
        "created_at": datetime.utcnow(),
        "current_room": room_name,
        "socket_id": sid
    })

    join_room(room_name)
    emit("join_success", {"room": room_name, "nickname": nickname, "username": anon_username})
    ts = datetime.now(ZoneInfo('America/Guayaquil'))
    emit("user_joined", {"username": anon_username, "nickname": nickname, "room": room_name, "timestamp": ts.isoformat()}, room=room_name)
    emit("status", {"msg": f"(anon) {nickname} se unió a {room_name}"}, room=room_name)
    print(f"[join] {anon_username} (nick={nickname}) -> {room_name}")

@socketio.on("leave")
@require_token
def ws_leave(username, data):
    room = (data.get("room") or "").strip()
    if not room:
        emit("leave_error", {"msg": "room requerido"})
        return

    u = users.find_one({"username": username})
    if u and u.get("is_anonymous"):
        if u.get("current_room") != room:
            emit("leave_error", {"msg": "no estás en esa sala"})
            return
        nick = u.get("nickname")
        users.delete_one({"username": username})
        leave_room(room)
        emit("leave_success", {"room": room})
        ts = datetime.now(ZoneInfo('America/Guayaquil'))
        payload = {"username": username, "room": room, "timestamp": ts.isoformat()}
        if nick:
            payload["nickname"] = nick
        emit("user_left", payload, room=room)
        emit("status", {"msg": f"(anon) {nick or username} salió de {room}"}, room=room)
        print(f"[leave] {username} (anon) <- {room}")
        return
    else:
        updated = users.find_one_and_update(
            {"username": username, "current_room": room},
            {"$set": {"current_room": None}},
            return_document=ReturnDocument.AFTER
        )
        if not updated:
            emit("leave_error", {"msg": "no estás en esa sala"})
            return
        leave_room(room)
        emit("leave_success", {"room": room})
        ts = datetime.now(ZoneInfo('America/Guayaquil'))
        emit("user_left", {"username": username, "room": room, "timestamp": ts.isoformat()}, room=room)
        emit("status", {"msg": f"{username} salió de {room}"}, room=room)
        print(f"[leave] {username} <- {room}")

@socketio.on("send_message")
@require_token
def ws_send_message(username, data):
    room = (data.get("room") or "").strip()
    msg = (data.get("msg") or "").strip()
    file_url = data.get("file_url")
    original_filename = data.get("original_filename")

    if not msg and not file_url:
        emit("msg_error", {"msg": "msg o file_url requeridos"})
        return
    if not room:
        emit("msg_error", {"msg": "room requerido"})
        return

    u = users.find_one({"username": username})
    if not u or u.get("current_room") != room:
        emit("msg_error", {"msg": "no perteneces a esa sala"})
        return

    room_doc = rooms.find_one({"name": room})
    room_type = room_doc.get("type", "text") if room_doc else "text"
    if file_url and room_type == "text":
        emit("msg_error", {"msg": "esta sala no permite archivos (solo texto)"})
        return

    doc = {
        "room": room,
        "username": username,
        "nickname": u.get("nickname"),
        "msg": msg,
        "timestamp": datetime.now(ZoneInfo('America/Guayaquil')),
        "file_url": file_url,
        "original_filename": original_filename
    }
    messages.insert_one(doc)

    emit("message", {
        "room": room,
        "username": username,
        "nickname": u.get("nickname"),
        "msg": msg,
        "timestamp": doc["timestamp"].isoformat(),
        "file_url": file_url,
        "original_filename": original_filename
    }, room=room)

    if file_url:
        print(f"[msg-file] [{room}] {u.get('nickname') or username}: {original_filename}")
    else:
        print(f"[msg] [{room}] {u.get('nickname') or username}: {msg}")

@socketio.on("disconnect")
def ws_disconnect():
    sid = request.sid
    user = users.find_one({"socket_id": sid})
    if user:
        username = user.get("username")
        is_anon = user.get("is_anonymous", False)
        current_room = user.get("current_room")
        ts = datetime.now(ZoneInfo('America/Guayaquil'))

        nickname = None
        if is_anon:
            nickname = user.get("nickname")
            users.delete_one({"username": username})
        else:
            users.find_one_and_update(
                {"socket_id": sid},
                {"$set": {"socket_id": None, "current_room": None}},
                return_document=ReturnDocument.AFTER
            )

        payload = {"username": username, "timestamp": ts.isoformat()}
        if current_room:
            payload['room'] = current_room
        if nickname:
            payload["nickname"] = nickname

        emit("user_disconnected", payload, broadcast=True)
        emit("status", {"msg": f"{username} desconectado"}, broadcast=True)
        print(f"[disconnect] limpiado usuario {username} (sid={sid})")
    else:
        print(f"[disconnect] sid no asociado: {sid}")

@app.route("/")
def index():
    return "<h3>Servidor WebSocket (Flask-SocketIO). Use eventos WS para registrar/login/join/leave/send_message.</h3>"

@app.route('/rooms', methods=['GET'])
def list_rooms():
    docs = list(rooms.find({}).sort('created_at', 1))
    out = []
    for d in docs:
        name = d.get('name')
        members = users.count_documents({'current_room': name})
        out.append({
            'id': d.get('id'),
            'name': name,
            'description': d.get('description'),
            'type': d.get('type', 'text'),
            'created_at': d.get('created_at').isoformat() if d.get('created_at') else None,
            'members': members
        })
    return jsonify({'rooms': out})

@app.route('/rooms', methods=['POST'])
@require_jwt_http
def create_room(username):
    user = users.find_one({"username": username})
    if not user or not user.get("is_admin"):
        return jsonify({'msg': 'privilegios insuficientes (admin requerido)'}), 403

    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    description = data.get('description') or ''
    provided_pin = (data.get('pin') or None)
    room_type = (data.get('type') or 'text').lower()
    max_file_mb = int(data.get('max_file_mb')) if data.get('max_file_mb') else MAX_FILE_SIZE_MB

    if room_type not in ('text', 'multimedia'):
        return jsonify({'msg': "type inválido (usar 'text' o 'multimedia')"}), 400

    if not name:
        return jsonify({'msg': 'name requerido'}), 400

    if rooms.find_one({'name': name}):
        return jsonify({'msg': 'room ya existe'}), 400

    if provided_pin is not None:
        pin_str = str(provided_pin).strip()
        if not pin_str.isdigit() or len(pin_str) < 4:
            return jsonify({'msg': 'pin inválido (numérico y al menos 4 dígitos)'}), 400
        pin = pin_str
    else:
        pin = f"{secrets.randbelow(900000) + 100000}"

    room_id = str(uuid.uuid4())
    doc = {
        'id': room_id,
        'name': name,
        'description': description,
        'pin': pin,
        'type': room_type,
        'max_file_mb': max_file_mb,
        'created_at': datetime.now(ZoneInfo('America/Guayaquil'))
    }
    rooms.insert_one(doc)

    return jsonify({
        'msg': 'room creado',
        'room': {
            'id': room_id,
            'name': name,
            'description': description,
            'type': room_type,
            'pin': pin,
            'max_file_mb': max_file_mb
        }
    }), 201

@app.route('/rooms/<room>/messages')
def room_messages(room):
    docs = list(messages.find({"room": room}).sort("timestamp", -1).limit(100))
    docs = list(reversed(docs))
    out = []
    for d in docs:
        ts = d.get("timestamp")
        ts_iso = None
        if ts:
            ts_iso = ts.isoformat() + "Z"
        out.append({
            "username": d.get("username"),
            "nickname": d.get("nickname"),
            "msg": d.get("msg"),
            "timestamp": ts_iso,
            "file_url": d.get("file_url"),
            "original_filename": d.get("original_filename")
        })
    return jsonify({"messages": out})

@app.route('/upload', methods=['POST', 'OPTIONS'])
@cross_origin(origins="*")
def upload_file():
    # Validar configuración Cloudinary
    if not CLOUDINARY_CONFIGURED:
        return jsonify({"msg": "Upload no configurado en el servidor (Cloudinary faltan variables)"}), 500

    if 'file' not in request.files:
        return jsonify({"msg": "No se encontró la parte 'file'"}), 400

    file_to_upload = request.files['file']
    if file_to_upload.filename == '':
        return jsonify({"msg": "No se seleccionó ningún archivo"}), 400

    content_length = request.content_length or 0
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if content_length and content_length > max_bytes:
        return jsonify({"msg": f"Archivo excede límite de {MAX_FILE_SIZE_MB} MB"}), 400

    username = request.form.get('username') or 'anonymous_upload'
    folder = f"chat_uploads/{username}"

    try:
        upload_result = cloudinary.uploader.upload(
            file_to_upload,
            folder=folder,
            resource_type="auto"
        )
        public_url = upload_result.get('secure_url') or upload_result.get('url')
        original_filename = upload_result.get('original_filename', file_to_upload.filename)
        
        print(f"[upload] {username} subió {original_filename} a Cloudinary: {public_url}")
        return jsonify({
            "msg": "Archivo subido exitosamente a Cloudinary",
            "url": public_url,
            "filename": original_filename
        }), 201
    except Exception as e:
        print(f"[upload error] {e}")
        return jsonify({"msg": f"Error al subir: {str(e)}"}), 500

@app.route('/download', methods=['GET', 'OPTIONS'])
@cross_origin(origins="*")
def download_file():
    """Proxy para descargar archivos desde Cloudinary sin problemas de CORS"""
    # Log de todos los parámetros recibidos
    print(f"[download] Query params completos: {request.args}")
    print(f"[download] URL completa: {request.url}")
    
    file_url = request.args.get('url')
    filename = request.args.get('filename', 'archivo')
    
    print(f"[download] Solicitud recibida - URL: {file_url}, Filename: {filename}")
    
    if not file_url:
        print("[download] Error: URL requerida - URL está vacía o None")
        print(f"[download] file_url type: {type(file_url)}, value: '{file_url}'")
        return jsonify({"msg": "URL requerida"}), 400
    
    try:
        # Si es URL de Cloudinary, generar URL con tiempo de expiración largo
        if 'cloudinary.com' in file_url:
            try:
                # Extraer el public_id de la URL
                # Ejemplo: https://res.cloudinary.com/dsfazlofc/image/upload/v1763429286/chat_uploads/dylan/w4x2etkq4t2qthbwlreg.pdf
                # El public_id sería: chat_uploads/dylan/w4x2etkq4t2qthbwlreg
                
                if '/upload/' in file_url:
                    # Extraer el path después de /upload/
                    parts = file_url.split('/upload/')
                    if len(parts) == 2:
                        upload_path = parts[1]
                        # Remover versión si existe (v123456/)
                        if upload_path.startswith('v'):
                            # Buscar el siguiente /
                            slash_idx = upload_path.find('/')
                            if slash_idx != -1:
                                upload_path = upload_path[slash_idx+1:]
                        
                        # Remover extensión si está incluida en el path
                        if '.' in upload_path:
                            public_id = upload_path.rsplit('.', 1)[0]
                        else:
                            public_id = upload_path
                        
                        # Generar URL firmada con expiración de 1 hora
                        expiration = int(time()) + 3600
                        
                        signed_url, _ = cloudinary_url(
                            public_id,
                            secure=True,
                            sign_url=True,
                            type='upload',
                            resource_type='auto'
                        )
                        
                        file_url = signed_url
                        print(f"[download] URL firmada generada: {public_id}")
            except Exception as e:
                print(f"[download] Error generando URL firmada: {e}")
                # Continuar con la URL original si falla
        
        print(f"[download] Descargando desde: {file_url[:80]}...")
        
        # Descargar el archivo desde Cloudinary
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
        }
        
        response = requests.get(file_url, timeout=30, headers=headers, allow_redirects=True)
        
        print(f"[download] Response status: {response.status_code}")
        
        if response.status_code == 401:
            # Intenta con la URL original sin firma
            print(f"[download] 401 con URL firmada, intentando sin firma")
            response = requests.get(request.args.get('url'), timeout=30, headers=headers, allow_redirects=True)
            print(f"[download] Segunda intenta status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[download error] Status {response.status_code} - {response.text[:200]}")
            return jsonify({"msg": f"Error: status {response.status_code}"}), response.status_code
        
        if not response.content:
            print(f"[download error] Respuesta vacía")
            return jsonify({"msg": "Error: respuesta vacía del servidor"}), 500
        
        # Obtener tipo MIME
        content_type = response.headers.get('Content-Type', 'application/octet-stream')
        if not content_type or 'text/html' in content_type:
            if filename.lower().endswith('.pdf'):
                content_type = 'application/pdf'
            elif filename.lower().endswith('.png'):
                content_type = 'image/png'
            elif filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
                content_type = 'image/jpeg'
            elif filename.lower().endswith('.gif'):
                content_type = 'image/gif'
            else:
                content_type = 'application/octet-stream'
        
        print(f"[download] Sirviendo {filename} ({len(response.content)} bytes) como {content_type}")
        
        return send_file(
            BytesIO(response.content),
            download_name=filename,
            as_attachment=True,
            mimetype=content_type
        )
    except requests.exceptions.RequestException as e:
        print(f"[download error] Request failed: {e}")
        return jsonify({"msg": f"Error de conexión: {str(e)}"}), 500
    except Exception as e:
        print(f"[download error] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"msg": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
