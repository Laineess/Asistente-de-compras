# Base de datos

> Estado: implementado en la Fase 5. El modelo ORM, la sesión y el repositorio viven en `backend/app/db/`; el grafo persiste al final del análisis.

## 1. Objetivo

Registrar cada opción de producto analizada para que el agente interactúe con una herramienta externa de persistencia y no se limite a la búsqueda.

El enunciado exige una base de datos **MySQL local** llamada `analisis_compras` y una tabla `resultados` con los campos:

- `nombre_producto`
- `comercio`
- `precio`
- `fecha_consulta`

## 2. Motores soportados

| Entorno | Motor | `DATABASE_URL` |
|---|---|---|
| Desarrollo | SQLite | `sqlite:///./backend/data/analisis_compras.db` |
| Entrega | MySQL 8.0 | `mysql+pymysql://app_user:password@localhost:3306/analisis_compras` |

El código usa **SQLAlchemy 2.0**, por lo que el mismo modelo funciona en ambos motores. La ruta relativa de SQLite se resuelve contra la raíz del proyecto en `backend/app/config.py`.

> Para la entrega se recomienda ejecutar con MySQL y dejar SQLite solo como entorno de desarrollo.

## 3. Esquema `analisis_compras`

### 3.1 Tabla `resultados`

| Campo | Tipo MySQL | Tipo SQLite | Nulo | Descripción |
|---|---|---|---|---|
| `id` | `INT AUTO_INCREMENT` | `INTEGER PRIMARY KEY AUTOINCREMENT` | No | Clave técnica (no requerida por el enunciado). |
| `nombre_producto` | `VARCHAR(255)` | `TEXT` | No | Producto consultado. |
| `comercio` | `VARCHAR(100)` | `TEXT` | No | `Walmart`, `Costco` o `Sam's`. |
| `precio` | `DECIMAL(12,2)` | `NUMERIC` | No | Precio final en pesos mexicanos. |
| `fecha_consulta` | `DATETIME` | `DATETIME` | No | Momento de la consulta. |

Los cuatro campos del enunciado están presentes. `id` se agrega como clave primaria técnica para evitar duplicados ambiguos y facilitar el historial.

### 3.2 Índices

| Índice | Campos | Uso |
|---|---|---|
| `idx_resultados_producto` | `nombre_producto` | Búsquedas por producto. |
| `idx_resultados_comercio` | `comercio` | Filtros por tienda. |
| `idx_resultados_fecha` | `fecha_consulta` | Historial ordenado por fecha. |

## 4. DDL MySQL

Archivo: [`backend/app/db/init.sql`](../backend/app/db/init.sql)

```sql
CREATE DATABASE IF NOT EXISTS analisis_compras
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE analisis_compras;

CREATE TABLE IF NOT EXISTS resultados (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre_producto VARCHAR(255) NOT NULL,
  comercio VARCHAR(100) NOT NULL,
  precio DECIMAL(12,2) NOT NULL,
  fecha_consulta DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_resultados_producto (nombre_producto),
  INDEX idx_resultados_comercio (comercio),
  INDEX idx_resultados_fecha (fecha_consulta)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;
```

## 5. DDL SQLite

SQLAlchemy crea la tabla automáticamente, pero el equivalente es:

```sql
CREATE TABLE IF NOT EXISTS resultados (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre_producto TEXT NOT NULL,
  comercio TEXT NOT NULL,
  precio NUMERIC NOT NULL,
  fecha_consulta DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_resultados_producto ON resultados (nombre_producto);
CREATE INDEX IF NOT EXISTS idx_resultados_comercio ON resultados (comercio);
CREATE INDEX IF NOT EXISTS idx_resultados_fecha ON resultados (fecha_consulta);
```

## 6. Mapeo ORM (SQLAlchemy 2.0)

Modelo implementado en [`backend/app/db/models.py`](../backend/app/db/models.py):

```python
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Index, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Resultado(Base):
    __tablename__ = "resultados"
    __table_args__ = (
        Index("idx_resultados_producto", "nombre_producto"),
        Index("idx_resultados_comercio", "comercio"),
        Index("idx_resultados_fecha", "fecha_consulta"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre_producto: Mapped[str] = mapped_column(String(255), nullable=False)
    comercio: Mapped[str] = mapped_column(String(100), nullable=False)
    precio: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fecha_consulta: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
```

### 6.1 Sesión y creación de tablas

`backend/app/db/session.py` crea el motor con `DATABASE_URL`, configura `pool_pre_ping` y usa `check_same_thread=False` solo para SQLite. `init_db()` ejecuta `Base.metadata.create_all()`; en MySQL crea la tabla si no existe y en SQLite crea el archivo y la tabla.

### 6.2 Repositorio

`backend/app/db/repository.py` expone `ResultadoRepository`:

| Método | Descripción |
|---|---|
| `save_result(result)` | Inserta una fila por cada `ProductOption` y devuelve el total. |
| `list_resultados(limit)` | Devuelve el historial ordenado por fecha descendente. |
| `count()` | Cuenta las filas de `resultados`. |
| `clear()` | Elimina todas las filas y devuelve cuántas borró. |

`build_default_repository()` llama a `init_db()` y construye el repositorio con `SessionLocal`.

```mermaid
flowchart LR
    G["Grafo: nodo persistir"] --> R["ResultadoRepository"]
    R --> S["SQLAlchemy Session"]
    S --> DB[("resultados")]
```

## 7. Operaciones

### 7.1 Inserción por opción

El nodo `persistir` llama a `ResultadoRepository.save_result(result)` e inserta una fila por cada `ProductOption` analizada. La fecha se toma de `AnalysisResult.fecha_consulta` y el comercio se guarda con su nombre visible (`Walmart`, `Costco`, `Sam's`). El total se refleja en `AnalysisResult.filas_guardadas` y en `AgentState["filas_guardadas"]`.

```sql
INSERT INTO resultados (nombre_producto, comercio, precio, fecha_consulta)
VALUES (:nombre_producto, :comercio, :precio, :fecha_consulta);
```

### 7.2 Historial

En código: `repo.list_resultados(limit=50, producto=None)`. Para la demo, `scripts/history.py`; por API, `GET /api/history`.

```sql
SELECT id, nombre_producto, comercio, precio, fecha_consulta
FROM resultados
ORDER BY fecha_consulta DESC
LIMIT 50;
```

### 7.3 Promedio por producto y comercio

En código: `repo.stats(producto=...)`, expuesto por `GET /api/stats`.

```sql
SELECT nombre_producto, comercio, AVG(precio) AS precio_promedio
FROM resultados
WHERE nombre_producto = :producto
GROUP BY nombre_producto, comercio;
```

### 7.4 Rango de precios

```sql
SELECT MIN(precio) AS minimo, MAX(precio) AS maximo, AVG(precio) AS promedio
FROM resultados
WHERE nombre_producto = :producto;
```

## 8. Usuario de aplicación (MySQL)

Para la entrega se recomienda no usar `root`:

```sql
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'CAMBIAR_ESTA_CLAVE';
GRANT SELECT, INSERT, UPDATE, DELETE ON analisis_compras.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
```

## 9. Migración SQLite → MySQL

1. Cambiar `DATABASE_URL` en `.env` al DSN de MySQL.
2. Ejecutar `backend/app/db/init.sql` con MySQL Workbench o `mysql`.
3. Reiniciar el backend; SQLAlchemy valida la conexión.
4. Si se desean conservar datos de desarrollo, exportar desde SQLite con `pandas` o `mysqldump` y reinsertar. Para datos de demo es más simple volver a ejecutar el análisis.

## 10. Seguridad y respaldos

- Las credenciales viven en `.env` y nunca se versionan.
- `.env.example` solo contiene marcadores de posición.
- Para MySQL, usar un usuario con permisos mínimos sobre `analisis_compras`.
- Respaldo sugerido: `mysqldump analisis_compras > backup.sql`.

## 11. Scripts y verificación

```bash
# Historial persistido
.venv/Scripts/python.exe scripts/history.py --limite 20

# Datos de ejemplo (opcional: --limpiar)
.venv/Scripts/python.exe scripts/seed.py --limpiar

# Vaciar la tabla (pide confirmación; --yes para automatizar)
.venv/Scripts/python.exe scripts/clear.py --yes
```

El agente guarda por defecto al ejecutar `scripts/run_agent.py`; usa `--sin-db` para omitir la persistencia. La suite tiene 143 pruebas y 90.6% de cobertura, incluidas las de repositorio, filtros, estadísticas, sesión, nodo de persistencia, grafo con SQLite temporal, endpoints de la API, sesiones y voz del bot.

## 12. Sesiones del bot de Telegram

El bot necesita recordar el estado de una conversación (producto, tiendas, presupuesto, perfil, modo y preferencia de voz). Ese estado **no** pertenece a `resultados` y se guarda en una base SQLite separada:

| Elemento | Valor |
|---|---|
| Archivo | `backend/data/bot_sessions.db` |
| Motor | SQLite con `aiosqlite` |
| Unidad | Una fila por `user_id`/`chat_id` |
| Expiración | `BOT_SESSION_TTL_HOURS` (24 h por defecto) |

Campos previstos:

| Campo | Tipo | Descripción |
|---|---|---|
| `user_id` | `INTEGER PRIMARY KEY` | ID numérico de Telegram (allowlist). |
| `chat_id` | `INTEGER` | Chat activo. |
| `estado` | `TEXT` | `idle`, `recolectando`, `confirmando`, `ejecutando`, `resultados`. |
| `slots` | `TEXT` (JSON) | Producto, tiendas, presupuesto, perfil y límite. |
| `modo` | `TEXT` | `fast` o `detallado`. |
| `voz` | `TEXT` | `auto`, `siempre` o `nunca`. |
| `ultimo_resultado` | `TEXT` (JSON, opcional) | Último resultado para seguimiento. |
| `actualizado_en` | `DATETIME` | Última actividad; base para expirar. |

Notas:

- `resultados` sigue siendo la única tabla de negocio persistente; el bot la usa con `ResultadoRepository`.
- Las sesiones son efímeras y se pueden borrar sin perder el historial de compras.
- No se guardan audios ni transcripciones; solo el texto que el usuario decide analizar.
- El detalle del flujo y la configuración está en [`10_bot_telegram.md`](10_bot_telegram.md).
