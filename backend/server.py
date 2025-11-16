import os
import jwt
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit, join_room, leave_room
from pymongo import ReturnDocument

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/Proyecto_Distribuidas")
JWT_SECRET = os.getenv("JWT_SECRET", "TOKEN_SUPER_SECRETO_SEGURO")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "20"))

app = Flask(__name__)
app.config["MONGO_URI"] = MONGO_URI

# Allow cross-origin requests from the frontend dev server
CORS(app)

mongo = PyMongo(app)
bcrypt = Bcrypt(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

users = mongo.db.users
messages = mongo.db.messages
rooms = mongo.db.rooms

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
            "socket_id": None
        })
        print("[seed] creado usuario 'admin' (password: admin123)")

seed_if_empty()


@socketio.on("connect")
def ws_connect(auth):
    #sid -> para controlar solo un solo cliente por sala 
    sid = request.sid
    token = None
    if isinstance(auth, dict):
        token = auth.get("token")
    print(f"[connect] sid={sid} conectado, auth_token_present={bool(token)}")
    emit("status", {"msg": "Conexión WebSocket establecida"})

def require_token(func):
    #copia metadatos de la función original
    @wraps(func)
    def wrapper(data):
        token = data.get("token")
        if not token:
            emit("error", {"code": "no_token", "msg": "token requerido"})
            return
        try:
            username = verify_token(token)
        except ValueError as e:
            code = "token_invalid"
            if str(e) == "token_expired":
                code = "token_expired"
            emit("error", {"code": code, "msg": "Token inválido o expirado"})
            return
        return func(username, data)
    return wrapper

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
        "socket_id": None
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

    sid = None
    try:
        sid = request.sid
    except Exception:
        sid = request.sid

    users.find_one_and_update(
        {"username": username},
        {"$set": {"socket_id": sid, "last_login": datetime.utcnow()}}
    )

    emit("login_success", {"msg": "login correcto", "token": token})
    print(f"[login] {username} inició sesión (sid={sid})")


@socketio.on("join")
@require_token
def ws_join(username, data):
    room = (data.get("room") or "").strip()
    if not room:
        emit("join_error", {"msg": "room requerido"})
        return

    sid = None
    try:
        sid = request.sid
    except Exception:
        sid = request.sid

    updated = users.find_one_and_update(
        {"username": username, "current_room": None},
        {"$set": {"current_room": room, "socket_id": sid}},
        return_document=ReturnDocument.AFTER
    )

    if not updated:
        u = users.find_one({"username": username})
        emit("join_error", {"msg": f"usuario ya en sala {u.get('current_room')}"})
        return

    join_room(room)
    emit("join_success", {"room": room})
    # emitir evento estructurado y texto legacy
    ts = datetime.now(ZoneInfo('America/Guayaquil'))
    emit("user_joined", {"username": username, "room": room, "timestamp": ts.isoformat()}, room=room)
    emit("status", {"msg": f"{username} se unió a {room}"}, room=room)
    print(f"[join] {username} -> {room}")


@socketio.on("leave")
@require_token
def ws_leave(username, data):
    room = (data.get("room") or "").strip()
    if not room:
        emit("leave_error", {"msg": "room requerido"})
        return

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
    # emitir evento estructurado y texto legacy
    ts = datetime.now(ZoneInfo('America/Guayaquil'))
    emit("user_left", {"username": username, "room": room, "timestamp": ts.isoformat()}, room=room)
    emit("status", {"msg": f"{username} salió de {room}"}, room=room)
    print(f"[leave] {username} <- {room}")


@socketio.on("send_message")
@require_token
def ws_send_message(username, data):
    room = (data.get("room") or "").strip()
    msg = (data.get("msg") or "").strip()
    if not room or not msg:
        emit("msg_error", {"msg": "room y msg requeridos"})
        return

    u = users.find_one({"username": username})
    if u.get("current_room") != room:
        emit("msg_error", {"msg": "no perteneces a esa sala"})
        return

    doc = {
        "room": room,
        "username": username,
        "msg": msg,
        # usar zona horaria de Guayaquil para timestamps
        "timestamp": datetime.now(ZoneInfo('America/Guayaquil'))
    }
    messages.insert_one(doc)

    # Emitir a la sala
    emit("message", {
        "room": room,
        "username": username,
        "msg": msg,
        "timestamp": doc["timestamp"].isoformat()
    }, room=room)
    print(f"[msg] [{room}] {username}: {msg}")


@socketio.on("disconnect")
def ws_disconnect():
    sid = request.sid
    user = users.find_one_and_update(
        {"socket_id": sid},
        {"$set": {"socket_id": None, "current_room": None}},
        return_document=ReturnDocument.AFTER
    )
    if user:
        # Emitir evento estructurado de desconexión (si tenía sala, indicar room)
        ts = datetime.now(ZoneInfo('America/Guayaquil'))
        payload = {"username": user['username'], "timestamp": ts.isoformat()}
        # incluir room si existía
        if user.get('current_room'):
            payload['room'] = user.get('current_room')
        emit("user_disconnected", payload, broadcast=True)
        emit("status", {"msg": f"{user['username']} desconectado"}, broadcast=True)
        print(f"[disconnect] limpiado usuario {user['username']} (sid={sid})")
    else:
        print(f"[disconnect] sid no asociado: {sid}")


@app.route("/")
def index():
    return "<h3>Servidor WebSocket (Flask-SocketIO). Use eventos WS para registrar/login/join/leave/send_message.</h3>"


@app.route('/rooms', methods=['GET'])
def list_rooms():
    # listado de salas definidas en la colección 'rooms'
    docs = list(rooms.find({}).sort('created_at', 1))
    out = []
    for d in docs:
        name = d.get('name')
        members = users.count_documents({'current_room': name})
        out.append({
            'name': name,
            'description': d.get('description'),
            'created_at': d.get('created_at').isoformat() if d.get('created_at') else None,
            'members': members
        })
    return jsonify({'rooms': out})


@app.route('/rooms', methods=['POST'])
def create_room():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    description = data.get('description') or ''
    if not name:
        return jsonify({'msg': 'name requerido'}), 400

    if rooms.find_one({'name': name}):
        return jsonify({'msg': 'room ya existe'}), 400

    doc = {
        'name': name,
        'description': description,
        'created_at': datetime.now(ZoneInfo('America/Guayaquil'))
    }
    rooms.insert_one(doc)
    return jsonify({'msg': 'room creado', 'room': {'name': name, 'description': description}}), 201


@app.route('/rooms/<room>/messages')
def room_messages(room):
    # Devuelve los últimos 100 mensajes de la sala
    docs = list(messages.find({"room": room}).sort("timestamp", -1).limit(100))
    # invertir para enviar desde el más antiguo al más nuevo
    docs = list(reversed(docs))
    out = []
    for d in docs:
        ts = d.get("timestamp")
        ts_iso = None
        if ts:
            # Añadimos la 'Z' manualmente para forzar que sea UTC
            ts_iso = ts.isoformat() + "Z" 
            
        out.append({
            "username": d.get("username"),
            "msg": d.get("msg"),
            "timestamp": ts_iso
        })
    return jsonify({"messages": out})

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)


## para probar en el postman:
# 1. Conexión WebSocket a ws://localhost:5000/socket.io/?EIO=4&transport=websocket
# 2. mandar un paquete para comenzar: 40
# 3. 42["register", {"username":"user","password":"pass123"}]
# 4. 42["login", {"username":"postman_user","password":"pass123"}]
# 5. 42["join", {"token":"<JWT>","room":"sala1"}]
# 6. 42["send_message", {"token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwb3N0bWFuX3VzZXIiLCJleHAiOjE3NjI5NzcyOTAsImlhdCI6MTc2MjkwNTI5MH0.ct3q9NaGNVoEWAuqV6Vebus6JaOu4QnJ73x7AYOyRgk","room":"sala1","msg":"Hola desde Postman!"}]
#7. 42["leave", {"token":"<JWT>","room":"sala1"}]






