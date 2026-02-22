# 🔧 Solución: Problema de Carga de Datos de Todoist en Railway

## 📋 Diagnóstico del Problema

### Problema Identificado

El sistema no cargaba datos de Todoist al presionar el botón "Regenerar" en Railway debido a que **la API de Todoist cambió su estructura y endpoint**.

### Causa Raíz

1. **URL de API obsoleta**: El código usaba `https://api.todoist.com/rest/v2/` que fue deprecada
2. **Nueva URL de API**: Todoist migró a `https://api.todoist.com/api/v1/`
3. **Estructura de respuesta diferente**: La nueva API devuelve `{"results": [...]}` en lugar de un array directo

### Error Recibido

```
410 Client Error: Gone for url: https://api.todoist.com/rest/v2/tasks
This endpoint is deprecated.
```

---

## ✅ Solución Implementada

### Cambios Realizados

#### 1. Actualización de URL Base (todoist_client.py)

**Antes:**
```python
BASE_URL = "https://api.todoist.com/rest/v2"
```

**Después:**
```python
BASE_URL = "https://api.todoist.com/api/v1"
```

#### 2. Manejo de Nueva Estructura de Respuesta

**Antes:**
```python
response = requests.get(url, headers=self.headers)
response.raise_for_status()

tasks = response.json()
return tasks
```

**Después:**
```python
response = requests.get(url, headers=self.headers)
response.raise_for_status()

data = response.json()
# New API returns {"results": [...]}
tasks = data.get('results', data) if isinstance(data, dict) else data
return tasks
```

Este cambio se aplicó en:
- `get_today_tasks()` (línea 40-46)
- `get_all_active_tasks()` (línea 62-68)

---

## 🧪 Verificación

### Prueba Exitosa

```bash
$ python3.11 diagnostico_todoist.py

================================================================================
🔍 DIAGNÓSTICO DE CONEXIÓN CON TODOIST
================================================================================

1️⃣ Verificando variables de entorno...
   TODOIST_API_TOKEN existe: True
   TODOIST_API_TOKEN longitud: 40

2️⃣ Probando conexión directa con API de Todoist...
   Status Code: 200
   ✅ Conexión exitosa!
   Total de tareas activas: 50

3️⃣ Probando con TodoistClient...
   ✅ Total de tareas obtenidas: 50
   ✅ Tareas formateadas: 50
```

---

## 📦 Archivos Modificados

1. **`todoist_client.py`**
   - Actualizada URL base de API
   - Actualizado manejo de respuesta en `get_today_tasks()`
   - Actualizado manejo de respuesta en `get_all_active_tasks()`

2. **`DESPLIEGUE_RAILWAY_PASO_A_PASO.md`**
   - Actualizado token de API de Todoist (de seguridad)

3. **`diagnostico_todoist.py`** (nuevo)
   - Script de diagnóstico para verificar conexión con Todoist
   - Útil para debugging futuro

---

## 🚀 Pasos para Desplegar en Railway

### 1. Subir los Cambios a GitHub

```bash
cd /ruta/a/daily-agenda-automation

# Agregar archivos modificados
git add todoist_client.py
git add DESPLIEGUE_RAILWAY_PASO_A_PASO.md
git add diagnostico_todoist.py

# Crear commit
git commit -m "fix: actualizar API de Todoist a v1 y corregir estructura de respuesta"

# Subir a GitHub
git push origin main
```

### 2. Railway Desplegará Automáticamente

Railway detectará los cambios y redesplegará automáticamente. El proceso toma aproximadamente 2-3 minutos.

### 3. Verificar Variables de Entorno en Railway

Asegúrate de que estas variables estén configuradas en Railway:

```
TODOIST_API_TOKEN=50ff91ef15761a6727b8b991ac3be61a96f76538
ICLOUD_USERNAME=gardel.f@gmail.com
ICLOUD_APP_PASSWORD=ewyy-vmnp-mian-aifq
```

### 4. Probar el Sistema

1. Accede a tu URL de Railway: `https://tu-app.up.railway.app`
2. Presiona el botón **"Regenerar"**
3. Verifica que las tareas de Todoist se carguen correctamente

---

## 🔍 Flujo Completo del Sistema

### 1. Punto de Entrada
- **Archivo**: `railway_init.sh` (ejecutado por Procfile)
- **Acción**: Inicializa BD y genera cronograma inicial
- **Servidor**: Inicia `web_server.py`

### 2. Endpoint de Regeneración
- **URL**: `/regenerate` o `/generate-cronograma`
- **Método**: GET o POST
- **Acción**: Llama a `regenerate_cronograma()`

### 3. Generación de Cronograma
- **Script**: `cronograma_generator_v7_5.py`
- **Proceso**:
  1. Detecta eventos nuevos en calendario compartido
  2. Obtiene eventos del calendario personal (iCloud)
  3. **Obtiene tareas de Todoist** ← AQUÍ ESTABA EL PROBLEMA
  4. Filtra tareas por fecha objetivo
  5. Carga tareas completadas de BD local
  6. Genera cronograma HTML

### 4. Cliente de Todoist
- **Archivo**: `todoist_client.py`
- **Clase**: `TodoistClient`
- **Métodos clave**:
  - `get_all_active_tasks()`: Obtiene todas las tareas activas
  - `format_tasks_for_display()`: Formatea tareas para visualización

---

## 🐛 Debugging Futuro

Si el problema persiste o aparecen nuevos errores:

### 1. Ejecutar Script de Diagnóstico

```bash
# En Railway, acceder a la consola y ejecutar:
python3.11 diagnostico_todoist.py
```

### 2. Verificar Logs de Railway

```bash
# Con Railway CLI:
railway logs

# O en el dashboard web:
Railway → Tu Proyecto → Deployments → Ver logs
```

### 3. Verificar Token de Todoist

1. Ir a https://todoist.com/app/settings/integrations
2. Verificar que el token sea válido
3. Si es necesario, generar un nuevo token y actualizar en Railway

---

## 📚 Documentación de Referencia

- **Todoist API v1**: https://developer.todoist.com/api/v1/
- **Todoist REST API v2** (deprecada): https://developer.todoist.com/rest/v2/
- **Railway Docs**: https://docs.railway.app

---

## ⚠️ Notas Importantes

1. **La API v2 de Todoist está deprecada** pero la documentación es confusa
2. **La URL correcta es `/api/v1/`** (no `/rest/v1/` ni `/rest/v2/`)
3. **La estructura de respuesta cambió**: ahora devuelve `{"results": [...]}`
4. **El token de Todoist fue actualizado** por seguridad (el anterior estaba expuesto)

---

## ✅ Checklist de Verificación

- [x] URL de API actualizada a `/api/v1/`
- [x] Manejo de nueva estructura de respuesta implementado
- [x] Token de Todoist actualizado
- [x] Script de diagnóstico creado
- [x] Cambios probados localmente
- [ ] Cambios subidos a GitHub
- [ ] Railway redesplegado
- [ ] Sistema verificado en producción

---

**Fecha de solución**: 12 de febrero de 2026  
**Autor**: Manus AI  
**Estado**: ✅ Solucionado y listo para desplegar
