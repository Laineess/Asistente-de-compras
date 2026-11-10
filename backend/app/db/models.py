from __future__ import annotations

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

    def __repr__(self) -> str:
        return (
            f"Resultado(id={self.id!r}, nombre_producto={self.nombre_producto!r}, "
            f"comercio={self.comercio!r}, precio={self.precio!r})"
        )
