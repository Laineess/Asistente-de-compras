from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db.models import Resultado
from app.db.session import SessionLocal, init_db
from app.models import AnalysisResult

SessionFactory = Callable[[], Session]


class ResultadoRepository:
    def __init__(self, session_factory: SessionFactory = SessionLocal) -> None:
        self._session_factory = session_factory

    def save_result(self, result: AnalysisResult) -> int:
        rows = [
            Resultado(
                nombre_producto=option.nombre,
                comercio=option.comercio.display_name,
                precio=option.precio,
                fecha_consulta=result.fecha_consulta,
            )
            for option in result.opciones
        ]
        if not rows:
            return 0
        with self._session_factory() as session:
            session.add_all(rows)
            session.commit()
        return len(rows)

    def list_resultados(
        self,
        limit: int = 50,
        producto: str | None = None,
    ) -> list[Resultado]:
        with self._session_factory() as session:
            stmt = select(Resultado)
            if producto:
                stmt = stmt.where(Resultado.nombre_producto.ilike(f"%{producto}%"))
            stmt = (
                stmt.order_by(Resultado.fecha_consulta.desc(), Resultado.id.desc())
                .limit(limit)
            )
            return list(session.scalars(stmt))

    def stats(self, producto: str | None = None) -> dict:
        filtro = (
            Resultado.nombre_producto.ilike(f"%{producto}%") if producto else None
        )
        with self._session_factory() as session:
            base = select(
                func.count(Resultado.id),
                func.min(Resultado.precio),
                func.max(Resultado.precio),
                func.avg(Resultado.precio),
            )
            if filtro is not None:
                base = base.where(filtro)
            total, minimo, maximo, promedio = session.execute(base).one()

            group = select(
                Resultado.comercio,
                func.count(Resultado.id),
                func.avg(Resultado.precio),
            )
            if filtro is not None:
                group = group.where(filtro)
            group = group.group_by(Resultado.comercio).order_by(Resultado.comercio)
            rows = session.execute(group).all()

            return {
                "total": int(total or 0),
                "precio_minimo": minimo,
                "precio_maximo": maximo,
                "precio_promedio": promedio,
                "por_comercio": [
                    {
                        "comercio": comercio,
                        "total": int(count),
                        "precio_promedio": avg,
                    }
                    for comercio, count, avg in rows
                ],
            }

    def count(self) -> int:
        with self._session_factory() as session:
            total = session.scalar(select(func.count()).select_from(Resultado))
            return int(total or 0)

    def clear(self) -> int:
        with self._session_factory() as session:
            result = session.execute(delete(Resultado))
            session.commit()
            return int(result.rowcount or 0)


def build_default_repository() -> ResultadoRepository:
    init_db()
    return ResultadoRepository()
