# Documentación del proyecto

Índice de documentos. La documentación se construye por fases junto al código.

| Documento | Estado | Fase |
|---|---|---|
| [`00_glosario.md`](00_glosario.md) | Completado | 2 |
| [`01_arquitectura.md`](01_arquitectura.md) | Completado | 2 |
| [`02_agentes_y_langgraph.md`](02_agentes_y_langgraph.md) | Completado | 4 |
| [`03_base_de_datos.md`](03_base_de_datos.md) | Completado | 2-5 |
| [`04_api.md`](04_api.md) | Completado | 6 |
| [`05_frontend.md`](05_frontend.md) | Completado | 7 |
| [`06_manual_usuario.md`](06_manual_usuario.md) | Pendiente | 10 |
| [`07_investigacion_agentes.md`](07_investigacion_agentes.md) / `.pdf` | Pendiente | 9 |
| [`08_decisiones_tecnicas.md`](08_decisiones_tecnicas.md) | Completado | 2 |
| [`09_pruebas.md`](09_pruebas.md) | Pendiente | 8 |

## Estado de la Fase 2

- Arquitectura y diagramas definidos.
- Esquema de base de datos y `init.sql` listos.
- ADRs registradas.
- Glosario creado.

## Estado de la Fase 3

- Modelos de dominio en `backend/app/models.py`.
- Providers Tavily y mock con fallback automático.
- Servicio de búsqueda con normalización, deduplicación, top-up y orden por precio.
- Catálogo mock generado con `scripts/generate_mock_data.py`.
- Script de prueba `scripts/search_demo.py`.
- 8 pruebas en verde.

## Estado de la Fase 4

- Grafo LangGraph con supervisor y nodos de búsqueda, precios, reseñas, audiencia, síntesis y validación.
- Gemini 3.8 Flash con transporte REST y fallback heurístico.
- CLI `scripts/run_agent.py` con `--sin-llm` y `--json`.
- 13 pruebas en verde.

## Estado de la Fase 5

- Modelo ORM `Resultado` y sesión SQLAlchemy con SQLite/MySQL.
- `ResultadoRepository` con guardado, historial, conteo y limpieza.
- Nodo de persistencia en el grafo; `filas_guardadas` en la respuesta.
- Scripts `seed.py`, `clear.py` y `history.py`.
- 18 pruebas en verde.

## Estado de la Fase 6

- API FastAPI en `backend/app/api/` con `POST /api/analyze`, `POST /api/analyze/stream`, `GET /api/history` y `GET /api/stats`.
- Esquemas Pydantic de request/response y validación de parámetros.
- Stream SSE con eventos `update`, `done` y `error`.
- `lifespan` inicializa la base de datos al arrancar.
- 23 pruebas en verde (incluye `test_api.py`).

## Estado de la Fase 7

- Frontend Next.js 16 con rutas `/` y `/history`.
- Cliente de API con modo JSON y stream SSE, cancelación y manejo de errores.
- Componentes de búsqueda, progreso, comparación, reseñas, audiencia, historial y estadísticas.
- Layout responsive con navegación, metadatos en español y modo oscuro.
- `npm run lint` y `npm run build` sin errores.

## Convenciones

- Formato fuente: Markdown.
- Diagramas: Mermaid.
- Exportación a PDF: `scripts/export_pdf.py` (Markdown -> HTML -> WeasyPrint).
- Idioma: español.
- Los secretos viven en `.env` (ignorado por git); `.env.example` es la plantilla versionada.
