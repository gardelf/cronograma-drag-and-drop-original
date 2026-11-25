# Nivel 2 — Gastar con sentido

Módulo Flask independiente de los cálculos del Nivel 1. `/nivel2` contiene matriz,
gastos interpretados, pendientes y resumen por valores. La integración en los dos
entrypoints existentes añade únicamente el registro del blueprint bajo bandera;
el enlace se añade al HTML de `/sandbox`, no a sus cálculos.

## Datos y reglas

PostgreSQL exclusivo mediante `NIVEL2_DATABASE_URL`, sin fallback a `DATABASE_URL`.
Las migraciones SQL versionadas se ejecutan con bloqueo transaccional. La carga
inicial inserta 20 unidades permanentes y 5 valores sin sobrescribir ediciones.
R05 es plaza 39, según la matriz solicitada; no se equipara a la antigua plaza 33.
Los costes desconocidos son NULL, nunca cero. Satisfacción y tiempo son referencias
de la matriz y no observaciones inferidas de un recibo. Una unidad puede recibir
muchos movimientos y cada movimiento puede repartirse entre varias unidades.

Solo se proponen interpretaciones para retiradas en rutas 1→2 y 6→7. Ingresos,
transferencias y otras rutas quedan excluidos y visibles en el historial. Esta
restricción corresponde a las cuentas actuales del propietario; debe revisarse
si se incorporan nuevas cuentas de gasto. Una coincidencia de comercio, incluido
Maroma, nunca confirma automáticamente una actividad, compañía o duración.

Las reglas de texto proponen unidades; el coste estándar y la categoría financiera
aportan indicios. Una corrección confirmada crea una regla persistente y específica
por descripción, destinatario, categoría, ruta, moneda e importe. Incluso esa regla
solicita confirmación para nuevos movimientos. Repartos y exclusiones eliminan la
regla simple correspondiente. No se utiliza un proveedor de IA en esta versión.

El resumen suma exclusivamente imputaciones confirmadas, vigentes y elegibles.
Separa moneda, unidad, valor y naturaleza: obligado, discrecional, desconocido.
Las propuestas y modificaciones pendientes no inflan sus totales.

## Sincronización

Worker independiente: `python -m nivel2.sync`. Solo realiza solicitudes GET a la
API de Firefly; no tiene ningún código de escritura, etiquetas ni borrado remoto.
Usa `NIVEL2_FIREFLY_TOKEN` o el token existente con `FIREFLY_URL`. El token existente
puede tener permisos más amplios en Firefly; el acceso de este módulo está limitado
a lectura por su implementación, no se afirma un alcance OAuth de solo lectura.

`NIVEL2_HISTORY_START` determina el inicio (por defecto 2025-09-01).
`NIVEL2_SYNC_SECONDS` determina el intervalo (900 segundos por defecto, mínimo 60).
Tras el histórico inicial, relee una ventana de 7 días y realiza reconciliación
completa diaria. Los cambios antiguos pueden tardar hasta la siguiente reconciliación
diaria. Cada journal conserva grupo, instancia y referencia original únicos.
Obtiene todas las páginas antes de aplicar cambios; verifica individualmente los
movimientos ausentes, conserva tombstones de eliminaciones y revisa las imputaciones
confirmadas si el original cambia. No elimina el historial. Bloqueo asesor evita
dos sincronizaciones simultáneas. Fallos se auditan por tipo sin volcar credenciales.

## Despliegue y acceso

La web existente activa el módulo mediante `NIVEL2_ENABLED=1`,
`NIVEL2_DATABASE_URL` y `NIVEL2_ACCESS_TOKEN`. Las credenciales de acceso son usuario
`nivel2` y el token de acceso, con autenticación Basic sobre HTTPS. Las respuestas
no se cachean, se elimina CORS abierto para este módulo y las mutaciones requieren
JSON, cabecera propia y origen válido. No reutiliza la contraseña de PostgreSQL.

El Dockerfile se construye con raíz `/nivel2`; permite un servicio web de prueba
(`nivel2.standalone:app`) y otro worker. Las migraciones se ejecutan antes del
arranque del web de prueba y del worker. El despliegue integrado depende de que
el worker haya migrado la base previamente. La app principal no bloquea su arranque
por indisponibilidad de la nueva base: sus rutas previas siguen independientes.

Las variables se vinculan en Railway por referencias, nunca se guardan secretos en
GitHub. La nueva base debe contar con la política de copias/restauración adecuada al
uso; este módulo no configura una política de backups automáticamente.

## Verificación

Actions ejecuta pruebas contra PostgreSQL desechable, matriz idempotente, repartos,
versiones concurrentes, aprendizaje, modificaciones/eliminaciones y fallos de lectura.
Pruebas adicionales verifican acceso y preservación literal de ambos entrypoints del
Nivel 1 salvo el registro opcional. Para desactivar el módulo basta deshabilitar la
bandera y detener el worker; no se requiere revertir ni borrar datos de Firefly.
