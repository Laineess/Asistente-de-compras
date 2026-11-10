from __future__ import annotations

import json
from collections.abc import Generator
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse

from app.agents.state import initial_state
from app.api.schemas import AnalyzeRequest, AnalyzeResponse, ResultadoOut, StatsOut
from app.db.repository import ResultadoRepository, build_default_repository
from app.graph import build_graph, run_analysis

router = APIRouter(prefix="/api", tags=["compras"])


@lru_cache(maxsize=1)
def get_repository() -> ResultadoRepository:
    return build_default_repository()


def _sse(payload: dict) -> str:
    data = json.dumps(jsonable_encoder(payload), ensure_ascii=False)
    return f"data: {data}\n\n"


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    state = run_analysis(
        consulta=request.producto,
        limite_por_tienda=request.limite_por_tienda,
        perfil=request.perfil,
        tiendas=request.tiendas,
        presupuesto=request.presupuesto,
        use_llm=request.usar_llm,
        persist=request.guardar,
    )
    result = state.get("resultado")
    if result is None:
        raise HTTPException(
            status_code=502,
            detail={
                "mensaje": "No se pudo completar el análisis.",
                "errores": state.get("errores", []),
            },
        )
    return AnalyzeResponse(
        resultado=result,
        pasos=state.get("pasos", []),
        errores=state.get("errores", []),
        advertencias=state.get("advertencias", []),
        filas_guardadas=state.get("filas_guardadas", 0),
    )


@router.post("/analyze/stream")
def analyze_stream(request: AnalyzeRequest) -> StreamingResponse:
    try:
        graph = build_graph(use_llm=request.usar_llm, persist=request.guardar)
        state = initial_state(
            consulta=request.producto,
            limite_por_tienda=request.limite_por_tienda,
            perfil=request.perfil,
            tiendas=request.tiendas,
            presupuesto=request.presupuesto,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    def event_generator() -> Generator[str, None, None]:
        current = dict(state)
        try:
            for event in graph.stream(state, stream_mode="updates"):
                for update in event.values():
                    current.update(update)
                yield _sse(
                    {
                        "event": "update",
                        "nodos": list(event.keys()),
                        "data": event,
                    }
                )
        except Exception as exc:
            yield _sse({"event": "error", "mensaje": str(exc)})
            return

        yield _sse(
            {
                "event": "done",
                "resultado": current.get("resultado"),
                "pasos": current.get("pasos", []),
                "errores": current.get("errores", []),
                "advertencias": current.get("advertencias", []),
                "filas_guardadas": current.get("filas_guardadas", 0),
            }
        )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/history", response_model=list[ResultadoOut])
def history(
    limit: int = Query(50, ge=1, le=200),
    producto: str | None = Query(None, min_length=1, max_length=200),
    repository: ResultadoRepository = Depends(get_repository),
) -> list[ResultadoOut]:
    rows = repository.list_resultados(limit=limit, producto=producto)
    return [ResultadoOut.model_validate(row) for row in rows]


@router.get("/stats", response_model=StatsOut)
def stats(
    producto: str | None = Query(None, min_length=1, max_length=200),
    repository: ResultadoRepository = Depends(get_repository),
) -> StatsOut:
    data = repository.stats(producto=producto)
    return StatsOut(producto=producto, **data)
