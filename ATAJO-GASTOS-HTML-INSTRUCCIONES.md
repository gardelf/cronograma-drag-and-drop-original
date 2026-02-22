# Atajo de iPhone - Gastos de Ayer (HTML)

## Configuración del Atajo

### Paso 1: Crear el atajo
1. Abre la app **Atajos** en tu iPhone
2. Toca **"+"** para crear un nuevo atajo
3. Dale un nombre: **"Gastos Ayer"**

### Paso 2: Añadir acciones

#### Acción 1: Obtener contenido de URL
1. Busca y añade: **"Obtener contenido de URL"**
2. En el campo URL, escribe:
   ```
   https://web-production-2ae52.up.railway.app/gastos-ayer-html
   ```
3. Método: **GET**

#### Acción 2: Vista Rápida
1. Busca y añade: **"Vista Rápida"**
2. Deja el campo vacío (usará el contenido de la acción anterior automáticamente)

### Paso 3: Guardar
1. Toca **"Listo"** arriba a la derecha

## Uso

### Ejecutar manualmente
1. Abre la app **Atajos**
2. Toca el atajo **"Gastos Ayer"**
3. Se abrirá una ventana emergente con el HTML formateado

### Ejecutar con Siri
1. Di: **"Oye Siri, Gastos Ayer"**
2. Se abrirá automáticamente la ventana emergente

### Añadir a pantalla de inicio
1. En la app Atajos, mantén presionado el atajo **"Gastos Ayer"**
2. Toca **"Detalles"**
3. Toca **"Añadir a pantalla de inicio"**
4. Personaliza el icono si quieres
5. Toca **"Añadir"**

## Características del HTML

### Diseño Visual
- **Fondo degradado morado** elegante
- **Tarjeta blanca** con sombra y bordes redondeados
- **Total destacado** con fondo degradado y texto grande
- **Lista de gastos** con emojis por categoría
- **Responsive** - se adapta al tamaño de pantalla

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

### Información Mostrada
- **Fecha** del día anterior
- **Total gastado** en grande
- **Número de compras**
- **Lista detallada** de cada gasto:
  - Emoji de categoría
  - Descripción
  - Categoría
  - Monto

## Ventajas sobre Notificación

✅ **Más espacio** - Muestra todos los gastos sin límite de altura
✅ **Mejor diseño** - Colores, gradientes, sombras, emojis grandes
✅ **Interactivo** - Puedes hacer scroll si hay muchos gastos
✅ **Responsive** - Se adapta al tamaño de pantalla
✅ **Profesional** - Aspecto visual moderno y elegante

## Solución de Problemas

### No se muestra nada
- Verifica que tengas conexión a internet
- Comprueba que la URL sea correcta
- Prueba abrir la URL en Safari para ver si funciona

### Muestra error
- Verifica que Firefly III esté funcionando
- Comprueba que haya gastos registrados para ayer
- Revisa los logs de Railway si es necesario

### El HTML no se ve bien
- Asegúrate de usar **"Vista Rápida"** y no "Mostrar resultado"
- Vista Rápida renderiza el HTML correctamente con todos los estilos

## Alternativa: Abrir en Safari

Si prefieres ver el HTML en Safari en lugar de Vista Rápida:

1. Reemplaza la acción **"Vista Rápida"** por **"Abrir URLs"**
2. En el campo URL, pon: **"Contenido de URL"** (variable de la acción anterior)

Esto abrirá el HTML en Safari en pantalla completa.
