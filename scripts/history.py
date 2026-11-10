from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.db import build_default_repository  # noqa: E402


def format_money(value) -> str:
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Muestra el historial de resultados.")
    parser.add_argument("--limite", type=int, default=20, help="Filas a mostrar")
    args = parser.parse_args()

    if args.limite < 1:
        parser.error("--limite debe ser mayor que 0")

    repo = build_default_repository()
    rows = repo.list_resultados(limit=args.limite)
    print(f"Registros: {repo.count()} | mostrando {len(rows)}.")
    for row in rows:
        fecha = row.fecha_consulta.strftime("%Y-%m-%d %H:%M")
        print(
            f"{row.id:>4} | {fecha} | {row.comercio:<8} | "
            f"{row.nombre_producto[:55]:<55} | {format_money(row.precio)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
