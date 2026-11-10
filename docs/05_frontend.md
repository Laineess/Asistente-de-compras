# Frontend

> Estado: completado en la Fase 7. Implementado con Next.js 16, React 19, TypeScript y Tailwind CSS 4.

## 1. Stack y configuración

| Elemento | Versión / decisión |
|---|---|
| Framework | Next.js `16.4.5` con App Router y Turbopack |
| UI | React `19.3.0` |
| Lenguaje | TypeScript en modo estricto |
| Estilos | Tailwind CSS 4 con `@tailwindcss/turbopack` |
| Lint | ESLint 9 + `eslint-config-next` |
| API | `fetch` nativo y `ReadableStream` para SSE |

`frontend/next.config.ts` habilita `cacheComponents` y `partialPrefetching`, y fija la raíz de Turbopack en el directorio del frontend. El alias `@/*` apunta a `src/*` desde `tsconfig.json`.

### Variables de entorno

| Variable | Valor por defecto | Uso |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | URL base de la API FastAPI. |

El archivo `frontend/.env.local` se usa para desarrollo y está ignorado por git. Si la variable no existe, el cliente usa `http://localhost:8000`.

## 2. Rutas

| Ruta | Tipo | Descripción |
|---|---|---|
| `/` | Client Component | Buscador, selección de tiendas, progreso del agente y resultados. |
| `/history` | Client Component | Historial persistido, filtro por producto y estadísticas. |

Ambas páginas consumen la API desde el navegador. No se hacen peticiones al backend durante el build, por lo que `npm run build` no requiere que FastAPI esté levantado.

## 3. Estructura

```text
frontend/
├─ src/
│  ├─ app/
│  │  ├─ layout.tsx          # layout raíz, navegación y metadatos
│  │  ├─ page.tsx            # página de análisis
│  │  ├─ globals.css         # Tailwind, tema y variables CSS
│  │  └─ history/page.tsx    # historial y estadísticas
│  ├─ components/
│  │  ├─ SearchBar.tsx
│  │  ├─ StoreSelector.tsx
│  │  ├─ AgentProgress.tsx
│  │  ├─ AnalysisView.tsx
│  │  ├─ PriceSummaryCards.tsx
│  │  ├─ ComparisonTable.tsx
│  │  ├─ ReviewScoreGauge.tsx
│  │  ├─ AudienceList.tsx
│  │  ├─ HistoryTable.tsx
│  │  └─ StatsCards.tsx
│  └─ lib/
│     ├─ api.ts              # cliente HTTP y parser SSE
│     ├─ constants.ts        # tiendas, nodos y etiquetas
│     ├─ types.ts            # tipos de la API
│     └─ utils.ts            # formato y extracción de pasos
├─ next.config.ts
├─ package.json
└─ tsconfig.json
```

## 4. Cliente de API

`src/lib/api.ts` centraliza el acceso al backend:

| Función | Endpoint | Descripción |
|---|---|---|
| `analyze(payload, signal)` | `POST /api/analyze` | Ejecuta el análisis y devuelve el JSON completo. |
| `analyzeStream(payload, handlers)` | `POST /api/analyze/stream` | Lee el stream SSE y notifica `update`, `done` y `error`. |
| `fetchHistory(params)` | `GET /api/history` | Obtiene las filas persistidas con `limit` y `producto`. |
| `fetchStats(producto)` | `GET /api/stats` | Obtiene totales y promedios. |

El parser SSE acumula líneas `data:` hasta encontrar `\n\n`, valida el JSON y tolera eventos desconocidos. `AbortController` permite cancelar tanto la petición JSON como el stream.

### Eventos SSE

```text
event: update
data: {"nodos":["buscar","precios"],"data":{"pasos":["buscar: 3 opciones"]}}

event: done
data: {"resultado":{...},"pasos":[...],"errores":[],"advertencias":[],"filas_guardadas":3}

event: error
data: {"mensaje":"..."}
```

## 5. Componentes

| Componente | Responsabilidad |
|---|---|
| `SearchBar` | Formulario: producto, tiendas, límite, perfil, LLM, persistencia y modo SSE. |
| `StoreSelector` | Selección múltiple de Walmart, Costco y Sam's. |
| `AgentProgress` | Nodos del grafo y traza de pasos durante la ejecución. |
| `AnalysisView` | Orquesta recomendación, precios, comparación, reseñas, audiencia y avisos. |
| `PriceSummaryCards` | Precio mínimo, máximo, promedio y ahorro estimado. |
| `ComparisonTable` | Tabla responsive de opciones con tienda, precio, score, fuente y enlace. |
| `ReviewScoreGauge` | Score /10 con indicador circular, pros, contras y fuentes. |
| `AudienceList` | Perfiles de comprador con porcentaje y evidencia. |
| `HistoryTable` | Filas del historial con estados de carga y vacío. |
| `StatsCards` | Totales, rango de precios y promedio por comercio. |

## 6. Flujo de la página de análisis

1. El usuario escribe el producto, elige tiendas y ajusta opciones.
2. `SearchBar` valida que exista producto y al menos una tienda.
3. Con SSE activo, `analyzeStream` actualiza `AgentProgress` en cada evento y muestra `AnalysisView` al recibir `done`.
4. Sin SSE, `analyze` devuelve la respuesta completa y se muestra el mismo resultado.
5. El botón **Cancelar** aborta la petición o el stream.
6. Los errores de red o de la API se muestran en un aviso con `role="alert"`.

La respuesta incluye `resultado`, `pasos`, `errores`, `advertencias` y `filas_guardadas`. Si el agente no genera resultado, la página muestra los errores devueltos.

## 7. Flujo del historial

1. `fetchHistory` y `fetchStats` se ejecutan en paralelo al montar la página.
2. El filtro por producto se envía como query string a ambos endpoints.
3. `StatsCards` se oculta mientras carga o si no hay filas.
4. `HistoryTable` muestra un estado vacío con enlace a `/` cuando no hay resultados.
5. Los botones **Limpiar** y **Actualizar** reinician la carga.

## 8. Estilos y accesibilidad

- Tailwind CSS 4 con diseño responsive y modo oscuro basado en `prefers-color-scheme`.
- Layout con cabecera fija, navegación entre `/` y `/history`, y pie de página.
- Variables CSS `--gauge-track` para el indicador de reseñas.
- Formularios con `label`, `sr-only`, foco visible y `role="alert"` en errores.
- Enlaces externos con `target="_blank"` y `rel="noopener noreferrer"`.
- Tablas con `scope="col"` y desplazamiento horizontal en pantallas pequeñas.

## 9. Scripts

```bash
cd frontend
npm install
npm run dev      # http://localhost:3000
npm test
npm run lint
npm run build
npm run start
```

Verificación actual:

- `npm test` ejecuta 11 pruebas de Vitest.
- `npm run lint` sin errores.
- `npm run build` compila TypeScript y genera `/` y `/history` como páginas estáticas.

## 10. Limitaciones

- Sin autenticación ni multiusuario.
- Sin pruebas de componentes ni E2E; las pruebas cubren utilidades y el parser SSE.
- Sin selector manual de tema claro/oscuro.
- Sin internacionalización; la interfaz está en español.
- El historial se limita a las últimas 50 filas desde la interfaz.

## 11. Referencias

- Contrato de la API: [`04_api.md`](04_api.md).
- Visión general: [`01_arquitectura.md`](01_arquitectura.md).
- Guía de Next.js 16 incluida en `frontend/AGENTS.md`.
