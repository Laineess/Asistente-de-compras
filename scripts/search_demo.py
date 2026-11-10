from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.models import ProductQuery, Store
from app.providers.factory import build_default_service


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prueba la capa de providers sin LLM."
    )
    parser.add_argument("producto", help="Producto a buscar, por ejemplo: laptop")
    parser.add_argument(
        "--tiendas",
        nargs="+",
        choices=[store.value for store in Store],
        default=[store.value for store in Store],
        help="Tiendas a consultar (por defecto todas).",
    )
    parser.add_argument("--limite", type=int, default=3, help="Resultados por tienda.")
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    query = ProductQuery(
        producto=args.producto,
        tiendas=[Store(value) for value in args.tiendas],
        limite_por_tienda=args.limite,
    )
    result = build_default_service().search(query)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
