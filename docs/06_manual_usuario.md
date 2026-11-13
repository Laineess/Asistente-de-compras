# Manual de usuario

> Estado: bot de texto y voz disponible, con despliegue 24/7 documentado. La interfaz web sigue disponible.

## 1. Qué hace el asistente

El asistente compara productos en **Walmart**, **Costco** y **Sam's**, analiza precios y reseñas, y recomienda qué comprar. Puedes usarlo de dos formas:

- **Bot de Telegram:** texto o notas de voz, ideal para el móvil.
- **Interfaz web:** formulario con comparación detallada e historial.

No realiza compras ni pagos: solo entrega información para decidir.

## 2. Requisitos

### Para usar el bot

- Una cuenta de Telegram.
- Estar incluido en la allowlist del bot (tu ID numérico).
- Conexión a internet.

No necesitas instalar nada en el teléfono.

### Para ejecutar el proyecto en local

- Python 3.12+
- Node.js 20+ solo si usarás la interfaz web.
- Nada adicional para voz: PyAV se instala con las dependencias de voz.
- Claves de Gemini y Tavily (opcionales; sin ellas se usan heurísticas y datos mock).
- Token de bot de Telegram y tu ID numérico.

## 3. Crear y configurar el bot (administrador)

1. Abre Telegram y busca **@BotFather**.
2. Envía `/newbot`, elige un nombre y un usuario terminado en `bot`.
3. Copia el token que entrega BotFather.
4. Obtén tu ID numérico con **@userinfobot** o un bot similar.
5. En `.env`, configura:

   ```env
   TELEGRAM_BOT_TOKEN=123456:ABC...
   TELEGRAM_ALLOWED_USER_IDS=123456789
   BOT_DEFAULT_MODE=fast
   TELEGRAM_TTS_VOICE=es-MX-JorgeNeural
   ```

6. Nunca compartas el token ni lo subas a git. Si se filtra, usa `/revoke` en BotFather.

## 4. Iniciar el bot

### Windows (desarrollo)

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r backend/requirements.txt
pip install -r backend/requirements-bot.txt
# Voz opcional:
# pip install -r backend/requirements-voice.txt
cd backend
../.venv/Scripts/python.exe -m app.bot.main
```

### Ubuntu (VPS, 24/7)

Sigue la guía de [`10_bot_telegram.md`](10_bot_telegram.md). El bot corre como servicio `compras-bot` con `systemd`; no requiere Docker ni abrir puertos.

## 5. Primer uso

1. Abre el chat con tu bot y envía `/start`.
2. Escribe una consulta, por ejemplo:

   ```text
   Busca una laptop para la universidad, máximo 15000, en Walmart y Costco
   ```

   También puedes enviar una **nota de voz** con la misma idea.
3. Si falta el producto, el bot lo preguntará.
4. Revisa el resumen y pulsa **Analizar**.
5. Espera el resultado: recomendación, enlaces y reseñas del top 3.
6. Si enviaste voz o activaste audio, recibirás un audio corto por cada producto del top 3.

## 6. Comandos

| Comando | Para qué sirve |
|---|---|
| `/start` | Bienvenida y ejemplo. |
| `/nuevo` | Empezar una consulta desde cero. |
| `/cancelar` | Cancelar la consulta o el análisis en curso. |
| `/ayuda` | Ver comandos y ejemplos. |
| `/modo` | Cambiar entre `fast` y `detallado`. |
| `/voz` | Elegir respuesta de audio: `auto`, `siempre` o `nunca`. |
| `/estado` | Ver modo, voz y datos recolectados. |

## 7. Datos de la consulta

| Dato | ¿Obligatorio? | Ejemplo | Nota |
|---|---|---|---|
| Producto | Sí | `laptop`, `audífonos`, `licuadora` | Si falta, el bot lo pide. |
| Tiendas | No | `Walmart y Costco` | Por defecto busca en las tres. |
| Presupuesto | No | `máximo 15000` | En pesos mexicanos; sin límite si se omite. |
| Perfil | No | `para estudiante`, `para gamer` | Ayuda al análisis de audiencia. |
| Límite | No | `3 por tienda` | Valor por defecto: 3. |

El bot intenta entender la consulta en lenguaje natural. Si algo es ambiguo, pregunta antes de ejecutar. Siempre muestra un resumen y pide confirmación.

## 8. Modos de análisis

| Modo | Cuándo usarlo | Qué cambia |
|---|---|---|
| `fast` | Uso diario | Sin Gemini; búsqueda y heurísticas. Más rápido y no consume cuota. |
| `detallado` | Cuando quieres una síntesis más rica | Usa Gemini para reseñas, audiencia y recomendación. Consume cuota gratuita. |

Cambia con `/modo`. Si Gemini falla o se agota la cuota, el bot responde con heurísticas y te avisa.

## 9. Cómo leer el resultado

- **Recomendación:** la opción principal y por qué conviene.
- **Precio:** mínimo, máximo, promedio y si está dentro de tu presupuesto.
- **Top 3:** el recomendado y dos alternativas. Cada uno incluye tienda, precio, enlace y reseña corta.
- **Score /10:** estimación de satisfacción basada en reseñas; no es una garantía.
- **Pros y contras:** puntos positivos y negativos encontrados en las reseñas.
- **Enlaces:** llevan a la publicación del producto en la tienda. Verifica precio y disponibilidad antes de comprar.
- **Advertencias:** indican datos mock, tiendas faltantes o reseñas insuficientes.

Los datos pueden venir de **Tavily** (reales) o del catálogo **mock** (simulados). El resultado indica la fuente; si es mock, úsalo solo como referencia.

## 10. Notas de voz y audio

- Envía una nota de voz en español; el bot la transcribe y muestra el texto.
- Si la transcripción tiene errores, corrige con un mensaje de texto.
- La entrada máxima es de 120 segundos por defecto.
- La respuesta de audio es breve (30-45 s por producto) y siempre va acompañada del texto.
- `/voz auto` envía audio solo cuando hablas; `/voz siempre` lo envía también para texto; `/voz nunca` lo desactiva.
- Si el audio falla, el texto sigue disponible.

## 11. Interfaz web (opcional)

1. Inicia el backend:

   ```bash
   cd backend
   ../.venv/Scripts/python.exe -m uvicorn app.main:app --reload
   ```

2. Inicia el frontend:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Abre `http://localhost:3000`.
4. Escribe el producto, elige tiendas y presupuesto, y ejecuta el análisis.
5. Revisa comparación, score, audiencia y enlaces.
6. En `/history` consulta las filas guardadas y las estadísticas.

## 12. Historial y privacidad

- Cada opción analizada se guarda en `resultados` si el guardado está activo.
- El historial se consulta en la web o con `scripts/history.py`.
- El bot guarda el estado de la conversación en `bot_sessions.db` por 24 horas.
- No se guardan audios ni transcripciones.
- Telegram no es cifrado de extremo a extremo para bots; evita enviar datos sensibles.
- Solo los IDs de la allowlist pueden usar el bot.

## 13. Solución de problemas

| Problema | Qué revisar |
|---|---|
| El bot no responde | Servicio activo, token correcto, conexión a internet. En VPS: `systemctl status compras-bot` y `journalctl -u compras-bot -f`. |
| Dice que no estás autorizado | Tu ID no está en `TELEGRAM_ALLOWED_USER_IDS`. |
| No entiende la consulta | Escribe producto, tiendas y presupuesto en un mensaje; o usa `/nuevo`. |
| No transcribe la voz | Dependencias de voz instaladas, audio menor a 120 s y formato compatible. |
| No llega el audio | Revisa `/voz`; puede fallar la red o `edge-tts`. El texto debe llegar igual. |
| Respuesta muy lenta | Usa `/modo fast`, reduce el límite o espera a que termine la búsqueda. |
| Gemini agotado | Cambia a `fast`; el bot seguirá funcionando. |
| Precios raros o mock | Configura `TAVILY_API_KEY`; los mock son sintéticos. |
| El bot quedó atascado | Usa `/cancelar` y luego `/nuevo`. |

## 14. Referencias

- Bot y despliegue: [`10_bot_telegram.md`](10_bot_telegram.md).
- API: [`04_api.md`](04_api.md).
- Frontend: [`05_frontend.md`](05_frontend.md).
- Decisiones: [`08_decisiones_tecnicas.md`](08_decisiones_tecnicas.md).
