# 🔄 INSTRUCCIONES DE ROLLBACK

## ✅ PUNTO DE REFERENCIA ESTABLE

**Tag:** `STABLE-WORKING-VERSION`  
**Fecha:** 18 de diciembre de 2025  
**Commit:** 52b346a

### Estado del sistema en este punto:

- ✅ Cronograma funcionando correctamente
- ✅ PostgreSQL configurado para Idealista
- ✅ Gastos extraordinarios del mes siguiente
- ✅ Detección de fechas y categorías con ChatGPT
- ✅ Respeto de horarios de Todoist (due_time)
- ✅ Color de texto de tareas en gris oscuro

### ⚠️ Problema pendiente:

Al marcar tareas como completadas y regenerar, las tareas desaparecen del cronograma en lugar de mantenerse tachadas.

---

## 🔙 Cómo volver a este punto estable:

### Opción 1: Usando el tag
```bash
cd /home/ubuntu/daily-agenda-automation
git fetch --all --tags
git checkout STABLE-WORKING-VERSION
git push --force
```

### Opción 2: Usando el commit
```bash
cd /home/ubuntu/daily-agenda-automation
git reset --hard 52b346a
git push --force
```

### Opción 3: Desde GitHub
1. Ve a: https://github.com/gardelf/daily-agenda-automation/releases
2. Busca el tag `STABLE-WORKING-VERSION`
3. Descarga el código fuente

---

## 📋 Verificación después del rollback:

1. Railway redesplegará automáticamente
2. Espera 2-3 minutos
3. Accede al cronograma: https://web-production-2ae52.up.railway.app/
4. Verifica que todo funciona correctamente

---

**Nota:** Este archivo se creó como referencia para futuras modificaciones.
