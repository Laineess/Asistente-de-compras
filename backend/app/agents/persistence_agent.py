from __future__ import annotations

from typing import Callable

from app.agents.state import AgentState
from app.db.repository import ResultadoRepository


def make_persistence_agent(
    repository: ResultadoRepository | None,
    enabled: bool = True,
) -> Callable[[AgentState], dict]:
    def persistence_agent(state: AgentState) -> dict:
        pasos = [*state.get("pasos", [])]
        result = state.get("resultado")
        if result is None:
            return {
                "filas_guardadas": 0,
                "pasos": [*pasos, "persistir:sin-resultado"],
            }
        if not enabled or repository is None:
            return {
                "filas_guardadas": 0,
                "pasos": [*pasos, "persistir:omitido"],
            }

        try:
            saved = repository.save_result(result)
        except Exception as exc:
            warnings = [
                *state.get("advertencias", []),
                f"No se pudo guardar en la base de datos: {exc}",
            ]
            errors = [*state.get("errores", []), f"persistencia: {exc}"]
            updated = result.model_copy(
                update={
                    "filas_guardadas": 0,
                    "advertencias": warnings,
                    "errores": errors,
                }
            )
            return {
                "resultado": updated,
                "filas_guardadas": 0,
                "advertencias": warnings,
                "errores": errors,
                "pasos": [*pasos, "persistir:error"],
            }

        warnings = list(state.get("advertencias", []))
        updated = result.model_copy(
            update={"filas_guardadas": saved, "advertencias": warnings}
        )
        return {
            "resultado": updated,
            "filas_guardadas": saved,
            "advertencias": warnings,
            "pasos": [*pasos, f"persistir:{saved} filas"],
        }

    return persistence_agent
