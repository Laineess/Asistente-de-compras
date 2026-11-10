# Análisis de Compras — Agente Multiagente

Asistente que ayuda a decidir qué producto comprar consultando precios y reseñas en **Walmart**, **Costco** y **Sam's**, y registrando cada consulta en una base de datos.

## Stack

- **Backend:** Python 3.12, FastAPI, LangGraph, LangChain, Gemini, Tavily, SQLAlchemy.
- **Frontend:** Next.js 16, TypeScript, Tailwind CSS.
- **Base de datos:** SQLite en desarrollo / MySQL en la entrega (configurable con `DATABASE_URL`).
- **Documentación:** Markdown y exportación a PDF con WeasyPrint.

## Estructura

```
analisis-compras/
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ config.py
│  │  ├─ models.py     # modelos Pydantic de dominio
│  │  ├─ llm.py        # cliente Gemini
│  │  ├─ api/         # esquemas y rutas FastAPI
│  │  ├─ graph/       # estado y orquestación LangGraph
│  │  ├─ agents/      # buscador, precios, reseñas, audiencia, síntesis
│  │  ├─ tools/       # herramientas de cada agente
│  │  ├─ providers/   # Tavily + mock por tienda
│  │  ├─ db/          # modelos ORM, sesión, repositorio e init.sql
│  │  └─ prompts/     # plantillas de los agentes
│  ├─ data/mock/      # datos de respaldo
│  ├─ tests/
│  └─ requirements.txt
├─ frontend/
│  ├─ src/app/        # páginas / y /history
│  ├─ src/components/ # componentes de UI
│  └─ src/lib/        # tipos, cliente API y utilidades
├─ docs/              # documentación del proyecto
├─ scripts/           # utilidades
├─ .env.example
└─ README.md
```

## Requisitos

- Python 3.12+
- Node.js 20+
- API keys: `GEMINI_API_KEY` (Google AI Studio) y `TAVILY_API_KEY`.

## Configuración

1. Copia `.env.example` a `.env` y completa las API keys. `.env` contiene secretos reales y está ignorado por git; solo `.env.example` se versiona.
2. Backend:
   ```bash
   python -m venv .venv
   .venv/Scripts/activate
   pip install -r backend/requirements.txt
   cd backend
   uvicorn app.main:app --reload
   ```
3. Frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

   Opcional: crea `frontend/.env.local` con `NEXT_PUBLIC_API_URL=http://localhost:8000` si el backend usa otra URL.

- Backend: http://localhost:8000 (Swagger en `/docs`)
- Frontend: http://localhost:3000

## API

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/analyze` | Ejecuta el análisis completo. |
| `POST` | `/api/analyze/stream` | Progreso del análisis por SSE. |
| `GET` | `/api/history` | Historial persistido (filtro `producto`, `limit`). |
| `GET` | `/api/stats` | Totales y promedios por comercio. |
| `GET` | `/api/health` | Estado del servicio. |

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"producto":"laptop","limite_por_tienda":2,"usar_llm":false}'

curl "http://localhost:8000/api/history?limit=10&producto=laptop"
```

Detalle de esquemas, SSE y errores en [`docs/04_api.md`](docs/04_api.md).

## Base de datos

Por defecto se usa SQLite en `backend/data/analisis_compras.db` (ignorado por git). Para MySQL, ajusta `DATABASE_URL` en `.env` y ejecuta `backend/app/db/init.sql`.

```bash
# Ver historial persistido
.venv/Scripts/python.exe scripts/history.py --limite 20

# Insertar datos de ejemplo (--limpiar borra los existentes)
.venv/Scripts/python.exe scripts/seed.py --limpiar

# Vaciar la tabla de resultados
.venv/Scripts/python.exe scripts/clear.py --yes
```

El agente guarda una fila por opción analizada al ejecutar `scripts/run_agent.py`. Usa `--sin-db` para omitir la persistencia.

## Documentación

- [Glosario](docs/00_glosario.md)
- [Arquitectura](docs/01_arquitectura.md)
- [Base de datos](docs/03_base_de_datos.md)
- [API](docs/04_api.md)
- [Frontend](docs/05_frontend.md)
- [Decisiones técnicas (ADRs)](docs/08_decisiones_tecnicas.md)
- Índice completo: [docs/](docs/README.md)

## Pruebas

```bash
cd backend
../.venv/Scripts/python.exe -m pytest -q
```

Prueba manual de la capa de datos (sin LLM):

```bash
.venv/Scripts/python.exe scripts/search_demo.py "laptop" --limite 3
```

Prueba del agente multiagente:

```bash
# Con Gemini + Tavily
.venv/Scripts/python.exe scripts/run_agent.py "laptop" --limite 3

# Sin Gemini (recomendado si se agota la cuota gratuita)
.venv/Scripts/python.exe scripts/run_agent.py "laptop" --limite 3 --sin-llm

# Salida JSON
.venv/Scripts/python.exe scripts/run_agent.py "laptop" --limite 3 --json

# Omitir la persistencia
.venv/Scripts/python.exe scripts/run_agent.py "laptop" --limite 3 --sin-db
```

> Gemini free tier: 20 solicitudes/día. El agente usa heurísticas si se agota la cuota.

La suite completa tiene 23 pruebas en verde.

Verificación del frontend:

```bash
cd frontend
npm run lint
npm run build
```

## Estado del proyecto

- [x] Fase 1 — Scaffolding
- [x] Fase 2 — Documentación base y diseño
- [x] Fase 3 — Capa de datos (providers)
- [x] Fase 4 — Grafo multiagente
- [x] Fase 5 — Persistencia
- [x] Fase 6 — API FastAPI
- [x] Fase 7 — Frontend Next.js
- [ ] Fase 8 — Pruebas y QA
- [ ] Fase 9 — Investigación y PDF
- [ ] Fase 10 — Empaquetado y entrega

La documentación vive en [`docs/`](docs/README.md).
