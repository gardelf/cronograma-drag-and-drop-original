# 📅 Integración con iCloud Calendar

## Descripción

Esta integración permite que el generador de cronogramas lea automáticamente los eventos de tu Calendario de iPhone (iCloud) y los trate como **bloques fijos prioritarios**. Los eventos del calendario ocupan su espacio reservado antes de distribuir las tareas de Todoist.

## 🎯 Funcionamiento

### Prioridad de bloques:

1. **Eventos del Calendario** (Prioridad máxima - P1)
2. **Bloques fijos predefinidos** (Desayunar, Comer)
3. **Tareas de Todoist** (Se distribuyen en los huecos libres)

### Ejemplo:

Si tienes una reunión en tu calendario de 10:00 a 11:30:
- El cronograma reservará ese bloque automáticamente
- Las tareas de Todoist se distribuirán antes de las 10:00 y después de las 11:30
- La reunión aparecerá en el cronograma HTML con el emoji 📅

## 🔧 Configuración

### Paso 1: Generar contraseña específica de app

1. Ve a https://appleid.apple.com
2. Inicia sesión con tu Apple ID
3. En la sección "Seguridad", busca "Contraseñas de apps"
4. Haz clic en "Generar contraseña"
5. Dale un nombre: "Railway Cronograma"
6. Copia la contraseña generada (formato: xxxx-xxxx-xxxx-xxxx)

⚠️ **Importante**: NO uses tu contraseña principal de iCloud. Usa solo la contraseña específica de app.

### Paso 2: Configurar variables de entorno

Añade estas variables de entorno en Railway (o en tu `.env` local):

```bash
ICLOUD_USERNAME=tu_email@icloud.com
ICLOUD_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

### Paso 3: Instalar dependencias

```bash
pip install -r requirements.txt
```

Las nuevas dependencias añadidas son:
- `caldav==1.3.9` - Cliente CalDAV para acceder a iCloud Calendar
- `icalendar==5.0.11` - Parser de formato iCalendar
- `pytz==2023.3` - Manejo de zonas horarias

## 📝 Uso

### Ejecución automática

Cuando ejecutas el generador de cronogramas:

```bash
python cronograma_generator_v7_5.py
```

El script automáticamente:

1. ✅ Se conecta a iCloud Calendar
2. ✅ Obtiene todos los eventos del día actual
3. ✅ Los convierte a bloques fijos con prioridad P1
4. ✅ Los integra en el cronograma antes de las tareas de Todoist

### Salida en consola

```
================================================================================
📅 CRONOGRAMA GENERATOR V7.5 - MORNING ALTERNATION RULE (FIXED)
================================================================================

1️⃣ Fetching events from iCloud Calendar...
✅ Conectado a iCloud Calendar

📅 Buscando eventos del calendario para: 02/12/2024
   Revisando calendario: Calendario
      ✓ 10:00-11:30: Reunión con equipo
      ✓ 15:00-16:00: Cita médica

✅ Total de eventos encontrados: 2
✅ Found 2 calendar events

2️⃣ Fetching ALL active tasks from Todoist...
✅ Found 95 active tasks

...

4️⃣ Generating cronograma with Morning Alternation Rule...
   Adding calendar events as fixed blocks...
      ✅ 10:00-11:30: 📅 Reunión con equipo
      ✅ 15:00-16:00: 📅 Cita médica
```

## 🧪 Pruebas

### Probar la conexión

Ejecuta el módulo de calendario directamente:

```bash
python calendar_client.py
```

Esto te mostrará:
- Si la conexión a iCloud es exitosa
- Todos los eventos del día actual
- Formato detallado de cada evento

### Sin credenciales configuradas

Si no configuras las credenciales, el sistema funcionará normalmente pero sin eventos del calendario:

```
⚠️  ADVERTENCIA: Credenciales de iCloud no configuradas
   Configura ICLOUD_USERNAME y ICLOUD_APP_PASSWORD en variables de entorno
⚠️  Cliente CalDAV no disponible, devolviendo lista vacía
✅ Found 0 calendar events
```

## 📋 Formato de eventos

Los eventos del calendario se convierten al siguiente formato:

```python
{
    'content': '📅 Reunión con equipo',
    'start_time': '10:00',
    'end_time': '11:30',
    'duration': 90,
    'type': 'Fija',
    'priority': 'P1',
    'priority_value': 4,
    'labels': ['calendario', 'Calendario'],
    'source': 'calendar',
    'url': None
}
```

## 🎨 Visualización en el cronograma

Los eventos del calendario aparecen:

- Con emoji **📅** al inicio del título
- Tipo: **Fija**
- Prioridad: **P1** (chip rojo)
- Etiquetas: **calendario** + nombre del calendario
- Color de fondo: Según el bloque horario

## 🔒 Seguridad

- ✅ Usa contraseñas específicas de app (no tu contraseña principal)
- ✅ Las credenciales se almacenan en variables de entorno
- ✅ Conexión HTTPS segura con iCloud
- ✅ No se almacenan credenciales en el código

## 🐛 Solución de problemas

### Error: "Authentication failed"

- Verifica que estés usando una contraseña específica de app
- Asegúrate de que el email sea correcto
- Comprueba que la autenticación de dos factores esté activada en tu Apple ID

### Error: "No calendars found"

- Verifica que tengas al menos un calendario en iCloud
- Comprueba que el calendario no esté oculto
- Asegúrate de que el calendario tenga eventos

### Los eventos no aparecen

- Verifica que los eventos sean del día actual
- Comprueba que los eventos tengan hora (no sean eventos de "todo el día")
- Asegúrate de que los eventos estén en el rango 07:00-21:00

## 📚 Referencias

- [CalDAV Python Library](https://caldav.readthedocs.io/)
- [iCloud CalDAV URL](https://caldav.icloud.com/)
- [Apple ID - Contraseñas de apps](https://appleid.apple.com)

## 🚀 Próximos pasos

Una vez configurado, el sistema funcionará automáticamente:

1. Railway ejecuta el script cada día a las 6:30 AM
2. Lee eventos del calendario
3. Lee tareas de Todoist
4. Genera cronograma integrado
5. Exporta HTML + ICS

**¡Cero clics necesarios!** 🎉
