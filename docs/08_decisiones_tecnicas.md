# Decisiones técnicas (ADRs)

Registro de decisiones de arquitectura. Formato: contexto, decisión, alternativas y consecuencias.

---

## ADR-001 — Orquestación con LangGraph

- **Estado:** Aceptada
- **Fecha:** 2026-11-08

**Contexto**
El flujo requiere varios pasos dependientes (búsqueda, precios, reseñas, audiencia, persistencia), estado compartido y posible reintento o salto de pasos. Una cadena lineal se queda corta.

**Decisión**
Usar LangGraph con un `StateGraph` tipado, nodos por responsabilidad y aristas condicionales gobernadas por un supervisor.

**Alternativas consideradas**
- Cadenas LCEL puras: simples, pero sin ciclos ni estado rico.
- Orquestación manual en Python: control total, pero sin trazabilidad ni checkpointing.
- CrewAI o AutoGen: más abstracción, menor control del flujo.

**Consecuencias**
- Positivas: estado explícito, ciclos, visualización del grafo, base para checkpointing y HITL.
- Negativas: curva de aprendizaje y cambios frecuentes de versión. Se mitiga fijando versiones en `requirements.lock.txt`.

---

## ADR-002 — Arquitectura multiagente con supervisor

- **Estado:** Aceptada
- **Fecha:** 2026-11-08

**Contexto**
El enunciado define cuatro acciones diferenciadas. Conviene separar responsabilidades para facilitar pruebas y mantenimiento.

**Decisión**
Un supervisor enruta a los agentes especializados (buscador, precios, reseñas, audiencia y síntesis); el flujo termina con el validador y el nodo de persistencia. Cada agente tiene su propio prompt y herramientas.

**Alternativas consideradas**
- Un solo agente ReAct con todas las herramientas: más simple, pero menos modular.
- Pipeline fijo sin supervisor: predecible, pero rígido.
- Jerarquía de subgrafos: potente, innecesaria para este alcance.

**Consecuencias**
- Positivas: separación de responsabilidades, pruebas unitarias por agente, mapeo directo al enunciado.
- Negativas: más llamadas al LLM (latencia y costo). Se mitiga con salidas estructuradas, caché opcional y ruta determinista de respaldo.

---

## ADR-003 — Gemini como LLM

- **Estado:** Aceptada
- **Fecha:** 2026-11-08

**Contexto**
Se necesita un LLM con salida estructurada, disponible sin costo inicial y compatible con LangChain.

**Decisión**
Usar Google Gemini mediante `langchain-google-genai`, con modelo configurable en `GEMINI_MODEL` (por defecto `gemini-3.8-flash`). El cliente se configura con transporte REST para evitar bloqueos del cliente gRPC al cerrar procesos en Windows.

**Alternativas consideradas**
- OpenAI GPT: buena calidad, requiere pago.
- Anthropic Claude: buena calidad, requiere pago.
- Ollama local: sin costo por API, pero requiere hardware y descarga de modelos.

**Consecuencias**
- Positivas: free tier, baja latencia, integración directa con LangChain.
- Negativas: límites de tasa y de contexto; dependencia de servicio externo. Se mitiga con reintentos, timeouts y fallback determinista.
- Free tier de `gemini-3.8-flash`: 20 solicitudes/día. Al agotarse, el agente usa heurísticas y no falla.

---

## ADR-004 — Tavily con respaldo mock

- **Estado:** Aceptada
- **Fecha:** 2026-11-08

**Contexto**
Walmart, Costco y Sam's bloquean scraping automatizado y no ofrecen APIs públicas gratuitas. La demo debe funcionar aunque la fuente real falle.

**Decisión**
Implementar una interfaz `StoreProvider` con dos implementaciones: `TavilyProvider` (datos reales) y `MockProvider` (datos locales). El servicio intenta Tavily y cae a mock si hay error, sin resultados o falta la API key.

**Alternativas consideradas**
- Scraping con Playwright: frágil, lento y con riesgo de bloqueo o incumplimiento de términos.
- Solo mock: demo estable, pero sin datos reales.
- SerpAPI u otros: requieren pago o cuotas.

**Consecuencias**
- Positivas: demo confiable, separación entre fuente y lógica, pruebas sin red.
- Negativas: los datos reales pueden no coincidir exactamente con el precio en tienda; el mock es sintético y debe declararse como tal.

---

## ADR-005 — SQLAlchemy con SQLite en desarrollo y MySQL en entrega

- **Estado:** Aceptada
- **Fecha:** 2026-11-08

**Contexto**
El enunciado exige MySQL local (`analisis_compras`), pero el servidor MySQL no está corriendo como servicio y se necesita avanzar sin bloqueos.

**Decisión**
Usar SQLAlchemy 2.0 y seleccionar el motor con `DATABASE_URL`. SQLite para desarrollo y MySQL 8.0 para la entrega. El DDL de MySQL vive en `backend/app/db/init.sql`. La implementación está en `backend/app/db/` (modelo `Resultado`, sesión y `ResultadoRepository`) y en el nodo `persistir` del grafo.

**Alternativas consideradas**
- Solo MySQL: cumple el requisito, pero bloquea el desarrollo.
- Solo SQLite: simple, pero no cumple el enunciado.
- SQL crudo por motor: duplica lógica.

**Consecuencias**
- Positivas: mismo modelo y código para ambos motores; migración por configuración.
- Negativas: hay que validar el flujo en MySQL antes de entregar (tipos, zona horaria, charset). Se documenta en `03_base_de_datos.md`.
- La persistencia es *best-effort*: si la base de datos falla, el agente devuelve el resultado con una advertencia en lugar de fallar por completo.

---

## ADR-006 — Backend FastAPI y frontend Next.js separados

- **Estado:** Aceptada
- **Fecha:** 2026-11-08

**Contexto**
El agente vive en Python y se eligió React/Next.js para la interfaz. Se requiere una API intermedia.

**Decisión**
FastAPI expone el grafo por HTTP y SSE; Next.js 16 consume la API. CORS restringido a `http://localhost:3000` en desarrollo.

**Alternativas consideradas**
- Streamlit o Gradio: más rápidos, pero no usan React.
- Django: más pesado para una API pequeña.
- Monolito con plantillas: menos flexible.

**Consecuencias**
- Positivas: separación clara, UI profesional, posibilidad de streaming de progreso.
- Negativas: dos servidores y configuración de CORS/entornos. Se documenta el arranque en el README.

---

## ADR-007 — Documentación en Markdown y PDF con WeasyPrint

- **Estado:** Aceptada
- **Fecha:** 2026-11-08

**Contexto**
Se debe entregar un PDF de investigación. No hay Pandoc ni LaTeX instalados; WeasyPrint ya está disponible.

**Decisión**
Escribir la documentación en Markdown y exportar el PDF con `scripts/export_pdf.py` (Markdown → HTML + CSS → WeasyPrint).

**Alternativas consideradas**
- LaTeX: mejor tipografía, pero requiere instalación pesada.
- Word/DOCX: editable, pero difícil de versionar.
- Pandoc: no instalado.

**Consecuencias**
- Positivas: documentación versionable, exportación reproducible, sin dependencias externas pesadas.
- Negativas: control tipográfico limitado; requiere CSS dedicado para tablas, saltos de página y encabezados.

---

## ADR-008 — Salidas estructuradas con Pydantic

- **Estado:** Aceptada
- **Fecha:** 2026-11-08

**Contexto**
El agente debe producir datos consumibles por la API y la base de datos: opciones, precios y scores.

**Decisión**
Definir modelos Pydantic (`ProductOption`, `PriceSummary`, `ReviewSummary`, `AudienceSummary`, `AnalysisResult`) y validar la salida del LLM contra ellos, con reintento si falla la validación.

**Alternativas consideradas**
- Parseo de texto libre con expresiones regulares: frágil.
- Solo function calling: útil, pero insuficiente para validar el resultado final.
- Sin validación: riesgo de errores silenciosos.

**Consecuencias**
- Positivas: contratos claros, errores detectables, mejor integración con FastAPI.
- Negativas: mantenimiento de esquemas y posibles fallos de validación del modelo. Se mitiga con reintentos y respaldo determinista.

---

## ADR-009 — Credenciales en `.env`

- **Estado:** Aceptada
- **Fecha:** 2026-11-08

**Contexto**
Se manejan claves de Gemini y Tavily, además de credenciales de base de datos.

**Decisión**
Guardar secretos en `.env` local, ignorado por git. Versionar únicamente `.env.example` con marcadores de posición. `backend/app/config.py` carga el archivo con `pydantic-settings`.

**Alternativas consideradas**
- Hardcodear claves: riesgo de fuga.
- Variables de entorno del sistema: válido, pero menos portable.
- Gestor de secretos (Vault, AWS Secrets Manager): sobredimensionado para el alcance.

**Consecuencias**
- Positivas: simple, seguro para el repositorio, portable.
- Negativas: configuración manual y sin rotación automática. Para producción se recomendaría un gestor de secretos.

---

## ADR-010 — Sin autenticación en el MVP

- **Estado:** Aceptada
- **Fecha:** 2026-11-08

**Contexto**
Es un proyecto académico de demostración local; el enunciado no pide usuarios ni roles.

**Decisión**
No implementar autenticación en el MVP. Restringir CORS y validar todas las entradas con Pydantic.

**Alternativas consideradas**
- JWT con registro/login: agrega complejidad no solicitada.
- OAuth con proveedor externo: innecesario para la demo.

**Consecuencias**
- Positivas: menos complejidad y foco en el agente.
- Negativas: no apto para producción. Se documenta como limitación explícita.

---

## ADR-011 — Bot de Telegram como interfaz principal

- **Estado:** Aceptada
- **Fecha:** 2026-11-12

**Contexto**
La interfaz web funciona en escritorio, pero el uso diario ocurre en el móvil. Se necesita una experiencia sin instalar apps, con texto y voz, y sin exponer un servidor web propio.

**Decisión**
Implementar un bot privado de Telegram con `python-telegram-bot`, *long polling* y allowlist de IDs. El bot reutiliza `run_analysis()` y no pasa por FastAPI. Pregunta los datos faltantes, confirma antes de ejecutar y devuelve enlaces y el top 3.

**Alternativas consideradas**
- Web app móvil: requiere dominio, TLS, hosting y autenticación.
- WhatsApp Business API: más fricción y costos.
- App nativa: sobredimensionada para el alcance.
- Bot público: riesgo de abuso y consumo de cuota.

**Consecuencias**
- Positivas: acceso inmediato, notificaciones, voz nativa, sin puertos públicos ni frontend para móvil.
- Negativas: dependencia de Telegram, sin cifrado E2E para bots y límites de formato (4096 caracteres). Se mitiga dividiendo mensajes y usando allowlist/rate limit.

---

## ADR-012 — Voz local con faster-whisper y edge-tts

- **Estado:** Aceptada
- **Fecha:** 2026-11-12

**Contexto**
El usuario quiere dictar consultas y recibir audio corto por producto sin pagar APIs de voz ni enviar audio a servicios adicionales.

**Decisión**
Transcribir con `faster-whisper` (`small`, CPU, `int8`, español) y sintetizar con `edge-tts` (`es-MX-JorgeNeural`). La entrada se decodifica con PyAV y la salida se transcodifica a OGG/Opus con PyAV; si falla, se envía MP3. No se requiere `ffmpeg` del sistema. El audio es opcional y siempre va acompañado de texto.

**Alternativas consideradas**
- Whisper API de OpenAI: buena calidad, pero costo y dependencia externa.
- Google Speech-to-Text/TTS: costo y configuración de credenciales.
- Solo texto: más simple, pero no cumple el requisito de voz.
- Modelo `medium`/`large`: mejor transcripción, pero demasiado pesado para un VPS modesto.

**Consecuencias**
- Positivas: sin costo por uso, privacidad de la transcripción, control del modelo y sin dependencia de binarios externos.
- Negativas: consumo de CPU/RAM, descarga inicial del modelo y calidad variable. Se mitiga con `small`, límite de duración y fallback a texto si algo falla.

---

## ADR-013 — Despliegue con systemd sin Docker

- **Estado:** Aceptada
- **Fecha:** 2026-11-12

**Contexto**
El bot debe estar disponible 24/7 en un VPS Ubuntu. Docker añade capas y complejidad que no se necesitan para un único proceso Python.

**Decisión**
Desplegar con un usuario sin privilegios, `venv`, un servicio `systemd` con `Restart=on-failure` y *long polling*. No se abren puertos para el bot; solo se requiere salida HTTPS.

**Alternativas consideradas**
- Docker/Compose: reproducible, pero más piezas y permisos.
- `nohup` o `screen`: simple, pero sin reinicio ni logs gestionados.
- Kubernetes: sobredimensionado.

**Consecuencias**
- Positivas: operación simple, logs con `journalctl`, arranque automático y menos superficie de ataque.
- Negativas: dependencia del sistema operativo y actualización manual. Se documenta el procedimiento en `10_bot_telegram.md`.

---

## ADR-014 — Modo `fast` por defecto

- **Estado:** Aceptada
- **Fecha:** 2026-11-12

**Contexto**
El free tier de Gemini permite 20 solicitudes/día. Un bot conversacional puede agotarlo con facilidad y dejar al usuario sin respuestas.

**Decisión**
Usar `fast` por defecto: búsqueda con Tavily/mock y heurísticas, sin Gemini. El modo `detallado` se activa manualmente con `/modo` y consume cuota. Si Gemini falla en `detallado`, se cae a heurísticas.

**Alternativas consideradas**
- `detallado` por defecto: mejor texto, pero agota la cuota rápido.
- Solo heurísticas: estable, pero sin la riqueza del LLM.
- Caché de respuestas: útil, pero no elimina el problema en consultas nuevas.

**Consecuencias**
- Positivas: disponibilidad estable, respuestas rápidas y menor costo.
- Negativas: recomendaciones menos elaboradas por defecto. El usuario puede subir de modo cuando lo necesite.
