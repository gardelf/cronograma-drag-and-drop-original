# 🚀 Guía Paso a Paso: Desplegar en Railway

## 📦 Método 1: Despliegue Directo desde Railway (MÁS FÁCIL)

### **Paso 1: Crear cuenta en Railway**

1. Ve a [railway.app](https://railway.app)
2. Click en "Login" o "Start a New Project"
3. Regístrate con GitHub, Google o email

### **Paso 2: Crear nuevo proyecto**

1. En el dashboard de Railway, click en **"New Project"**
2. Selecciona **"Deploy from GitHub repo"**
3. Si es tu primera vez, autoriza Railway para acceder a GitHub
4. Click en **"Deploy from GitHub repo"** de nuevo

### **Paso 3: Subir código a GitHub**

**Opción A: Crear repositorio nuevo en GitHub**

1. Ve a [github.com/new](https://github.com/new)
2. Nombre del repositorio: `daily-agenda-automation`
3. Visibilidad: **Private** (recomendado)
4. NO marques "Initialize with README"
5. Click en **"Create repository"**

**Opción B: Descargar y subir código**

He preparado un archivo comprimido con todo el código:
- **Ubicación:** `/home/ubuntu/daily-agenda-automation.tar.gz`
- **Tamaño:** 115KB

Puedes descargarlo y extraerlo en tu Mac, luego:

```bash
# En tu Mac, después de extraer el archivo
cd daily-agenda-automation
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/daily-agenda-automation.git
git push -u origin main
```

### **Paso 4: Conectar Railway con GitHub**

1. En Railway, selecciona tu repositorio `daily-agenda-automation`
2. Railway detectará automáticamente:
   - `Procfile` → Comando de inicio
   - `requirements.txt` → Dependencias Python
   - `railway.json` → Configuración específica
3. Click en **"Deploy"**

### **Paso 5: Configurar Variables de Entorno**

**MUY IMPORTANTE:** Antes de que funcione, debes configurar estas variables:

1. En Railway, ve a tu proyecto
2. Click en **"Variables"** (o el ícono de engranaje)
3. Añade estas 3 variables:

```
ICLOUD_USERNAME=gardel.f@gmail.com
ICLOUD_APP_PASSWORD=ewyy-vmnp-mian-aifq
TODOIST_API_TOKEN=50ff91ef15761a6727b8b991ac3be61a96f76538
```

4. Click en **"Add"** para cada una
5. Railway redesplegará automáticamente

### **Paso 6: Obtener URL Pública**

1. Después del despliegue, ve a **"Settings"**
2. En la sección **"Networking"**, click en **"Generate Domain"**
3. Railway te dará una URL como: `https://daily-agenda-automation-production.up.railway.app`
4. ¡Esa es tu URL permanente! 🎉

### **Paso 7: Verificar que Funciona**

1. Abre la URL en tu navegador
2. Deberías ver el cronograma HTML
3. Verifica que aparezcan eventos nuevos (si los hay)
4. Prueba los botones "Copiar" e "Ignorar"

---

## 📦 Método 2: Despliegue desde Archivo ZIP (Sin GitHub)

Si no quieres usar GitHub, puedes usar Railway CLI:

### **Paso 1: Instalar Railway CLI en tu Mac**

```bash
# Usando npm (si tienes Node.js instalado)
npm install -g @railway/cli

# O usando Homebrew
brew install railway
```

### **Paso 2: Descargar el código**

1. Descarga el archivo `/home/ubuntu/daily-agenda-automation.tar.gz`
2. Extráelo en tu Mac:
   ```bash
   tar -xzf daily-agenda-automation.tar.gz
   cd daily-agenda-automation
   ```

### **Paso 3: Login en Railway**

```bash
railway login
```

Esto abrirá tu navegador para autenticarte.

### **Paso 4: Inicializar y Desplegar**

```bash
# Crear nuevo proyecto
railway init

# Configurar variables de entorno
railway variables set ICLOUD_USERNAME=gardel.f@gmail.com
railway variables set ICLOUD_APP_PASSWORD=ewyy-vmnp-mian-aifq
railway variables set TODOIST_API_TOKEN=50ff91ef15761a6727b8b991ac3be61a96f76538

# Desplegar
railway up

# Generar dominio público
railway domain
```

---

## ⏰ Configurar Generación Diaria a las 6:30 AM

Railway no tiene cron jobs nativos, pero hay 3 opciones:

### **Opción 1: GitHub Actions (GRATIS y RECOMENDADO)**

1. En tu repositorio de GitHub, crea el archivo `.github/workflows/daily-cronograma.yml`:

```yaml
name: Generar Cronograma Diario

on:
  schedule:
    - cron: '30 5 * * *'  # 6:30 AM Madrid (UTC+1 = 5:30 UTC)
  workflow_dispatch:  # Permite ejecución manual

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger cronograma generation
        run: |
          curl -X POST https://TU-URL.railway.app/generate-cronograma
```

2. Reemplaza `TU-URL.railway.app` con tu URL real
3. Commit y push a GitHub
4. GitHub Actions ejecutará automáticamente cada día

### **Opción 2: Cron-job.org (GRATIS)**

1. Ve a [cron-job.org](https://cron-job.org)
2. Regístrate gratis
3. Crea nuevo cron job:
   - **URL:** `https://TU-URL.railway.app/generate-cronograma`
   - **Schedule:** `30 6 * * *` (6:30 AM)
   - **Timezone:** Europe/Madrid
4. Activa el job

### **Opción 3: Railway Cron (Próximamente)**

Railway está desarrollando soporte nativo para cron jobs. Por ahora, usa las opciones anteriores.

---

## 🔍 Monitoreo y Mantenimiento

### **Ver Logs:**

```bash
# Con Railway CLI
railway logs

# O en el dashboard web
Railway → Tu Proyecto → Deployments → Ver logs
```

### **Actualizar el Código:**

```bash
# Hacer cambios en el código
git add .
git commit -m "Descripción de cambios"
git push

# Railway desplegará automáticamente
```

### **Regenerar Cronograma Manualmente:**

Visita: `https://TU-URL.railway.app/generate-cronograma`

---

## 💰 Costos de Railway

- **Plan Hobby:** $5/mes + uso
- **Incluye:** $5 de créditos gratis al mes
- **Este proyecto usa:** ~$2-3/mes en uso
- **Total estimado:** $5-8/mes

**Alternativa GRATIS:** Render.com o Fly.io tienen planes gratuitos que podrían funcionar.

---

## ✅ Checklist Final

Antes de dar por terminado el despliegue, verifica:

- [ ] Código subido a GitHub (o desplegado con CLI)
- [ ] Proyecto creado en Railway
- [ ] Variables de entorno configuradas (3 variables)
- [ ] Despliegue exitoso (sin errores en logs)
- [ ] URL pública generada
- [ ] Cronograma visible en navegador
- [ ] Eventos nuevos detectándose
- [ ] Botones de copiar/ignorar funcionando
- [ ] Cron job configurado (GitHub Actions o cron-job.org)
- [ ] Primera generación automática verificada

---

## 🆘 Problemas Comunes

### **Error: "Application failed to respond"**

**Solución:**
- Verifica que las variables de entorno estén configuradas
- Revisa los logs: `railway logs`
- Asegúrate de que `Procfile` existe y es correcto

### **Error: "Module not found"**

**Solución:**
- Verifica que `requirements.txt` está en la raíz del proyecto
- Railway instala dependencias automáticamente

### **Cronograma no se genera automáticamente**

**Solución:**
- Verifica que el cron job esté configurado
- Prueba manualmente: `https://TU-URL.railway.app/generate-cronograma`
- Revisa logs de GitHub Actions (si usas esa opción)

---

## 📞 Soporte

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **GitHub Actions Docs:** https://docs.github.com/actions

---

**¡Listo para desplegar!** 🚀

Sigue estos pasos y tendrás tu sistema funcionando 24/7 en minutos.
