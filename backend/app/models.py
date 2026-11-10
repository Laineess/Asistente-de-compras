from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Store(str, Enum):
    walmart = "walmart"
    costco = "costco"
    sams = "sams"

    @property
    def display_name(self) -> str:
        return {
            "walmart": "Walmart",
            "costco": "Costco",
            "sams": "Sam's",
        }[self.value]


class ProductQuery(BaseModel):
    producto: str = Field(min_length=1, max_length=200)
    tiendas: list[Store] = Field(default_factory=lambda: list(Store))
    limite_por_tienda: int = Field(default=3, ge=1, le=10)


class ReviewSnippet(BaseModel):
    autor: str | None = None
    texto: str = Field(min_length=1)
    calificacion: float | None = Field(default=None, ge=0, le=5)


class ProductOption(BaseModel):
    nombre: str = Field(min_length=1)
    comercio: Store
    precio: Decimal = Field(ge=0)
    moneda: str = "MXN"
    url: str | None = None
    descripcion: str | None = None
    calificacion: float | None = Field(default=None, ge=0, le=5)
    resenas: list[ReviewSnippet] = Field(default_factory=list)
    fuente: Literal["tavily", "mock"] = "mock"

    @property
    def comercio_nombre(self) -> str:
        return self.comercio.display_name


class SearchResult(BaseModel):
    opciones: list[ProductOption] = Field(default_factory=list)
    errores: list[str] = Field(default_factory=list)
    tiendas_con_mock: list[Store] = Field(default_factory=list)


class PriceSummary(BaseModel):
    precio_final: Decimal = Field(ge=0)
    opcion_recomendada: str
    precio_promedio: Decimal = Field(ge=0)
    precio_minimo: Decimal = Field(ge=0)
    precio_maximo: Decimal = Field(ge=0)
    rango: Decimal = Field(ge=0)
    moneda: str = "MXN"
    opciones_consideradas: int = Field(ge=1)
    comercio_mas_barato: str
    comercio_mas_caro: str
    presupuesto: Decimal | None = Field(default=None, ge=0)
    opciones_dentro_presupuesto: int | None = Field(default=None, ge=0)


class ReviewSummary(BaseModel):
    score: float = Field(ge=0, le=10)
    resenas_analizadas: int = Field(ge=3)
    sintesis: str
    pros: list[str] = Field(default_factory=list)
    contras: list[str] = Field(default_factory=list)
    fuentes: list[str] = Field(default_factory=list)


class AudienceProfile(BaseModel):
    perfil: str
    descripcion: str
    evidencia: str | None = None
    porcentaje: float | None = Field(default=None, ge=0, le=100)


class AudienceSummary(BaseModel):
    perfiles: list[AudienceProfile] = Field(default_factory=list)
    sintesis: str | None = None


class AnalysisResult(BaseModel):
    producto: str
    tiendas: list[Store]
    opciones: list[ProductOption] = Field(default_factory=list)
    resumen_precios: PriceSummary | None = None
    resumen_resenas: ReviewSummary | None = None
    usuarios_relevantes: AudienceSummary | None = None
    presupuesto: Decimal | None = None
    recomendacion: str = ""
    advertencias: list[str] = Field(default_factory=list)
    filas_guardadas: int = 0
    errores: list[str] = Field(default_factory=list)
    fecha_consulta: datetime = Field(default_factory=datetime.now)
