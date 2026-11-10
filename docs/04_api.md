# API HTTP

> Estado: completado en la Fase 6. Implementación en `backend/app/api/`.

La API expone el grafo multiagente, el historial y las estadísticas de precios. FastAPI genera la documentación interactiva en `http://localhost:8000/docs`.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Metadatos de la aplicación y enlaces principales. |
| `GET` | `/api/health` | Estado del servicio y entorno. |
| `POST` | `/api/analyze` | Ejecuta el análisis completo y devuelve el resultado. |
| `POST` | `/api/analyze/stream` | Igual que el anterior, con progreso por SSE. |
| `GET` | `/api/history` | Últimas filas de `resultados`, con filtro opcional por producto. |
| `GET` | `/api/stats` | Totales, mínimo, máximo, promedio y desglose por comercio. |

## Ejecutar el servidor

```bash
cd backend
../.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

Al arrancar, el `lifespan` llama a `init_db()` y crea la tabla `resultados` si no existe (SQLite por defecto).

## `POST /api/analyze`

### Request

```json
{
  "producto": "laptop",
  "tiendas": ["walmart", "costco", "sams"],
  "limite_por_tienda": 3,
  "perfil": "estudiante universitario",
  "usar_llm": true,
  "guardar": true
}
```

| Campo | Tipo | Default | Reglas |
|---|---|---|---|
| `producto` | string | — | 1 a 200 caracteres. |
| `tiendas` | string[] | las tres tiendas | Valores: `walmart`, `costco`, `sams`. |
| `limite_por_tienda` | int | `3` | Entre 1 y 10. |
| `perfil` | string \| null | `null` | Texto libre para el análisis de audiencia. |
| `usar_llm` | bool | `true` | `false` usa solo heurísticas (sin Gemini). |
| `guardar` | bool | `true` | `false` omite la persistencia. |

### Response `200`

```json
{
  "resultado": {
    "producto": "laptop",
    "tiendas": ["walmart", "costco", "sams"],
    "opciones": [
      {
        "nombre": "Laptop Lenovo IdeaPad 3",
        "comercio": "walmart",
        "precio": "10999.00",
        "moneda": "MXN",
        "url": "https://example.com/producto",
        "descripcion": "Laptop para estudio y trabajo.",
        "calificacion": 4.4,
        "resenas": [],
        "fuente": "mock"
      }
    ],
    "resumen_precios": {
      "precio_final": "10999.00",
      "opcion_recomendada": "Laptop Lenovo IdeaPad 3",
      "precio_promedio": "11500.00",
      "precio_minimo": "10999.00",
      "precio_maximo": "12000.00",
      "rango": "1001.00",
      "moneda": "MXN",
      "opciones_consideradas": 3,
      "comercio_mas_barato": "Walmart",
      "comercio_mas_caro": "Costco"
    },
    "resumen_resenas": {
      "score": 8.1,
      "resenas_analizadas": 3,
      "sintesis": "Buena relación calidad-precio.",
      "pros": ["Precio"],
      "contras": ["Peso"],
      "fuentes": ["Walmart", "Costco"]
    },
    "usuarios_relevantes": {
      "perfiles": [
        {
          "perfil": "Estudiante",
          "descripcion": "Equipo suficiente para tareas y clases.",
          "evidencia": "Precio y portabilidad.",
          "porcentaje": 75
        }
      ],
      "sintesis": "Perfil principal: estudiante."
    },
    "recomendacion": "Conviene la opción de Walmart por precio y reseñas.",
    "advertencias": [],
    "filas_guardadas": 3,
    "errores": [],
    "fecha_consulta": "2026-11-09T10:30:00"
  },
  "pasos": ["supervisor:buscar", "buscador:3 opciones", "sintetizar:ok", "validar:ok", "persistir:3 filas"],
  "errores": [],
  "advertencias": [],
  "filas_guardadas": 3
}
```

Los `Decimal` se serializan como cadenas para no perder precisión.

### Errores

| Código | Cuándo |
|---|---|
| `422` | Body inválido (producto vacío, límite fuera de rango, tienda desconocida). |
| `502` | El grafo terminó sin `resultado`; el detalle incluye `errores`. |

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"producto":"laptop","limite_por_tienda":2,"usar_llm":false}'
```

## `POST /api/analyze/stream`

Mismo request que `/api/analyze`. Responde `text/event-stream` con eventos SSE:

```text
data: {"event": "update", "nodos": ["supervisor"], "data": {...}}

data: {"event": "update", "nodos": ["buscar"], "data": {...}}

data: {"event": "done", "resultado": {...}, "pasos": [...], "errores": [], "advertencias": [], "filas_guardadas": 3}
```

Si el grafo falla durante la ejecución se emite `{"event": "error", "mensaje": "..."}` y se cierra el stream.

```bash
curl -N -X POST http://localhost:8000/api/analyze/stream \
  -H "Content-Type: application/json" \
  -d '{"producto":"laptop","limite_por_tienda":1,"usar_llm":false}'
```

## `GET /api/history`

| Query | Tipo | Default | Reglas |
|---|---|---|---|
| `limit` | int | `50` | Entre 1 y 200. |
| `producto` | string \| null | `null` | Búsqueda parcial sin distinguir mayúsculas. |

```bash
curl "http://localhost:8000/api/history?limit=10&producto=laptop"
```

```json
[
  {
    "id": 12,
    "nombre_producto": "Laptop Lenovo IdeaPad 3",
    "comercio": "Walmart",
    "precio": "10999.00",
    "fecha_consulta": "2026-11-09T10:30:00"
  }
]
```

## `GET /api/stats`

| Query | Tipo | Default | Reglas |
|---|---|---|---|
| `producto` | string \| null | `null` | Búsqueda parcial sin distinguir mayúsculas. |

```bash
curl "http://localhost:8000/api/stats?producto=laptop"
```

```json
{
  "producto": "laptop",
  "total": 9,
  "precio_minimo": "10999.00",
  "precio_maximo": "13500.50",
  "precio_promedio": "12150.25",
  "por_comercio": [
    { "comercio": "Costco", "total": 3, "precio_promedio": "13000.00" },
    { "comercio": "Sam's", "total": 3, "precio_promedio": "12500.00" },
    { "comercio": "Walmart", "total": 3, "precio_promedio": "11000.00" }
  ]
}
```

## CORS y configuración

- Orígenes permitidos: `CORS_ORIGINS` (default `http://localhost:3000`).
- Base de datos: `DATABASE_URL` (SQLite por defecto).
- Las claves `GEMINI_API_KEY` y `TAVILY_API_KEY` viven en `.env`, ignorado por git.

## Pruebas

`backend/tests/test_api.py` cubre el análisis (con grafo mockeado), el error `502`, historial, estadísticas, validación de `limit` y el stream SSE. La suite completa tiene **23 pruebas** en verde.
