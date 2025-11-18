from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from app.config import config
from app.utils.database import init_database, mongo, bcrypt
from app.services.cloudinary_service import CloudinaryService

socketio = SocketIO()

def create_app(config_name='default'):
    """Factory para crear la aplicación Flask"""
    app = Flask(__name__)
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones
    CORS(app)
    init_database(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode="eventlet")
    
    # Configurar Cloudinary
    with app.app_context():
        CloudinaryService.configure()
    
    # Inicializar modelos
    from app.models import init_models
    user_model, room_model, message_model = init_models(mongo, bcrypt)
    
    # Registrar blueprints
    from app.routes.auth import auth_bp
    from app.routes.rooms import rooms_bp
    from app.routes.upload import upload_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(upload_bp)
    
    # Registrar eventos de socket
    from app.sockets.auth_events import register_auth_events
    from app.sockets.room_events import register_room_events
    from app.sockets.message_events import register_message_events
    
    register_auth_events(socketio)
    register_room_events(socketio)
    register_message_events(socketio)
    
    # Seed inicial
    with app.app_context():
        if mongo.db.users.count_documents({}) == 0:
            user_model.create_user("admin", "admin123", is_admin=True)
            print("[seed] creado usuario 'admin'")
        
        if mongo.db.rooms.count_documents({}) == 0:
            room_model.create_room("General", "Sala de discusión general", "multimedia")
            print("[seed] creada sala 'General'")
    
    @app.route('/')
    def index():
        return "<h3>Servidor WebSocket activo</h3>"
    
    return app