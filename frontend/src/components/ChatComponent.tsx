import type React from "react";
import { useEffect, useRef, useState } from "react";
import { io, Socket } from "socket.io-client";
import { Toast } from 'primereact/toast';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { InputText } from 'primereact/inputtext';
import { Divider } from 'primereact/divider';
        

interface MessageData{
    msg: string;
    username: string;
    timestamp: string;
}

export const ChatComponent: React.FC = () => {

    const [socket, setSocket] = useState<Socket | null>(null);
    const [isConnected, setIsConnected] = useState<boolean>(false);
    const [messages, setMessages] = useState<string[]>([]);
    const [username, setUsername] = useState<string>('');
    const [inputValue, setInputValue] = useState<string>('');
    const toast = useRef<Toast | null>(null);

    const messagesEndRef = useRef<null | HTMLDivElement>(null);

    useEffect(() => {
        if (username) {
            console.log(`Intentando conectarse con el username: ${username}`);
            const newSocket = io('http://localhost:5000', )
            
            newSocket.on('connect', () => {
                console.log('Conectado al servidor de chat')
                setIsConnected(true)
                showToast('success', 'Conexión exitosa', `Bienvenido , ${username}`);
            })

            newSocket.on('disconnect', () => {
                console.log('Desconectado del servidor de chat')
                setIsConnected(false);
                showToast('warn', 'Desconectado', `Conexión perdida de ${username}`);
            })

            newSocket.on('status', (data: {msg: string}) => {
                showToast('info', 'Estado del servidor', data.msg)
            })

            newSocket.on('response', (data: MessageData) => {
                const message = `[${data.timestamp}] ${data.username}: ${data.msg}`
                setMessages((prev) => [...prev, message])
                showToast('warn', 'Nuevo mensaje', `${data.username} dice: ${data.msg}`);
            });
            setSocket(newSocket)

            return () => {
                newSocket.close()
            }
        }
    }, [username])

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }

    useEffect(() => { scrollToBottom() }, [messages]);

     const sendMessage = () => {
        if(isConnected && inputValue.trim() && socket){
            const messageData: MessageData = {
                msg: inputValue,
                username,
                timestamp: new Date().toLocaleTimeString()
            }

            socket.emit('message', messageData)
            setInputValue('')
        }
    }



    const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' && isConnected) {
            sendMessage()
        }
    }

    const handleUsernameSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (username.trim()) {
        //
        }
    }

    const showToast = (severity: string, summary: string, detail: string) => {
        toast.current?.show({ severity, summary, detail });
    };


    return (
    <Card title="Chat en Vivo" className="p-m-2">
      <Toast ref={toast} position="top-right" />
      
      {!isConnected && (
        <form onSubmit={handleUsernameSubmit} className="p-d-flex p-flex-column p-ai-center p-mb-3">
          <label htmlFor="username-input" className="p-mb-1">Ingresa tu nombre:</label>
          <div className="p-d-flex p-ai-center">
            <InputText
              id="username-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Tu nombre..."
              className="p-mr-2"
              autoFocus
            />
            <Button label="Entrar" type="submit" icon="pi pi-sign-in" disabled={!username.trim()} />
          </div>
        </form>
      )}

      {isConnected && (
        <div className="p-d-flex p-jc-between p-ai-center p-mb-2">
          <h4>Conectado como: <strong>{username}</strong></h4>
          <Button
            label="Cambiar Nombre"
            icon="pi pi-user-edit"
            size="small"
            severity="secondary"
            text
            onClick={() => setUsername('')}
          />
        </div>
      )}

      <Divider />

      {isConnected ? (
        <div className="p-d-flex p-flex-column" style={{ height: '400px' }}>
          <div className="p-flex-1 p-overflow-auto p-mb-2" style={{ maxHeight: '300px', border: '1px solid #ccc' }}>
            {messages.map((msg, index) => (
              <div key={index} className="p-p-2 p-text-left">
                {msg}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-d-flex p-ai-center">
            <InputText
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Escribe un mensaje..."
              className="p-flex-1 p-mr-2"
              disabled={!isConnected}
            />
            <Button
              label="Enviar"
              icon="pi pi-send"
              onClick={sendMessage}
              disabled={!inputValue.trim() || !isConnected}
            />
          </div>
        </div>
      ) : (
        <div className="p-d-flex p-ai-center p-jc-center" style={{ height: '300px' }}>
          <p>Por favor, ingresa un nombre para unirte al chat.</p>
        </div>
      )}
    </Card>
  );
}

