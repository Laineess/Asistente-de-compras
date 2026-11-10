from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from app.graph import run_analysis  # noqa: E402
from app.models import Store  # noqa: E402


def format_money(value) -> str:
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Ejecuta el agente de compras.")
    parser.add_argument("consulta", help="Producto a buscar, por ejemplo: laptop")
    parser.add_argument(
        "--limite",
        type=int,
        default=3,
        help="Opciones por tienda (1-10)",
    )
    parser.add_argument(
        "--perfil",
        default=None,
        help="Perfil del usuario (estudiante, profesional, gamer, hogar)",
    )
    parser.add_argument(
        "--tiendas",
        default=None,
        help="Tiendas separadas por coma: walmart,costco,sams",
    )
    parser.add_argument(
        "--sin-llm",
        action="store_true",
        help="Ejecuta sin Gemini (usa resúmenes heurísticos)",
    )
    parser.add_argument(
        "--sin-db",
        action="store_true",
        help="No guarda el resultado en la base de datos",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime el resultado completo en JSON",
    )
    args = parser.parse_args()

    if not 1 <= args.limite <= 10:
        parser.error("--limite debe estar entre 1 y 10")

    tiendas = None
    if args.tiendas:
        try:
            tiendas = [
                Store(name.strip().lower())
                for name in args.tiendas.split(",")
                if name.strip()
            ]
        except ValueError as exc:
            parser.error(f"Tienda inválida: {exc}")

    if args.sin_llm:
        print("Modo sin LLM: se usan resúmenes heurísticos.", file=sys.stderr)

    state = run_analysis(
        consulta=args.consulta,
        limite_por_tienda=args.limite,
        perfil=args.perfil,
        tiendas=tiendas,
        use_llm=not args.sin_llm,
        persist=not args.sin_db,
    )
    result = state.get("resultado")

    if args.json:
        payload = {
            "pasos": state.get("pasos", []),
            "errores": state.get("errores", []),
            "advertencias": state.get("advertencias", []),
            "filas_guardadas": state.get("filas_guardadas", 0),
            "resultado": result.model_dump(mode="json") if result else None,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Pasos:", " -> ".join(state.get("pasos", [])))
    if state.get("errores"):
        print("Errores:", "; ".join(state["errores"]))
    if not result:
        print("No se generó un resultado.")
        return 1

    print(f"\nProducto: {result.producto}")
    print(f"Tiendas: {', '.join(store.display_name for store in result.tiendas)}")
    print("\nOpciones:")
    for option in result.opciones:
        print(
            f"- {option.nombre} | {option.comercio.display_name} | "
            f"{format_money(option.precio)} {option.moneda} | "
            f"calificación {option.calificacion or 'N/D'} | fuente {option.fuente}"
        )

    if result.resumen_precios:
        price = result.resumen_precios
        print("\nPrecios:")
        print(
            f"- Mínimo: {format_money(price.precio_minimo)} "
            f"({price.comercio_mas_barato}) | "
            f"Máximo: {format_money(price.precio_maximo)} "
            f"({price.comercio_mas_caro}) | "
            f"Promedio: {format_money(price.precio_promedio)}"
        )
        print(f"- Opción recomendada: {price.opcion_recomendada}")

    if result.resumen_resenas:
        reviews = result.resumen_resenas
        print("\nReseñas:")
        print(f"- Score: {reviews.score}/10 | Analizadas: {reviews.resenas_analizadas}")
        print(f"- Pros: {'; '.join(reviews.pros)}")
        print(f"- Contras: {'; '.join(reviews.contras)}")
        print(f"- Síntesis: {reviews.sintesis}")

    if result.usuarios_relevantes:
        print("\nPerfiles:")
        for profile in result.usuarios_relevantes.perfiles:
            print(f"- {profile.perfil}: {profile.descripcion}")

    print("\nRecomendación final:")
    print(result.recomendacion)

    if args.sin_db:
        print("\nPersistencia: omitida (--sin-db).")
    else:
        print(f"\nPersistencia: {result.filas_guardadas} filas guardadas en resultados.")

    if result.advertencias:
        print("\nAdvertencias:")
        for warning in result.advertencias:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(exit_code)
