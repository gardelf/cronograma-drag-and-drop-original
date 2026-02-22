# 🚀 Despliegue en Railway - Sistema de Cronograma Automatizado

## 📋 Requisitos Previos

1. Cuenta en [Railway.app](https://railway.app)
2. Token de API de Todoist
3. Credenciales de iCloud (usuario y contraseña específica de app)

---

## 🔧 Pasos de Despliegue

### **1. Crear Proyecto en Railway**

1. Ve a [Railway.app](https://railway.app)
2. Click en "New Project"
3. Selecciona "Deploy from GitHub repo" o "Empty Project"

### **2. Conectar Repositorio (Opción A)**

Si tienes el código en GitHub:
1. Conecta tu cuenta de GitHub
2. Selecciona el repositorio
3. Railway detectará automáticamente los archivos de configuración

### **3. Desplegar desde CLI (Opción B)**

Si prefieres usar la CLI de Railway:

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Inicializar proyecto
cd /home/ubuntu/daily-agenda-automation
railway init

# Desplegar
railway up
```

### **4. Configurar Variables de Entorno**

En el dashboard de Railway, ve a "Variables" y añade:

```
ICLOUD_USERNAME=gardel.f@gmail.com
ICLOUD_APP_PASSWORD=ewyy-vmnp-mian-aifq
TODOIST_API_TOKEN=tu_token_todoist_aqui
```

**⚠️ IMPORTANTE:** Reemplaza `tu_token_todoist_aqui` con tu token real de Todoist.

### **5. Verificar Despliegue**

1. Railway asignará automáticamente una URL pública
2. Accede a la URL para verificar que el cronograma se carga
3. Verifica el endpoint de health: `https://tu-app.railway.app/health`

---

## ⏰ Configurar Cron Job para Generación Diaria

Railway no tiene cron jobs nativos, pero hay varias opciones:

### **Opción 1: Railway Cron (Recomendado)**

1. En el dashboard de Railway, ve a tu proyecto
2. Click en "New" → "Cron Job"
3. Configura:
   - **Schedule:** `30 6 * * *` (6:30 AM diario)
   - **Command:** `python3.11 cronograma_generator_v7_5.py`

### **Opción 2: Servicio Externo (GitHub Actions)**

Crear archivo `.github/workflows/daily-cronograma.yml`:

```yaml
name: Generate Daily Cronograma

on:
  schedule:
    - cron: '30 6 * * *'  # 6:30 AM UTC (7:30 AM Madrid)
  workflow_dispatch:  # Permite ejecución manual

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Railway Deployment
        run: |
          curl -X POST https://tu-app.railway.app/generate-cronograma \
            -H "Content-Type: application/json"
```

### **Opción 3: Servicio de Cron Externo**

Usar servicios como:
- [cron-job.org](https://cron-job.org)
- [EasyCron](https://www.easycron.com)
- [Cronitor](https://cronitor.io)

Configurar para llamar a: `https://tu-app.railway.app/generate-cronograma`

---

## 🔍 Endpoints Disponibles

| Endpoint | Método | Descripción |
|---|---|---|
| `/` | GET | Cronograma HTML principal |
| `/health` | GET | Health check del servidor |
| `/new-events` | GET | Lista de eventos nuevos (JSON) |
| `/copy-and-regenerate` | POST | Copiar evento y regenerar |
| `/ignore-event` | POST | Ignorar evento |

---

## 📊 Monitoreo y Logs

### **Ver Logs en Railway:**

1. Dashboard → Tu Proyecto → "Deployments"
2. Click en el deployment activo
3. Ver logs en tiempo real

### **Comandos útiles con Railway CLI:**

```bash
# Ver logs en tiempo real
railway logs

# Ver estado del servicio
railway status

# Abrir dashboard
railway open
```

---

## 🐛 Troubleshooting

### **Problema: "Application failed to respond"**

**Solución:**
- Verificar que el puerto está configurado correctamente
- Railway usa la variable `PORT` automáticamente
- Asegúrate de que `web_server.py` usa `os.getenv('PORT', 8000)`

### **Problema: "Module not found"**

**Solución:**
- Verificar que `requirements.txt` está completo
- Railway instala dependencias automáticamente

### **Problema: "Calendar connection failed"**

**Solución:**
- Verificar variables de entorno `ICLOUD_USERNAME` y `ICLOUD_APP_PASSWORD`
- Asegurarse de usar contraseña específica de app, no la contraseña principal

### **Problema: "Database locked"**

**Solución:**
- Railway usa almacenamiento efímero por defecto
- Considerar usar Railway Volumes para persistencia
- O usar base de datos externa (Railway PostgreSQL)

---

## 💾 Persistencia de Datos

Railway usa almacenamiento efímero por defecto. Para persistir la base de datos:

### **Opción 1: Railway Volumes**

```bash
# Crear volumen
railway volume create cronograma-db

# Montar en /data
railway volume attach cronograma-db /data

# Actualizar código para usar /data/events_tracker.db
```

### **Opción 2: PostgreSQL en Railway**

1. Añadir servicio PostgreSQL en Railway
2. Migrar de SQLite a PostgreSQL
3. Usar variable `DATABASE_URL` automáticamente

---

## 🔄 Actualizar Despliegue

### **Con GitHub:**
- Push a la rama principal
- Railway despliega automáticamente

### **Con Railway CLI:**
```bash
railway up
```

---

## 💰 Costos

Railway ofrece:
- **Plan Hobby:** $5/mes + uso
- **Plan Pro:** $20/mes + uso
- 500 horas gratis al mes en plan Hobby

**Estimación para este proyecto:**
- ~720 horas/mes (24/7)
- Uso mínimo de CPU/RAM
- **Costo estimado:** $5-10/mes

---

## 📞 Soporte

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **Railway Status:** https://status.railway.app

---

## ✅ Checklist de Despliegue

- [ ] Proyecto creado en Railway
- [ ] Variables de entorno configuradas
- [ ] Código desplegado exitosamente
- [ ] URL pública accesible
- [ ] Health check respondiendo
- [ ] Cronograma visible en navegador
- [ ] Eventos nuevos detectándose
- [ ] Botones de copiar/ignorar funcionando
- [ ] Cron job configurado para 6:30 AM
- [ ] Logs monitoreándose

---

**¡Listo para producción!** 🚀
