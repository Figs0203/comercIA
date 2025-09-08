# 🛒 ComercIA: Plataforma de Comercio con IA

**ComercIA** es una plataforma de comercio electrónico desarrollada en **Django** que integra **inteligencia artificial** para mejorar la experiencia de compra y venta en el entorno universitario.  
El sistema se conecta con **redes sociales (X/Twitter)** y utiliza **Google Gemini 1.5 Flash** para procesar lenguaje natural, detectando publicaciones relevantes y generando recomendaciones personalizadas para los usuarios.

---

## ✨ Características principales

### 👤 Para Compradores
- 🔍 **Búsqueda inteligente** en lenguaje natural con IA.  
- ⭐ Sistema de **favoritos** personalizado.  
- 🎯 **Recomendaciones basadas en Twitter** (últimas publicaciones).  
- 🎨 Interfaz **responsiva y moderna**.  
- 💬 Contacto directo con vendedores vía **WhatsApp**.  

### 🛍️ Para Vendedores
- 📦 **Gestión completa de productos** con categorías.  
- 🕒 **Horarios de atención** en el perfil.  
- 💬 Sistema de **comentarios y calificaciones**.  
- 📱 Integración con **WhatsApp** para ventas rápidas.  

### 🛠️ Para Administradores
- 📊 Monitoreo de ingesta de redes sociales.  
- 🔐 Gestión de cuentas vinculadas a Twitter.  
- 📑 Análisis de consultas procesadas por IA.  
- ⚙️ Panel de administración de Django completo.  

---

## 🏗️ Arquitectura Técnica

- **Backend:** Django 5.1.6 con arquitectura MVT  
- **Base de Datos:** SQLite 
- **Frontend:** Bootstrap 5 + JavaScript Vanilla  
- **APIs Externas:**  

| **API** | **Tipo** | **Estado** | **Propósito** |
|---------|----------|------------|---------------|
| **Google Gemini 1.5 Flash** | IA/ML | ✅ **Activa** | Procesamiento de lenguaje natural |
| **X API v2** | Social Media | ✅ **Activa** | Ingesta de tweets |
| **Telegram Bot API** | Social Media | ✅ **Activa** | Ingesta de mensajes |
| **Ngrok API** | Desarrollo | ✅ **Activa** | Túneles públicos |
| **Render.com API** | Despliegue | ✅ **Activa** | Hosting en la nube |

- **Despliegue:** Render.com con soporte para ngrok  

---

## 📂 Modelos principales

- `Product` → Catálogo de productos con precios, categorías e imágenes.  
- `SellerProfile` → Perfiles de vendedores con contacto vía WhatsApp.  
- `SocialPost` → Publicaciones de X categorizadas automáticamente.  
- `ChatQuery` → Historial de consultas procesadas por IA.  
- `Comment` → Sistema de comentarios y calificaciones.  
- `Favorite` → Lista de favoritos por usuario.  

---

## 🚀 Instalación y ejecución

### 🔧 Requisitos
- Python 3.10+  
- Django 5.1.6  
- Token de acceso para **X API v2**  
- Credenciales de **Google Gemini API**  

### ⚙️ Pasos de instalación
```bash
# Clonar el repositorio
git clone https://github.com/Figs0203/comercIA.git
cd comercIA

# Crear entorno virtual
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Instalar dependencias
pip install -r requirements.txt

# Migrar base de datos
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor de desarrollo
python manage.py runserver
````

---

## Variables de entorno

Crear un archivo `.env` en la raíz (no se sube a Git) basado en `.env.example`.

Ejemplo:

```
SECRET_KEY=pon_aqui_una_clave_segura
DEBUG=1

# Gemini
GEMINI_API_KEY=tu_api_key

# X (Twitter)
X_BEARER_TOKEN=tu_bearer_token
X_USER_ID=1234567890
# O alternativamente
# X_USERNAME=mi_usuario
X_MAX_RESULTS=3

# Telegram
TELEGRAM_BOT_TOKEN=token_de_telegram
```

---

## 📘 Documentación del proyecto

El proyecto cuenta con una **wiki** donde se encuentran los documentos oficiales:

* [📑 Entregable](../../wiki/Entregable)
* [🎨 Guía de estilo de programación](../../wiki/Guía-de-estilo-de-programación)
* [⚙️ Reglas de programación](../../wiki/Reglas-de-programación)

---

## 👥 Equipo de desarrollo

* Agustín Figueroa
* Jesús Gómez Ávila
* Tomás Lopera Londoño

---

## 📜 Licencia

Este proyecto es de uso académico en el marco de la asignatura de **Arquitectura de Software**.
El código puede ser reutilizado con fines educativos y de investigación.

