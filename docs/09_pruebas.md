# Pruebas

> Estado: Fase 8 completada y bot cerrado (texto, voz y despliegue). Backend con pytest y cobertura; frontend con Vitest, ESLint y build de Next.js; bot con 76 pruebas.

## 1. Estrategia

La suite combina pruebas unitarias, de integración y de contrato HTTP:

| Capa | Herramienta | Alcance |
|---|---|---|
| Providers | pytest | Mock, servicio de búsqueda, Tavily con cliente falso, normalización de precios y reseñas. |
| Agentes y grafo | pytest | Ruteo del supervisor, precios, reseñas, audiencia, validación, síntesis, persistencia y fallbacks. |
| Base de datos | pytest + SQLite temporal | Guardado, historial, filtros, estadísticas, sesión y errores de persistencia. |
| API | pytest + FastAPI TestClient | Validación, análisis, SSE, historial, estadísticas y errores. |
| LLM y configuración | pytest | Parseo JSON, contenido multimodal, construcción del modelo y settings. |
| Bot | pytest | Parser, conversación, sesiones SQLite, formatter, voz, rate limit y handlers con dobles. |
| Frontend | Vitest | Utilidades de formato y parser SSE del cliente API. |
| Calidad estática | ESLint + TypeScript | Lint y compilación de producción de Next.js. |

Las pruebas no usan claves reales ni red: Tavily, Gemini y el grafo se sustituyen por clientes falsos o mocks. La base de datos de prueba vive en `tmp_path`.

## 2. Backend

### Archivos de prueba

| Archivo | Pruebas | Cobertura funcional |
|---|---:|---|
| `test_agents.py` | 14 | Precios con presupuesto, supervisor, validador, audiencia, síntesis, búsqueda y modelos. |
| `test_api.py` | 11 | Endpoints, SSE, validación, presupuesto y dependencia del repositorio. |
| `test_config.py` | 3 | Rutas SQLite y CORS. |
| `test_db.py` | 11 | Repositorio, filtros, estadísticas, sesión y persistencia. |
| `test_factory.py` | 2 | Providers Tavily/mock según API key. |
| `test_graph.py` | 5 | Flujo completo, LLM falso, fallo de búsqueda y construcción del grafo. |
| `test_health.py` | 3 | Health, metadatos y lifespan. |
| `test_llm.py` | 7 | `content_to_text`, JSON, `invoke_text/json` y `build_llm`. |
| `test_providers.py` | 7 | Mock, fallback, deduplicación, precios, rating y títulos. |
| `test_tavily_provider.py` | 4 | Búsqueda normalizada, filtros, límite y helpers. |
| `bot/test_parser.py` | 8 | Producto, tiendas, presupuesto, perfil, límite y casos límite. |
| `bot/test_conversation.py` | 8 | Slots, estados, confirmación, cancelación y kwargs. |
| `bot/test_session_store.py` | 5 | Roundtrip, actualización, aislamiento, expiración y purga. |
| `bot/test_formatter.py` | 6 | Agrupación, top 3, enlaces, mensajes largos y URLs inseguras. |
| `bot/test_handlers.py` | 21 | Allowlist, comandos, rate limit, callbacks, voz y flujo con grafo falso. |
| `bot/test_voice.py` | 24 | STT/TTS, PyAV, conversión, fallbacks y limpieza de temporales. |
| `bot/test_main.py` | 3 | Validación de token/allowlist y arranque con polling falso. |
| `bot/test_runner.py` | 1 | Ejecución del análisis en hilo con doble. |
| **Total** | **143** | 67 base + 76 del bot. |

`backend/.coveragerc` limita la medición a `app/` y omite las plantillas de prompts.

### Comandos

```bash
cd backend
../.venv/Scripts/python.exe -m pytest -q
../.venv/Scripts/python.exe -m pytest --cov=app --cov-report=term-missing -q
```

### Resultado

- **143 pruebas en verde** (67 base + 76 del bot).
- **Cobertura total: 90.6%** (ramas incluidas).
- Archivos con cobertura completa: `api/routes.py`, `api/schemas.py`, `db/repository.py`, `graph/builder.py`, `agents/supervisor.py`, `agents/persistence_agent.py`, `main.py` y `models.py`.
- Módulos con mayor margen: `agents/audience_agent.py` (75.8%), `agents/synthesis_agent.py` (77.7%) y `agents/review_agent.py` (89.4%), por ramas de sanitización y prompts que no se ejercitan sin un LLM real.
- El presupuesto se prueba con opciones dentro y fuera del límite; la API rechaza valores negativos.

## 3. Frontend

### Pruebas unitarias

| Archivo | Pruebas | Alcance |
|---|---:|---|
| `src/lib/utils.test.ts` | 7 | `isRecord`, `toStringArray`, `extractPasos`, moneda, fecha y score. |
| `src/lib/api.test.ts` | 4 | SSE fragmentado, evento `error`, error HTTP y query strings. |
| **Total** | **11** | |

Vitest se ejecuta en entorno Node y usa `fetch` y `ReadableStream` nativos. No requiere navegador ni backend levantado.

### Comandos

```bash
cd frontend
npm test
npm run lint
npm run build
```

### Resultado

- **11 pruebas en verde**.
- `npm run lint` sin errores.
- `npm run build` compila TypeScript y prerenderiza `/`, `/_not-found` y `/history`.
- `npm audit --omit=dev` no reporta vulnerabilidades en dependencias de producción.
- No se configuró cobertura de frontend; el foco está en las utilidades puras y el parser SSE.

## 4. QA manual

Con el backend en `http://localhost:8000` y el frontend en `http://localhost:3000`:

1. Abrir `/` y ejecutar una consulta con SSE activo; verificar nodos, traza y resultado.
2. Repetir con SSE desactivado; el resultado debe ser equivalente.
3. Cancelar una consulta en curso; no debe quedar un error visible.
4. Ajustar el presupuesto y confirmar que la recomendación, la tabla y los enlaces reflejan el filtro.
5. Ejecutar con `usar_llm=false` y `guardar=true`; confirmar filas en `/history`.
6. Filtrar el historial por producto y revisar las tarjetas de estadísticas.
7. Simular backend caído y verificar el aviso `role="alert"` en ambas páginas.

Comandos de humo:

```bash
curl http://localhost:8000/api/health
curl "http://localhost:8000/api/history?limit=5"
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"producto":"laptop","limite_por_tienda":2,"presupuesto":13000,"usar_llm":false,"guardar":false}'
```

## 5. Bot de Telegram

Las pruebas del bot no usan red, modelos reales ni llamadas a Telegram:

| Archivo | Alcance |
|---|---|
| `backend/tests/bot/test_parser.py` | Producto, tiendas, presupuesto, perfil y modo. |
| `backend/tests/bot/test_conversation.py` | Slots, estados, confirmación y cancelación. |
| `backend/tests/bot/test_session_store.py` | Persistencia, expiración y aislamiento por usuario. |
| `backend/tests/bot/test_formatter.py` | Top 3, enlaces, división de mensajes y audio. |
| `backend/tests/bot/test_voice.py` | STT/TTS, PyAV, conversión, fallbacks y limpieza. |
| `backend/tests/bot/test_handlers.py` | Allowlist, comandos, rate limit, voz y flujo con grafo falso. |

Casos mínimos:

- Un usuario fuera de la allowlist no ejecuta análisis.
- El parser completa tiendas por defecto y respeta el presupuesto.
- Cancelar durante `CONFIRMANDO` no llama al grafo.
- El formateador agrupa por producto y no repite el mismo modelo.
- Los mensajes largos se dividen sin romper enlaces.
- Si falla TTS, la respuesta de texto se envía igual.
- Las sesiones expiran y no se mezclan entre usuarios.

QA manual en Telegram real (pendiente de ejecutar):

1. `/start` y consulta con producto, tiendas y presupuesto.
2. Consulta sin producto: el bot debe preguntarlo.
3. Confirmar, cancelar y reintentar.
4. Cambiar a `/modo fast` y verificar que no se llama a Gemini.
5. Enviar nota de voz y revisar la transcripción.
6. Verificar enlaces y top 3, sin productos duplicados.
7. Comprobar que el servicio `systemd` reinicia tras un fallo simulado.

Los conteos actualizados son 143 backend (76 del bot) y 11 frontend.

## 6. Limitaciones

- No hay pruebas E2E de navegador ni de componentes React.
- No se mide cobertura del frontend.
- Tavily y Gemini se simulan; no se validan cuotas ni respuestas reales en la suite.
- La integración con MySQL no se prueba automáticamente; el repositorio se valida con SQLite temporal.
- No hay pruebas de carga, seguridad ofensiva ni accesibilidad automatizada.
- La voz usa PyAV; si falla la decodificación o `edge-tts`, el texto sigue disponible y el TTS cae a MP3.

## 7. Referencias

- API: [`04_api.md`](04_api.md).
- Frontend: [`05_frontend.md`](05_frontend.md).
- Base de datos: [`03_base_de_datos.md`](03_base_de_datos.md).
- Bot de Telegram: [`10_bot_telegram.md`](10_bot_telegram.md).
