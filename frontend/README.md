# AquaChat Frontend

Aplicación web construida con Vite + React + TypeScript para gestionar salas de chat en tiempo real dentro del proyecto **Salas_Proyecto_Distribuidas**. Integra autenticación mediante Socket.IO, consumo de servicios REST para administrar salas y una experiencia moderna basada en componentes de Shadcn UI con Tailwind CSS.

## Tabla de contenido

1. [Tecnologías y dependencias](#tecnologías-y-dependencias)
2. [Arquitectura general](#arquitectura-general)
3. [Estructura de carpetas](#estructura-de-carpetas)
4. [Flujos funcionales](#flujos-funcionales)
5. [Configuración del entorno](#configuración-del-entorno)
6. [Variables de entorno](#variables-de-entorno)
7. [Scripts disponibles](#scripts-disponibles)
8. [Recursos compartidos y utilidades](#recursos-compartidos-y-utilidades)
9. [Guía de estilos y UX](#guía-de-estilos-y-ux)
10. [Pruebas y próximos pasos](#pruebas-y-próximos-pasos)

---

## Tecnologías y dependencias

- **Vite 5 + React 18 + TypeScript**: base del proyecto SPA.
- **Tailwind CSS 3 + @shadcn/ui + Radix UI**: sistema de diseño y componentes accesibles.
- **TanStack Query 5**: manejo de fetching/cache para datos REST (`/rooms`, `/messages`).
- **Socket.IO client 4**: capa en tiempo real para autenticación, presencia y mensajería.
- **React Router 6**: control de rutas públicas (`/login`, `/register`) y privadas (`/lobby`, `/sala/:id`).
- **React Hook Form + Zod (preinstalados)**: validaciones declarativas (actualmente se usa manejo manual en formularios principales).
- **Sonner + sistema propio de toast**: notificaciones inmediatas y personalizadas.

## Arquitectura general

- **Entrypoint**: `src/main.tsx` monta `App` sobre Vite, inyectando estilos globales desde `src/index.css`.
- **App shell**: `src/App.tsx` configura `QueryClientProvider`, proveedor de tooltips y el router principal.
- **Comunicación con backend**:
  - **REST** vía `fetch` usando la constante `apiUrl` expuesta desde `src/lib/socket.ts`.
  - **Tiempo real** con `initSocket()`/`getSocket()` que encapsulan la conexión, reconexiones y autenticación por token.
- **Estado y persistencia**:
  - LocalStorage maneja `chat_token`, `chat_user`, `is_admin` y `pin_<room>`.
  - Hooks locales controlan el UI state (formularios, filtros, adjuntos).
- **UI y accesibilidad**:
  - Componentes reutilizables en `src/components/ui/*` (botones, inputs, diálogos, etc.) basados en Shadcn.
  - Animaciones y estilos personalizados definidos en `src/index.css` y `tailwind.config.ts`.

## Estructura de carpetas

```
frontend/
├── public/              # Assets estáticos servidos por Vite
├── src/
│   ├── components/
│   │   ├── NavLink.tsx
│   │   └── ui/          # Catálogo Shadcn (button, input, toast, etc.)
│   ├── hooks/           # Hooks compartidos (use-toast, useIsMobile)
│   ├── lib/
│   │   ├── socket.ts    # Cliente Socket.IO y helper REST
+│   │   └── utils.ts    # utilidades como cn()
│   ├── pages/           # Páginas principales (Login, Register, Lobby, ChatRoom, NotFound)
│   ├── types/           # Tipados adicionales (ej. sonner.d.ts)
│   ├── App.tsx          # Shell con router
│   └── main.tsx         # Punto de entrada
├── components.json      # Configuración de Shadcn
├── tailwind.config.ts   # Design tokens/temas
├── tsconfig*.json       # Configuración TypeScript
└── vite.config.ts       # Config Vite + plugin React SWC
```

## Flujos funcionales

### 1. Autenticación (Login / Register)
- Formularios controlados (`src/pages/Login.tsx`, `Register.tsx`) validan campos mínimos y notifican con Sonner.
- Eventos Socket.IO:
  - `login`: recibe `{ username, password }` y espera `login_success` (token, `is_admin`) o `login_error`.
  - `register`: recibe `{ username, password }` y espera `register_success` con token.
- Tras autenticarse:
  - Se almacena `chat_token` y `chat_user`.
  - Se re-inicializa el socket con `initSocket(token)` para incluir el token en el handshake.
  - Se redirige al `/lobby`.

### 2. Lobby de salas (`src/pages/Lobby.tsx`)
- Obtiene la lista de salas con `GET {apiUrl}/rooms`.
- Permite filtrar por nombre, ver descripción y número estimado de miembros.
- Si `is_admin` es `true`, se habilita el formulario para crear salas:
  - Parámetros: nombre, descripción, tipo (`text` o `multimedia`), PIN (mínimo 4 dígitos) y límite de archivos (MB).
  - Envía `POST {apiUrl}/rooms` con token en `Authorization: Bearer`.
- Las tarjetas redirigen a `/sala/:name` (nombre codificado en URL).

### 3. Sala de chat (`src/pages/ChatRoom.tsx`)
- **PIN obligatorio**: al entrar se solicita y almacena localmente (`pin_<room>`). Si el backend rechaza el PIN (`join_error` con mensaje correspondiente) se limpia y se vuelve a mostrar el diálogo.
- **Inicialización**:
  - Consulta `/rooms` para conocer el tipo (texto/multimedia).
  - Consulta `/rooms/{room}/messages` para cargar historial (texto, imágenes base64, archivos).
  - Establece listeners Socket.IO para `message`, `status`, `user_joined`, `user_left`, `user_disconnected`.
  - Emite `join` enviando `token`, `room` y `pin`.
- **Mensajería**:
  - Sólo se permite adjuntar imágenes/archivos si la sala es `multimedia`. Límites: 5 MB imágenes, 10 MB archivos genéricos.
  - Los mensajes incluyen previsualización, descarga (para archivos) y marca de tiempo local.
  - Las notificaciones con `useToast()` avisan de mensajes entrantes y de la entrada/salida de usuarios.
- **Presencia**:
  - Los eventos `status` y `user_*` actualizan el listado local de usuarios conectados mostrado en el encabezado.
  - Al desmontar, se emite `leave` automáticamente.

### 4. Manejo de errores
- Todos los `fetch` y emisiones relevantes hacen `toast.error` cuando falla la operación.
- `NotFound` registra en consola las rutas inexistentes.

## Configuración del entorno

1. **Prerequisitos**
   - Node.js 18+ (recomendado 20 LTS).
   - npm 9+ (o pnpm/bun si prefieres, actualiza los scripts en consecuencia).

2. **Instalación**

```bash
npm install
```

3. **Ejecución en desarrollo**

```bash
npm run dev
# Vite sirve la app en http://localhost:5173/
```

4. **Compilación para producción**

```bash
npm run build
npm run preview   # previsualizar el build
```

5. **Linter**

```bash
npm run lint
```

## Variables de entorno

`VITE_API_URL` es la única variable requerida. Define la URL base del backend Express/Fastify (o equivalente) que expone los endpoints REST y sirve Socket.IO.

Ejemplo de `.env`:

```
VITE_API_URL=http://localhost:5000
```

> Si no se define, el cliente intenta conectarse a `http://localhost:5000` (ver `src/lib/socket.ts`).

## Scripts disponibles

| Script        | Descripción                                                                 |
| ------------- | --------------------------------------------------------------------------- |
| `npm run dev` | Levanta Vite en modo HMR.                                                   |
| `npm run build` | Genera la versión optimizada en `dist/`.                                 |
| `npm run build:dev` | Build en modo development (útil para depurar SSR/CDN).               |
| `npm run preview` | Sirve el contenido de `dist/` para smoke tests.                        |
| `npm run lint` | Ejecuta ESLint sobre todo el código fuente.                               |

## Recursos compartidos y utilidades

- `src/lib/socket.ts`: controla la instancia única de Socket.IO, reconexiones y helpers (`emit`, `on`, `off`).
- `src/hooks/use-toast.ts`: implementación personalizada de colas de toast (inspirada en Shadcn) con límite configurable.
- `src/hooks/use-mobile.tsx`: helper para detectar `isMobile` según breakpoint 768px.
- `src/lib/utils.ts`: función `cn` para combinar clases Tailwind de forma segura.
- `src/types/sonner.d.ts`: tipado mínimo para el paquete `sonner` (cuando no exporta tipos completos).

## Guía de estilos y UX

- **Tailwind** gobierna la mayor parte de las clases utilitarias; las personalizaciones globales viven en `src/index.css`.
- **Temas y colores**: configurados en `tailwind.config.ts` y según tokens generados por Shadcn (`primary`, `accent`, `background`, etc.).
- **Componentes reutilizables**: importa desde `@/components/ui/<componente>` para mantener consistencia (botones, inputs, scroll-area, dialog, toast, etc.).
- **Animaciones**: clases utilitarias (`animate-fade-in`, `glow-button`, `chat-bubble-user`) definidas también en `index.css`.

## Pruebas y próximos pasos

- Actualmente no existen pruebas automatizadas. Se recomienda:
  - Añadir tests de componentes críticos (Login, Lobby, ChatRoom) usando Vitest + React Testing Library.
  - Integrar pruebas E2E (Playwright o Cypress) para validar flujos de autenticación y mensajería.
- Considerar un guard de ruta para evitar accesos sin token.
- Añadir manejo centralizado de errores y loading states con TanStack Query o Zustand para mejorar la experiencia.

---

Para dudas adicionales sobre el frontend o para proponer mejoras, documenta los cambios en este README y mantén sincronizada la configuración con el backend distribuido. ¡Felices commits!
