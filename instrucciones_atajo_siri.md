# Instrucciones para el Atajo de Siri: "Registrar Gasto"

¡Hola! He preparado todo para que puedas registrar tus gastos usando tu voz con Siri. El `backend` ya está funcionando en la nube.

Para que todo funcione, sigue estos dos pasos:

1.  **Configura las Claves API en Railway.**
2.  **Crea el Atajo en tu iPhone.**

---

### Paso 1: Configurar las Claves API en Railway

Para que el sistema pueda guardar los gastos en tu cuenta de Firefly III, necesitas añadir tu token de API a la configuración del proyecto en Railway. También puedes añadir opcionalmente tu clave de OpenAI para la categorización con IA.

1.  **Ve a tu proyecto en Railway:**
    *   Abre este enlace: [https://railway.app/project/a8bbb9f9-b87f-4b0a-a0c4-0c8c1a2e4a9d/service/web?id=a8bbb9f9-b87f-4b0a-a0c4-0c8c1a2e4a9d](https://railway.app/project/a8bbb9f9-b87f-4b0a-a0c4-0c8c1a2e4a9d/service/web?id=a8bbb9f9-b87f-4b0a-a0c4-0c8c1a2e4a9d)
    *   Si no has iniciado sesión, hazlo con tu cuenta de GitHub.

2.  **Ve a la pestaña "Variables":**
    *   Dentro de tu proyecto, busca el servicio llamado `web` y haz clic en él.
    *   Selecciona la pestaña `Variables`.

3.  **Añade las siguientes variables:**

    *   **`FIREFLY_TOKEN`**:
        *   **Nombre:** `FIREFLY_TOKEN`
        *   **Valor:** Pega aquí tu token de la API de Firefly III (el que me proporcionaste anteriormente).

    *   **`OPENAI_API_KEY`** (Opcional):
        *   Si quieres usar la categorización por IA para gastos que no sigan las reglas, añade esta variable.
        *   **Nombre:** `OPENAI_API_KEY`
        *   **Valor:** Pega aquí tu clave de la API de OpenAI.

    *   **`FIREFLY_URL`** (Ya debería estar configurada, pero verifícala):
        *   **Nombre:** `FIREFLY_URL`
        *   **Valor:** `https://firefly-core-production-f02a.up.railway.app`

4.  **Guarda y redespliega:**
    *   Railway guardará las variables automáticamente y comenzará un nuevo despliegue. Espera a que finalice (verás una marca de verificación verde).

---

### Paso 2: Crear el Atajo en tu iPhone

Ahora, vamos a crear el atajo en la app **Atajos** de tu iPhone. He diseñado los pasos para que sean muy fáciles de seguir.

1.  **Abre la app Atajos** y pulsa el icono `+` para crear un nuevo atajo.

2.  **Renombra el atajo:** Pulsa en la parte superior donde dice "Nuevo atajo" y ponle el nombre **"Registrar Gasto"**. Esto te permitirá activarlo diciendo "Oye Siri, Registrar Gasto".

3.  **Añade la acción "Solicitar entrada":**
    *   Pulsa en "Añadir acción".
    *   Busca y selecciona **Solicitar entrada**.
    *   Configúrala así:
        *   `Solicitar` **Texto** `con` **"¿Qué gasto quieres registrar?"**.

4.  **Añade la acción "URL":**
    *   Pulsa el `+` azul.
    *   Busca y selecciona **URL**.
    *   Pega la siguiente URL:
        ```
        https://web-production-2ae52.up.railway.app/registrar-gasto
        ```

5.  **Añade la acción "Obtener contenido de URL":**
    *   Pulsa el `+` azul.
    *   Busca y selecciona **Obtener contenido de URL**.
    *   Pulsa en la flecha azul `>` para ver más opciones y configúrala así:
        *   **Método:** `POST`
        *   **Cabeceras:** Pulsa en `Añadir nueva cabecera`.
            *   **Clave:** `Content-Type`
            *   **Texto:** `application/json`
        *   **Cuerpo de la solicitud:**
            *   Selecciona `JSON`.
            *   Pulsa en `Añadir nuevo campo` y elige `Texto`.
            *   Configura el campo así:
                *   **Clave:** `texto`
                *   **Texto:** Pulsa en la variable `Entrada proporcionada` (debería aparecerte como una burbuja azul).

6.  **Añade la acción "Obtener diccionario de":**
    *   Pulsa el `+` azul.
    *   Busca y selecciona **Obtener diccionario de**.
    *   En el campo `Obtener diccionario de`, pulsa y selecciona la variable `Contenido de la URL`.

7.  **Añade la acción "Obtener valor de diccionario":**
    *   Pulsa el `+` azul.
    *   Busca y selecciona **Obtener valor de diccionario**.
    *   Configúrala así:
        *   `Obtener valor para` **mensaje** `en` **Diccionario**.

8.  **Añade la acción "Mostrar notificación":**
    *   Pulsa el `+` azul.
    *   Busca y selecciona **Mostrar notificación**.
    *   En el campo de texto, borra el contenido por defecto y pulsa para seleccionar la variable `Valor del diccionario`.

¡Y listo! Ahora puedes probarlo.

### ¿Cómo usarlo?

Simplemente di:

> **"Oye Siri, Registrar Gasto"**

Siri te preguntará "¿Qué gasto quieres registrar?". Responde con el importe y la descripción. Por ejemplo:

*   `25.50 Mercadona`
*   `60 gasolina`
*   `12.80 un libro`

El sistema lo registrará en Firefly III con la categoría correcta y te mostrará una notificación de confirmación.

Si tienes alguna duda, ¡pregunta!
