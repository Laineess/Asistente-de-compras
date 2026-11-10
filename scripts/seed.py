from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.db import ResultadoRepository, SessionLocal, init_db  # noqa: E402
from app.db.models import Resultado  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Inserta datos de ejemplo en resultados.")
    parser.add_argument(
        "--limpiar",
        action="store_true",
        help="Elimina los registros existentes antes de insertar",
    )
    args = parser.parse_args()

    init_db()
    repo = ResultadoRepository(SessionLocal)
    if args.limpiar:
        print(f"Registros eliminados: {repo.clear()}")

    now = datetime.now()
    rows = [
        Resultado(
            nombre_producto="Laptop de demostración",
            comercio="Walmart",
            precio=Decimal("12999.00"),
            fecha_consulta=now - timedelta(minutes=3),
        ),
        Resultado(
            nombre_producto="Laptop de demostración",
            comercio="Costco",
            precio=Decimal("13499.00"),
            fecha_consulta=now - timedelta(minutes=2),
        ),
        Resultado(
            nombre_producto="Laptop de demostración",
            comercio="Sam's",
            precio=Decimal("12799.00"),
            fecha_consulta=now - timedelta(minutes=1),
        ),
        Resultado(
            nombre_producto="Audífonos de demostración",
            comercio="Walmart",
            precio=Decimal("899.00"),
            fecha_consulta=now,
        ),
    ]
    with SessionLocal() as session:
        session.add_all(rows)
        session.commit()

    print(f"Insertadas {len(rows)} filas de ejemplo. Total: {repo.count()}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
