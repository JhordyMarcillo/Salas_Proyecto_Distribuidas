import { io, type Socket } from "socket.io-client";

let socket: Socket | null = null;
let currentToken: string | null = null;

const getApiUrl = () => {
  return (import.meta.env.VITE_API_URL as string) || "http://localhost:5000";
};

export function initSocket(token?: string) {
  const url = getApiUrl();

  // si ya hay socket y el token no cambió, devolverlo
  if (socket && token === currentToken) return socket;

  // si hay socket pero token cambió, desconectar primero
  if (socket) {
    try { socket.disconnect(); } catch (e) { /* ignore */ }
    socket = null;
  }

  socket = io(url, {
    transports: ["websocket", "polling"],
    auth: token ? { token } : {},
    autoConnect: true,
    reconnectionAttempts: 3,
  });

  currentToken = token ?? null;

  // logs mínimos para depuración
  socket.on("connect", () => {
    // eslint-disable-next-line no-console
    console.log("[socket] connected", socket?.id, "token present:", !!currentToken);
  });
  socket.on("connect_error", (err: any) => {
    // eslint-disable-next-line no-console
    console.warn("[socket] connect_error", err && err.message ? err.message : err);
  });

  return socket;
}

export function connectWithStoredToken() {
  const t = localStorage.getItem("chat_token");
  return initSocket(t ?? undefined);
}

export function disconnectSocket() {
  if (socket) {
    try { socket.disconnect(); } catch (e) { /* ignore */ }
    socket = null;
  }
}

export function getSocket() {
  return socket;
}

export function emit(event: string, data?: any) {
  if (!socket) return;
  socket.emit(event, data);
}

export function on(event: string, handler: (...args: any[]) => void) {
  if (!socket) return;
  socket.on(event, handler);
}

export function off(event: string, handler?: (...args: any[]) => void) {
  if (!socket) return;
  if (handler) socket.off(event, handler);
  else socket.off(event);
}

export const apiUrl = getApiUrl();
