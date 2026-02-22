# 🔄 Sistema Iterativo de Cronograma con Eventos Compartidos

## 📋 Descripción

Sistema completo que detecta eventos nuevos en el calendario compartido "Casa Juana Doña", los muestra en el cronograma para revisión, y permite copiarlos al calendario personal con regeneración automática del cronograma.

---

## 🏗️ Arquitectura del Sistema

### **Componentes:**

1. **events_db.py** - Base de datos SQLite para rastrear eventos
2. **event_detector.py** - Detector de eventos nuevos en calendario compartido
3. **web_server.py** - Servidor Flask con endpoints para copiar/ignorar eventos
4. **cronograma_generator_v7_5.py** - Generador modificado con sección de eventos nuevos
5. **calendar_client.py** - Cliente CalDAV extendido con métodos adicionales

---

## 🔄 Flujo Completo

```
🌅 6:30 AM - Railway ejecuta cronograma_generator_v7_5.py
   ↓
1️⃣ Detecta eventos nuevos en "Casa Juana Doña" (últimos 30 días)
   • Compara con base de datos de eventos conocidos
   • Marca nuevos eventos como 'new' en la BD
   ↓
2️⃣ Lee eventos de TU calendario personal (solo para hoy)
   • Estos son los bloques fijos prioritarios
   ↓
3️⃣ Lee tareas de Todoist
   ↓
4️⃣ Genera cronograma:
   • Bloques fijos: Solo eventos de TU calendario personal
   • Tareas: Distribuidas alrededor de TUS eventos
   ↓
5️⃣ Genera HTML con sección destacada de eventos nuevos
   • Si hay eventos pendientes → Sección amarilla arriba
   • Botones: "Copiar y regenerar" | "Ignorar"
   ↓
📧 Te envía el cronograma HTML
   ↓
   
🖥️ ABRES EL CRONOGRAMA
   ↓
📋 VES SECCIÓN DE EVENTOS NUEVOS (si los hay)
   ↓
🤔 DECIDES: ¿Este evento me afecta?
   ↓
   
┌─────────────────────────────────────┐
│ OPCIÓN A: Copiar evento             │
└─────────────────────────────────────┘
   ↓
✅ Haces clic en "Copiar y regenerar"
   ↓
📡 JavaScript envía petición a http://localhost:8000/copy-and-regenerate
   ↓
🔄 Servidor web (web_server.py):
   1. Busca evento en "Casa Juana Doña" por UID
   2. Copia evento a TU calendario personal
   3. Marca evento como 'copied' en BD
   4. Regenera cronograma (ejecuta cronograma_generator_v7_5.py)
   ↓
🔃 Página se recarga automáticamente
   ↓
✅ Cronograma actualizado:
   • Evento copiado ahora es bloque fijo
   • Tareas redistribuidas alrededor del nuevo evento
   • Evento desaparece de "nuevos"

┌─────────────────────────────────────┐
│ OPCIÓN B: Ignorar evento            │
└─────────────────────────────────────┘
   ↓
❌ Haces clic en "Ignorar"
   ↓
📡 JavaScript envía petición a http://localhost:8000/ignore-event
   ↓
🗑️ Servidor web marca evento como 'ignored' en BD
   ↓
🔃 Página se recarga
   ↓
✅ Evento desaparece de la sección de nuevos
```

---

## 📁 Estructura de Archivos

```
/home/ubuntu/daily-agenda-automation/
├── events_db.py                    # Base de datos SQLite
├── event_detector.py               # Detector de eventos nuevos
├── web_server.py                   # Servidor Flask
├── cronograma_generator_v7_5.py    # Generador modificado
├── calendar_client.py              # Cliente CalDAV extendido
├── events.db                       # Base de datos SQLite (generada)
├── cronograma_v7_5_YYYYMMDD_HHMMSS.html  # Cronograma generado
└── cronograma_v7_5_YYYYMMDD_HHMMSS.ics   # Archivo ICS
```

---

## 🗄️ Base de Datos (events.db)

### **Tabla: events**

| Campo | Tipo | Descripción |
|---|---|---|
| `uid` | TEXT PRIMARY KEY | UID único del evento (de iCloud) |
| `summary` | TEXT | Título del evento |
| `start_time` | TEXT | Hora de inicio (HH:MM) |
| `end_time` | TEXT | Hora de fin (HH:MM) |
| `date` | TEXT | Fecha del evento (YYYY-MM-DD) |
| `detected_at` | TIMESTAMP | Cuándo se detectó por primera vez |
| `status` | TEXT | Estado: 'new', 'copied', 'ignored' |
| `copied_at` | TIMESTAMP | Cuándo se copió (si aplica) |

---

## 🌐 Endpoints del Servidor Web

### **GET /health**
Verifica que el servidor esté funcionando.

**Respuesta:**
```json
{
  "status": "ok",
  "timestamp": "2025-12-03T05:29:47.521853"
}
```

### **POST /copy-and-regenerate**
Copia un evento al calendario personal y regenera el cronograma.

**Request:**
```json
{
  "uid": "E1A03EE9-59A2-4D8A-A651-428D5F2A85BC"
}
```

**Respuesta exitosa:**
```json
{
  "success": true,
  "message": "Evento copiado y cronograma regenerado",
  "reload": true
}
```

**Respuesta de error:**
```json
{
  "success": false,
  "error": "Descripción del error"
}
```

### **POST /ignore-event**
Marca un evento como ignorado.

**Request:**
```json
{
  "uid": "F39F27F8-5892-4998-83C9-A8CC7280C79C"
}
```

**Respuesta exitosa:**
```json
{
  "success": true,
  "message": "Evento marcado como ignorado"
}
```

---

## 🎨 Sección de Eventos Nuevos en HTML

### **Apariencia:**
- Fondo amarillo claro (#fff4e6)
- Borde naranja (#f59e0b)
- Título: "🆕 EVENTOS NUEVOS EN CALENDARIO COMPARTIDO"
- Cada evento en tarjeta blanca con:
  - 📅 Título del evento
  - 🕐 Fecha y horario
  - Fecha de detección
  - Botones: "📋 Copiar y regenerar" (verde) | "❌ Ignorar" (gris)

### **Funcionalidad JavaScript:**
- **copyAndRegenerate()**: Envía petición POST, muestra overlay de carga, recarga página
- **ignoreEvent()**: Envía petición POST, confirma acción, recarga página
- **showLoadingOverlay()**: Muestra spinner animado durante la operación
- **showSuccessMessage()**: Muestra notificación de éxito temporal

---

## 🚀 Cómo Usar

### **1. Generar cronograma manualmente:**
```bash
cd /home/ubuntu/daily-agenda-automation
python3.11 cronograma_generator_v7_5.py
```

### **2. Iniciar servidor web:**
```bash
cd /home/ubuntu/daily-agenda-automation
python3.11 web_server.py
```

El servidor se inicia en `http://localhost:8000`

### **3. Abrir cronograma:**
Abre el archivo HTML generado en tu navegador.

### **4. Revisar eventos nuevos:**
Si hay eventos nuevos, verás la sección amarilla arriba.

### **5. Copiar o ignorar:**
- Haz clic en "Copiar y regenerar" para copiar el evento a tu calendario
- Haz clic en "Ignorar" para marcarlo como ignorado

### **6. Cronograma se regenera automáticamente:**
La página se recarga con el cronograma actualizado.

---

## 🔧 Configuración en Railway

### **Variables de entorno necesarias:**
```
TODOIST_API_TOKEN=tu_token_todoist
ICLOUD_USERNAME=gardel.f@gmail.com
ICLOUD_APP_PASSWORD=ewyy-vmnp-mian-aifq
```

### **Procfile (para Railway):**
```
web: python3.11 web_server.py
```

### **Cron job (para ejecución diaria):**
```yaml
schedule: "30 6 * * *"  # 6:30 AM cada día
command: python3.11 cronograma_generator_v7_5.py
```

---

## 📊 Ejemplo de Uso

### **Escenario:**

1. **Lunes 6:30 AM** - Railway ejecuta el script
2. **Detecta**: Nuevo evento "Fisio alex" el 10/12 a las 12:15
3. **Genera**: Cronograma con sección de eventos nuevos
4. **7:00 AM** - Recibes el cronograma por email
5. **7:05 AM** - Abres el cronograma
6. **Ves**: "🆕 EVENTOS NUEVOS EN CALENDARIO COMPARTIDO"
   - 📅 Fisio alex
   - 🕐 10/12/2025 12:15 - 13:00
7. **Decides**: "Sí, me afecta"
8. **Haces clic**: "📋 Copiar y regenerar cronograma"
9. **Esperas 5 segundos**: Pantalla de carga
10. **Página se recarga**: Cronograma actualizado
11. **Ahora ves**: "Fisio alex" integrado en el día 10/12
12. **Tareas ajustadas**: Redistribuidas alrededor del nuevo evento

---

## ✅ Ventajas del Sistema

1. ✅ **Decisión informada** - Ves el cronograma antes de decidir
2. ✅ **Un solo lugar** - Todo en el cronograma HTML
3. ✅ **Un clic** - Copiar es inmediato
4. ✅ **Regeneración automática** - No tienes que hacer nada más
5. ✅ **Historial** - BD rastrea qué eventos has copiado/ignorado
6. ✅ **Sin duplicados** - Eventos copiados desaparecen de "nuevos"
7. ✅ **Gratis** - No requiere servicios de pago adicionales
8. ✅ **Confiable** - Railway garantiza la detección

---

## 🐛 Troubleshooting

### **Problema: No se detectan eventos nuevos**
- Verifica que el calendario "Casa Juana Doña" tenga eventos
- Revisa que las credenciales de iCloud sean correctas
- Ejecuta `python3.11 event_detector.py` manualmente para ver logs

### **Problema: Error al copiar evento**
- Verifica que el servidor web esté corriendo
- Revisa logs en `web_server.log`
- Asegúrate de que las credenciales de iCloud tengan permisos de escritura

### **Problema: Página no se recarga**
- Abre la consola del navegador (F12) para ver errores JavaScript
- Verifica que el servidor esté en `http://localhost:8000`
- Revisa que el endpoint `/copy-and-regenerate` responda

---

## 📝 Notas Importantes

1. **Calendario compartido vs personal**:
   - "Casa Juana Doña" = Calendario compartido (solo lectura para detección)
   - Tu calendario personal = Donde se copian los eventos

2. **Detección de eventos**:
   - Se revisan los próximos 30 días
   - Solo eventos nuevos (no en la BD) se muestran

3. **Regeneración**:
   - Solo se regenera el cronograma del día actual
   - Eventos futuros se copian pero no afectan el cronograma de hoy

4. **Base de datos**:
   - Se crea automáticamente en la primera ejecución
   - Persiste entre ejecuciones
   - Puedes resetearla borrando `events.db`

---

## 🎉 ¡Sistema Completo!

El sistema está listo para usar. Cada mañana:
1. Detecta eventos nuevos automáticamente
2. Te muestra una propuesta de cronograma
3. Tú decides qué eventos te afectan
4. El cronograma se ajusta automáticamente

**¡Cero clics necesarios para la detección, un clic para la decisión!** 🚀
