# Salas Proyecto Distribuidas - Backend

Backend para sistema de salas de chat en tiempo real desarrollado con Flask, SocketIO y MongoDB. Permite registro de usuarios, autenticación JWT, gestión de salas y mensajería en tiempo real.

Este documento describe cómo instalar y ejecutar el backend, las variables de entorno importantes, los endpoints HTTP y eventos WebSocket disponibles, así como observaciones de seguridad y problemas conocidos detectados en `server.py`.

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.8+** (recomendado 3.9 o superior)
- **MongoDB** (versión 4.0 o superior)
  - Puedes instalarlo localmente o usar MongoDB Atlas (cloud)
- **pip** (gestor de paquetes de Python)
- **Git** (para clonar el repositorio)

## 🚀 Instalación y Configuración

### Paso 1: Clonar el repositorio

```powershell
cd path\to\Salas_Proyecto_Distribuidas\backend
```

### Paso 2: Crear un entorno virtual (recomendado)

Es recomendable usar un entorno virtual para aislar las dependencias del proyecto:

**Windows:**
```powershell
python -m venv venv
venv\Scripts\Activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Paso 3: Instalar dependencias

```powershell
pip install -r requirements.txt
```