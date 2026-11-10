# Scripts

Utilidades de desarrollo y entrega.

| Script | Propósito | Fase |
|---|---|---|
| `generate_mock_data.py` | Regenerar el catálogo mock de las tres tiendas | 3 |
| `search_demo.py` | Probar providers sin LLM | 3 |
| `run_agent.py` | Ejecutar el grafo por CLI (`--sin-llm`, `--json`, `--sin-db`) | 4 |
| `seed.py` | Insertar datos de ejemplo en `resultados` | 5 |
| `clear.py` | Vaciar `resultados` (pide confirmación) | 5 |
| `history.py` | Mostrar el historial persistido | 5 |
| `export_pdf.py` | Generar el PDF de investigación | 9 |

## run_agent.py

```bash
.venv/Scripts/python.exe scripts/run_agent.py "laptop" --limite 3
.venv/Scripts/python.exe scripts/run_agent.py "laptop" --limite 3 --sin-llm
.venv/Scripts/python.exe scripts/run_agent.py "laptop" --limite 3 --json
.venv/Scripts/python.exe scripts/run_agent.py "laptop" --limite 3 --sin-db
```

## Base de datos

```bash
.venv/Scripts/python.exe scripts/history.py --limite 20
.venv/Scripts/python.exe scripts/seed.py --limpiar
.venv/Scripts/python.exe scripts/clear.py --yes
```
