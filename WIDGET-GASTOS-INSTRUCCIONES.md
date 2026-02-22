# Widget de Gastos de Ayer - Instrucciones de Instalación

## Requisitos
- iPhone con iOS 14 o superior
- App **Scriptable** (gratis en App Store)

## Instalación

### 1. Instalar Scriptable
1. Abre la **App Store**
2. Busca **"Scriptable"**
3. Descarga e instala la app (es gratis)

### 2. Crear el script

1. Abre la app **Scriptable**
2. Toca el botón **"+"** (arriba a la derecha)
3. Se abrirá un nuevo script vacío
4. **Copia todo el contenido** del archivo `scriptable-gastos-ayer.js`
5. **Pégalo** en el editor de Scriptable (borra el contenido que haya)
6. Toca el título "Untitled Script" arriba
7. Cámbiale el nombre a: **"Gastos Ayer"**
8. Toca **"Done"** para guardar

### 3. Probar el script

1. En la lista de scripts, toca **"Gastos Ayer"**
2. Debería ejecutarse y mostrar una vista previa del widget
3. Si ves tus gastos de ayer, ¡funciona! ✅

### 4. Añadir el widget a la pantalla de inicio

1. Ve a la **pantalla de inicio** de tu iPhone
2. Mantén presionado en un espacio vacío hasta que los iconos tiemblen
3. Toca el botón **"+"** (arriba a la izquierda)
4. Busca **"Scriptable"**
5. Selecciona el tamaño **"Medium"** (mediano, rectangular)
6. Toca **"Add Widget"**
7. El widget aparecerá en tu pantalla
8. **Mantén presionado** sobre el widget
9. Toca **"Edit Widget"**
10. En **"Script"**, selecciona **"Gastos Ayer"**
11. Toca fuera del widget para guardar
12. Toca **"Done"** arriba a la derecha

## Características del Widget

### Diseño Visual
- **Fondo degradado azul** elegante
- **Total destacado en amarillo** con tamaño grande
- **Emojis por categoría** para identificación rápida
- **Lista de hasta 4 gastos** con descripción y monto
- **Fecha del día** en la parte inferior

### Emojis por Categoría
- 🍽️ Comida
- 🚗 Coche
- 💊 Salud
- 🚌 Transporte
- 🎮 Ocio
- 👕 Ropa
- 🏠 Casa
- 💻 Tecnología
- ✈️ Viajes
- 📦 Otros

### Actualización
- El widget se actualiza **automáticamente** cada cierto tiempo
- También puedes **tocar el widget** para forzar actualización

## Solución de Problemas

### El widget muestra "Sin gastos ayer"
- Verifica que haya gastos registrados en Firefly III para el día anterior
- Comprueba que el endpoint funcione: abre Safari y ve a `https://web-production-2ae52.up.railway.app/gastos-ayer`

### El widget muestra error
- Verifica que tengas conexión a internet
- Abre la app Scriptable y ejecuta el script manualmente para ver el error
- Comprueba que la URL del API sea correcta en el script

### El widget no se actualiza
- Toca el widget para forzar actualización
- Reinicia el iPhone si es necesario

## Personalización

Puedes editar el script para personalizar:

- **Colores del fondo**: Cambia los valores en `gradient.colors`
- **Número de gastos mostrados**: Cambia `maxExpenses = Math.min(data.expenses.length, 4)`
- **Emojis**: Modifica el objeto `CATEGORY_EMOJIS`
- **Tamaño de fuente**: Ajusta los valores en `Font.systemFont(XX)`

## Notas

- El widget muestra los gastos de **ayer**, no de hoy
- Si hoy es lunes, mostrará los gastos del domingo
- El widget funciona en **modo claro y oscuro** de iOS
- El tamaño recomendado es **Medium** (mediano)
