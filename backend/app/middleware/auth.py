from functools import wraps
from flask import request, jsonify
from flask_socketio import emit
from app.services.jwt_service import JWTService


def require_jwt_http(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from app.services.jwt_service import JWTService
        
        token = None
        
        # Extraer token del header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                # Formato esperado: "Bearer <token>"
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({
                    "msg": "Formato de token inválido. Usar 'Bearer <token>'"
                }), 401

        if not token:
            return jsonify({"msg": "Token de autorización requerido"}), 401
        
        # Verificar el token
        try:
            username = JWTService.verify_token(token)
        except ValueError as e:
            code = "token_invalid"
            if str(e) == "token_expired":
                code = "token_expired"
            return jsonify({
                "code": code, 
                "msg": "Token inválido o expirado"
            }), 401

        # Inyectar username como primer argumento
        return f(username, *args, **kwargs)
    
    return decorated_function


def require_token_socket(func):
    @wraps(func)
    def wrapper(data):
        from app.services.jwt_service import JWTService
        from app.utils.database import mongo
        
        users = mongo.db.users
        token = data.get("token")
        username = None

        if token:
            # Verificar token JWT
            try:
                username = JWTService.verify_token(token)
            except ValueError as e:
                code = "token_invalid"
                if str(e) == "token_expired":
                    code = "token_expired"
                emit("error", {
                    "code": code, 
                    "msg": "Token inválido o expirado"
                })
                return
        else:
            # Buscar usuario por socket_id (sesión anónima)
            sid = request.sid
            u = users.find_one({"socket_id": sid})
            if not u:
                emit("error", {
                    "code": "no_token", 
                    "msg": "Token requerido o registra sesión anónima antes"
                })
                return
            username = u.get("username")

        # Inyectar username como primer argumento
        return func(username, data)
    
    return wrapper


def require_admin(f):
    @wraps(f)
    def decorated_function(username, *args, **kwargs):
        from app.utils.database import mongo
        
        user = mongo.db.users.find_one({"username": username})
        
        if not user or not user.get("is_admin", False):
            return jsonify({
                "msg": "Privilegios insuficientes. Se requiere rol de administrador."
            }), 403
        
        return f(username, *args, **kwargs)
    
    return decorated_function


def require_admin_socket(func):
    @wraps(func)
    def wrapper(username, data):
        from app.utils.database import mongo
        
        users = mongo.db.users
        user = users.find_one({"username": username})
        
        if not user or not user.get("is_admin", False):
            emit("error", {
                "code": "forbidden",
                "msg": "Privilegios insuficientes. Se requiere rol de administrador."
            })
            return
        
        return func(username, data)
    
    return wrapper


def optional_auth_http(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from app.services.jwt_service import JWTService
        
        username = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
                try:
                    username = JWTService.verify_token(token)
                except ValueError:
                    # Token inválido, pero como es opcional, continuamos
                    pass
            except IndexError:
                pass
        
        return f(username, *args, **kwargs)
    
    return decorated_function