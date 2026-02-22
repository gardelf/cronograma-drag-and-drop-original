# 📅 Daily Agenda Automation System

Sistema automatizado para organizar eventos de calendario y tareas de Todoist en una agenda diaria optimizada usando ChatGPT.

## 🎯 Estado del Proyecto

### ✅ Completado
- [x] Integración con Todoist API (funcionando correctamente)
- [x] Cliente de Todoist para obtener tareas del día
- [x] Servidor web Flask con múltiples endpoints
- [x] Sistema de procesamiento con ChatGPT
- [x] Módulo de envío por email
- [x] Tabla HTML de respaldo (fallback)
- [x] Sistema de configuración con variables de entorno
- [x] Scripts de prueba

### ⏳ Pendiente
- [ ] Validar API Key de OpenAI (esperando nueva clave)
- [ ] Configurar SMTP para envío de emails
- [ ] Configurar atajo de iPhone para enviar eventos
- [ ] Programar ejecución diaria automática
- [ ] Desplegar en Railway

## 📁 Estructura del Proyecto

```
daily-agenda-automation/
├── config.py              # Gestión de configuración
├── todoist_client.py      # Cliente API de Todoist
├── chatgpt_processor.py   # Procesamiento con ChatGPT
├── email_sender.py        # Envío de emails
├── server.py              # Servidor web Flask
├── test_manual.py         # Script de prueba manual
├── test_openai.py         # Test de API Key de OpenAI
├── .env                   # Variables de entorno (NO subir a git)
├── .env.example           # Ejemplo de configuración
└── README.md              # Este archivo
```

## 🔧 Configuración Actual

### Todoist
- ✅ API Token configurado
- ✅ Conexión verificada
- ✅ Obtiene tareas del día correctamente

### OpenAI
- ⏳ API Key pendiente de validación
- ⏳ Esperando nueva clave del usuario

### Email
- ⏳ SMTP no configurado aún
- Destinatario: gardel.f@gmail.com

### Calendario
- Método: iPhone Shortcuts (JSON POST)
- ⏳ Atajo pendiente de configuración

## 🚀 Endpoints del Servidor

- `GET /health` - Health check
- `POST /process-agenda` - Procesar agenda diaria
- `GET /test-todoist` - Probar conexión con Todoist
- `GET /test-email` - Probar envío de email
- `GET /manual-run` - Ejecutar manualmente sin eventos de calendario

## 📝 Próximos Pasos

1. Obtener API Key válida de OpenAI
2. Configurar SMTP para Gmail
3. Crear atajo en iPhone
4. Probar flujo completo
5. Preparar para despliegue en Railway

## 🔐 Seguridad

- Token secreto para autenticación: `daily-agenda-secret-2024`
- Todas las API keys están en `.env` (no versionado)
- Usar HTTPS en producción

## 📧 Contacto

Usuario: gardel.f@gmail.com
