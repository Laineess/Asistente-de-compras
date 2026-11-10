from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.db import build_default_repository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Elimina los registros de resultados.")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="No pedir confirmación",
    )
    args = parser.parse_args()

    repo = build_default_repository()
    total = repo.count()
    if not args.yes:
        answer = input(f"¿Eliminar {total} registros de resultados? [s/N] ")
        if answer.strip().lower() not in {"s", "si", "sí", "y", "yes"}:
            print("Cancelado.")
            return 1

    deleted = repo.clear()
    print(f"Registros eliminados: {deleted}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
