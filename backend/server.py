from flask import Flask, render_template
from flask_socketio import SocketIO, emit #emit -> reenvia el mensaje a todo el bloque

app = Flask(__name__)
app.config["SECRET_KEY"] = "MI_SUPER_CLAVE_SECRETA"

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

@socketio.on("connect")
def handle_message():
    print('Usuario Conectado')
    emit('status', {'msg': 'Conectado al chat'}, broadcast=True)

@socketio.on("disconnect")
def handle_disconnect():
    print('Usuario desconectado')
    emit('status', {'msg': 'Desconectado del chat'}, broadcast=True)

@socketio.on("message")
def handle_message(data):
    print(f'Nuevo mensaje {data["msg"]} de: {data.get("username")}')
    message_data = {
        'msg': data['msg'],
        'username': data.get("username"),
        'timestamp': data.get("timestamp"),
    }

    emit("response", message_data, broadcast=True)

@app.route('/')
def index():
    return "<h1> Bienvenidos </h1><br/><p>Ingrese a localhost:5000</p>"


if __name__ == '__main__':
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)

# pip install Flask Flask-SocketIO -> se crea un flask

# npm create vite@latest . -- --template-react-ts -> crear un cliente de vite

# npm install primereact primeicons -> componentes de interfaz enriquecida 

# npm install socket.io-client -> soporte del socket en los clientes 

## para activar el primereact es poner dentro del src 

#import React from 'react';
#import ReactDOM from 'react-dom/client';
#import 'primereact/resources/themes/lara-light-indigo/theme.css';  // Tema de PrimeReact (elige uno)
#import 'primereact/resources/primereact.min.css';  // Estilos base
#import 'primeicons/primeicons.css';  // Iconos
#import App from './App.tsx';  // Componente principal

#ReactDOM.createRoot(document.getElementById('root')!).render(
#  <React.StrictMode>
#    <App />
#  </React.StrictMode>
#);