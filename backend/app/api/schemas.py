from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models import AnalysisResult, Store


class AnalyzeRequest(BaseModel):
    producto: str = Field(min_length=1, max_length=200)
    tiendas: list[Store] = Field(default_factory=lambda: list(Store))
    limite_por_tienda: int = Field(default=3, ge=1, le=10)
    perfil: str | None = None
    presupuesto: Decimal | None = Field(default=None, ge=0)
    usar_llm: bool = True
    guardar: bool = True


class AnalyzeResponse(BaseModel):
    resultado: AnalysisResult
    pasos: list[str] = Field(default_factory=list)
    errores: list[str] = Field(default_factory=list)
    advertencias: list[str] = Field(default_factory=list)
    filas_guardadas: int = 0


class ResultadoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre_producto: str
    comercio: str
    precio: Decimal
    fecha_consulta: datetime


class ComercioStats(BaseModel):
    comercio: str
    total: int
    precio_promedio: Decimal | None = None


class StatsOut(BaseModel):
    producto: str | None = None
    total: int
    precio_minimo: Decimal | None = None
    precio_maximo: Decimal | None = None
    precio_promedio: Decimal | None = None
    por_comercio: list[ComercioStats] = Field(default_factory=list)
