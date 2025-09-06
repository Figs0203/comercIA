# Configuración de Telegram para ComercIA

## 📋 **Requisitos Previos**

1. **Bot de Telegram**: Necesitas crear un bot en Telegram
2. **Token del Bot**: Obtener el token de @BotFather
3. **Chat ID**: ID del canal o grupo a monitorear

## 🤖 **Crear un Bot de Telegram**

1. Abre Telegram y busca `@BotFather`
2. Envía el comando `/newbot`
3. Sigue las instrucciones para crear tu bot
4. Guarda el **token** que te proporciona

## 🔧 **Configuración en ComercIA**

### **1. Variables de Entorno**

Agrega a tu archivo `.env` o variables de entorno:

```bash
TELEGRAM_BOT_TOKEN=tu_token_aqui
```

### **2. Configurar Fuentes de Telegram**

```bash
# Listar fuentes existentes
python manage.py setup_telegram --list

# Agregar un canal/grupo
python manage.py setup_telegram --chat-id "-1001234567890" --name "Canal de Ventas"

# Eliminar una fuente
python manage.py setup_telegram --remove 1
```

### **3. Obtener Chat ID**

Para obtener el ID de un canal o grupo:

1. **Método 1**: Usar @userinfobot
   - Agrega el bot a tu canal/grupo
   - El bot te mostrará el Chat ID

2. **Método 2**: Usar la API de Telegram
   ```bash
   curl "https://api.telegram.org/bot<TU_TOKEN>/getUpdates"
   ```

3. **Método 3**: Usar @RawDataBot
   - Envía un mensaje al bot
   - Te mostrará toda la información del chat

## 🚀 **Probar la Integración**

```bash
# Probar obtención de mensajes (simulación)
python manage.py fetch_social --platform telegram --dry-run

# Probar obtención real
python manage.py fetch_social --platform telegram
```

## 📝 **Tipos de Chat ID**

- **Grupos**: Comienzan con `-` (ej: `-1001234567890`)
- **Canales**: Comienzan con `-100` (ej: `-1001234567890`)
- **Chats privados**: Números positivos (ej: `123456789`)

## ⚠️ **Limitaciones**

1. **Bot debe ser admin**: El bot debe ser administrador del canal/grupo
2. **Límites de API**: Telegram tiene límites de rate limiting
3. **Solo mensajes de texto**: Por ahora solo procesa mensajes de texto

## 🔍 **Monitoreo**

Los mensajes se almacenan en la base de datos y se pueden ver en:
- **Admin de Django**: `/admin/social_ingestion/socialpost/`
- **Vista de recomendaciones**: `/recomendaciones/`

## 🛠️ **Solución de Problemas**

### **Error: "Chat not found"**
- Verifica que el bot sea admin del canal
- Confirma que el Chat ID sea correcto

### **Error: "Unauthorized"**
- Verifica que el token del bot sea correcto
- Asegúrate de que el bot esté activo

### **No se obtienen mensajes**
- Verifica que haya mensajes recientes en el canal
- Confirma que los mensajes contengan texto
- Revisa los logs del comando `fetch_social`
