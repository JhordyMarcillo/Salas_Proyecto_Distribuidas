from app import create_app, socketio
import os

config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == "__main__":
    socketio.run(
        app, 
        debug=app.config['DEBUG'], 
        host="0.0.0.0", 
        port=5000
    )