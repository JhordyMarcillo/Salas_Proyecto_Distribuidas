# Salas_Proyecto_Distribuidas# Documentación Unificada del Proyecto AquaChat (Salas_Proyecto_Distribuidas)

Este proyecto consiste en un sistema distribuido de salas de chat en tiempo real (**AquaChat**), compuesto por un **Frontend** desarrollado con React y un **Backend** construido con Flask. Integra autenticación, gestión de salas y mensajería en tiempo real mediante Socket.IO y persistencia de datos con MongoDB.

---

## 1. Arquitectura General

El sistema se divide en dos componentes principales que se comunican mediante servicios **REST** para la gestión de datos (salas, historial de mensajes) y **WebSockets (Socket.IO)** para la funcionalidad en tiempo real (mensajería, presencia, autenticación).

### A. Frontend (AquaChat)

Aplicación web (SPA) que proporciona la interfaz de usuario para gestionar salas de chat en tiempo real.
* **Base:** Vite 5 + React 18 + TypeScript.
* **Estilo:** **Tailwind CSS 3**, `@shadcn/ui`, y **Radix UI**.
* **Data Fetching:** **TanStack Query 5** para datos REST (`/rooms`, `/messages`).
* **Tiempo Real:** **Socket.IO client 4** para la capa de autenticación, presencia y mensajería.
* **Persistencia de Estado:** **LocalStorage** maneja `chat_token`, `chat_user`, `is_admin`, y `pin_<room>`.

### B. Backend

Servidor que maneja la lógica de negocio, autenticación, y persistencia.
* **Base:** **Python 3.8+** y **Flask 2.2.3**.
* **Tiempo Real:** **Flask-SocketIO 5.3.0**.
* **Base de Datos:** **MongoDB** (v4.0+) a través de `flask-pymongo`.
* **Seguridad:** Autenticación con **JWT** (`pyjwt`) y hasheo de contraseñas con **bcrypt** (`flask-bcrypt`).
* **Usuario por defecto:** Crea automáticamente el usuario administrador `admin`/`admin123` si la base de datos está vacía.

---

## 2. Tecnologías Clave

### Frontend
* Vite 5, React 18, TypeScript
* Tailwind CSS, Shadcn UI, Radix UI
* TanStack Query 5
* Socket.IO client 4
* React Router 6
* Formularios/Validación: React Hook Form + Zod

### Backend
* Python 3.8+, Flask 2.2.3
* Flask-SocketIO 5.3.0
* MongoDB (v4.2.0)
* PyJWT 2.10.1, Flask-Bcrypt 1.0.1
* Flask-CORS 3.1.1, Flask-PyMongo 2.3.0

---

## 3. Configuración y Variables de Entorno

Ambos componentes se levantan en el puerto `5000` por defecto.

### A. Backend - Requisitos y Configuración

| Variable de Entorno | Descripción | Default (Si no se define) |
| :--- | :--- | :--- |
| `MONGO_URI` | URI de conexión a MongoDB. | `mongodb://localhost:27017/Proyecto_Distribuidas` |
| `JWT_SECRET` | Secreto para la firma de tokens JWT. | `TOKEN_SUPER_SECRETO_SEGURO` |
| `JWT_EXPIRE_HOURS` | Horas de expiración del token. | `20` |

**Pasos de Instalación:**
1.  Clonar el repositorio y moverse a la carpeta `backend`.
2.  Crear y activar un entorno virtual.
3.  Instalar dependencias: `pip install -r requirements.txt`.
4.  Levantar el servidor: `python server.py` (Se inicia en `http://localhost:5000`).

### B. Frontend - Requisitos y Configuración

| Variable de Entorno | Descripción | Default (Si no se define) |
| :--- | :--- | :--- |
| `VITE_API_URL` | URL base del backend que expone REST y Socket.IO. | `http://localhost:5000` |

**Pasos de Instalación:**
1.  Moverse a la carpeta `frontend`.
2.  Instalar dependencias: `npm install`.
3.  Ejecución en desarrollo: `npm run dev` (Vite sirve la app en `http://localhost:5173/`).
4.  Compilación para producción: `npm run build`.

---

## 4. Flujos Funcionales y Comunicación

La comunicación entre el Frontend y el Backend utiliza endpoints REST para la gestión de datos y eventos Socket.IO para la interacción en tiempo real.

### A. Flujo de Autenticación (Login / Register)

El Frontend maneja formularios controlados y notifica con Sonner. El Backend maneja la lógica de negocio a través de Socket.IO.

| Componente | Tipo de Comunicación | Evento/Endpoint | Respuestas Clave (Backend) |
| :--- | :--- | :--- | :--- |
| **Frontend** | Socket.IO | `register` o `login` | `register_success` / `login_success` (con **JWT**) |
| **Persistencia** | LocalStorage | Token y usuario. | N/A |

### B. Flujo de Salas y Mensajería

| Acción | Comunicación | Backend Endpoint/Evento | Frontend Acciones Clave |
| :--- | :--- | :--- | :--- |
| **Listar Salas** | REST | `GET /rooms` | Obtiene la lista, permite filtrar en el Lobby. |
| **Crear Sala** | REST | `POST /rooms` | Habilitado si el usuario es `is_admin`. Permite definir PIN, tipo, y límites. |
| **Unirse a Sala** | Socket.IO | `join` | Solicita y almacena **PIN obligatorio** localmente (`pin_<room>`). |
| **Historial** | REST | `GET /rooms/<room>/messages` | Carga los últimos 100 mensajes. |
| **Mensaje** | Socket.IO | `send_message` | Emite mensajes de texto o multimedia (imágenes/archivos) según el tipo de sala. |
| **Presencia** | Socket.IO | `user_joined`, `user_left`, `status` | Actualiza el listado local de usuarios conectados y muestra notificaciones. |

---

## 5.  Detalles de Eventos WebSocket del Backend

El Backend (Flask-SocketIO) utiliza los siguientes eventos clave:

| Evento de Emisión (Cliente a Servidor) | Payload | Eventos de Recepción (Servidor a Cliente) |
| :--- | :--- | :--- |
| `register` | `{ username, password }` | `register_success` o `register_error` |
| `login` | `{ username, password }` | `login_success` o `login_error` |
| `join` | `{ token, room, [pin] }` | `join_success` o `join_error`. **Broadcast:** `user_joined` |
| `leave` | `{ token, room }` | `leave_success` o `leave_error`. **Broadcast:** `user_left` |
| `send_message` | `{ token, room, msg, [attachment] }` | `message` (broadcast a la sala) o `msg_error` |

---

## 6. Seguridad y Notas

* Las contraseñas se almacenan **hasheadas con bcrypt**.
* La autenticación se basa en **tokens JWT** con expiración configurable (default: 20 horas).
* **Acceso a salas:** Los usuarios solo pueden enviar mensajes a salas en las que están unidos.
* **Archivos:** El Frontend impone límites de 5 MB para imágenes y 10 MB para archivos genéricos, solo si la sala es de tipo `multimedia`.

---

