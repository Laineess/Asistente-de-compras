from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from app.bot.parser import ParsedRequest, parse_request
from app.models import Store

IDLE = "idle"
COLLECTING = "recolectando"
CONFIRMING = "confirmando"
RUNNING = "ejecutando"
RESULTS = "resultados"
CANCELLED = "cancelado"

MODES = {"fast", "detallado"}
VOICE_MODES = {"auto", "siempre", "nunca"}


@dataclass(slots=True)
class Session:
    user_id: int
    chat_id: int
    estado: str = IDLE
    producto: str | None = None
    tiendas: list[Store] = field(default_factory=lambda: list(Store))
    presupuesto: Decimal | None = None
    perfil: str | None = None
    limite: int = 3
    modo: str = "fast"
    voz: str = "auto"
    entrada_voz: bool = False
    actualizado_en: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def slots(self) -> dict[str, Any]:
        return {
            "producto": self.producto,
            "tiendas": [store.value for store in self.tiendas],
            "presupuesto": str(self.presupuesto) if self.presupuesto is not None else None,
            "perfil": self.perfil,
            "limite": self.limite,
            "entrada_voz": self.entrada_voz,
        }

    def to_row(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "estado": self.estado,
            "slots": json.dumps(self.slots(), ensure_ascii=False),
            "modo": self.modo,
            "voz": self.voz,
            "actualizado_en": self.actualizado_en.isoformat(),
        }

    @classmethod
    def from_row(cls, row: Any) -> "Session":
        slots = json.loads(row["slots"] or "{}")
        stores: list[Store] = []
        for raw in slots.get("tiendas") or []:
            try:
                stores.append(Store(raw))
            except ValueError:
                continue
        if not stores:
            stores = list(Store)
        budget = slots.get("presupuesto")
        try:
            presupuesto = Decimal(str(budget)) if budget not in (None, "") else None
        except (InvalidOperation, ValueError):
            presupuesto = None
        updated = row["actualizado_en"]
        try:
            actualizado = datetime.fromisoformat(updated)
        except (TypeError, ValueError):
            actualizado = datetime.now(timezone.utc)
        return cls(
            user_id=int(row["user_id"]),
            chat_id=int(row["chat_id"]),
            estado=str(row["estado"]),
            producto=slots.get("producto"),
            tiendas=stores,
            presupuesto=presupuesto,
            perfil=slots.get("perfil"),
            limite=int(slots.get("limite") or 3),
            modo=str(row["modo"] or "fast"),
            voz=str(row["voz"] or "auto"),
            entrada_voz=bool(slots.get("entrada_voz", False)),
            actualizado_en=actualizado,
        )


class ConversationManager:
    def __init__(
        self,
        default_mode: str = "fast",
        default_voice: str = "auto",
        default_limit: int = 3,
    ) -> None:
        self.default_mode = default_mode if default_mode in MODES else "fast"
        self.default_voice = default_voice if default_voice in VOICE_MODES else "auto"
        self.default_limit = max(1, min(10, default_limit))

    def new_session(self, user_id: int, chat_id: int) -> Session:
        return Session(
            user_id=user_id,
            chat_id=chat_id,
            modo=self.default_mode,
            voz=self.default_voice,
            limite=self.default_limit,
        )

    def reset(self, session: Session) -> Session:
        return replace(
            session,
            estado=IDLE,
            producto=None,
            tiendas=list(Store),
            presupuesto=None,
            perfil=None,
            limite=self.default_limit,
            entrada_voz=False,
            actualizado_en=datetime.now(timezone.utc),
        )

    def cancel(self, session: Session) -> Session:
        return replace(
            session,
            estado=CANCELLED,
            producto=None,
            tiendas=list(Store),
            presupuesto=None,
            perfil=None,
            entrada_voz=False,
            actualizado_en=datetime.now(timezone.utc),
        )

    def apply_text(
        self,
        session: Session,
        text: str,
        *,
        from_voice: bool = False,
    ) -> tuple[Session, ParsedRequest]:
        parsed = parse_request(text)
        base = session
        if session.estado in {IDLE, RESULTS, CANCELLED}:
            base = self.reset(session)

        producto = parsed.producto or base.producto
        tiendas = parsed.tiendas if parsed.tiendas is not None else base.tiendas
        presupuesto = (
            parsed.presupuesto if parsed.presupuesto_mencionado else base.presupuesto
        )
        perfil = parsed.perfil if parsed.perfil_mencionado else base.perfil
        limite = parsed.limite if parsed.limite is not None else base.limite
        estado = CONFIRMING if producto else COLLECTING

        updated = replace(
            base,
            estado=estado,
            producto=producto,
            tiendas=tiendas,
            presupuesto=presupuesto,
            perfil=perfil,
            limite=limite,
            entrada_voz=from_voice,
            actualizado_en=datetime.now(timezone.utc),
        )
        return updated, parsed

    def set_input_voice(self, session: Session, from_voice: bool) -> Session:
        return replace(
            session,
            entrada_voz=from_voice,
            actualizado_en=datetime.now(timezone.utc),
        )

    def set_mode(self, session: Session, mode: str) -> Session:
        if mode not in MODES:
            raise ValueError(f"modo invalido: {mode}")
        return replace(
            session,
            modo=mode,
            actualizado_en=datetime.now(timezone.utc),
        )

    def set_voice(self, session: Session, voice: str) -> Session:
        if voice not in VOICE_MODES:
            raise ValueError(f"modo de voz invalido: {voice}")
        return replace(
            session,
            voz=voice,
            actualizado_en=datetime.now(timezone.utc),
        )

    def set_stores(self, session: Session, stores: list[Store]) -> Session:
        return replace(
            session,
            tiendas=stores or list(Store),
            estado=CONFIRMING if session.producto else session.estado,
            actualizado_en=datetime.now(timezone.utc),
        )

    def set_budget(self, session: Session, budget: Decimal | None) -> Session:
        return replace(
            session,
            presupuesto=budget,
            actualizado_en=datetime.now(timezone.utc),
        )

    def set_profile(self, session: Session, profile: str | None) -> Session:
        return replace(
            session,
            perfil=profile,
            actualizado_en=datetime.now(timezone.utc),
        )

    def set_running(self, session: Session) -> Session:
        return replace(
            session,
            estado=RUNNING,
            actualizado_en=datetime.now(timezone.utc),
        )

    def set_results(self, session: Session) -> Session:
        return replace(
            session,
            estado=RESULTS,
            actualizado_en=datetime.now(timezone.utc),
        )

    def needs_product(self, session: Session) -> bool:
        return not session.producto

    def ready(self, session: Session) -> bool:
        return bool(session.producto) and session.estado in {CONFIRMING, RESULTS}

    def question(self, session: Session) -> str | None:
        if not session.producto:
            return (
                "¿Qué producto quieres comparar? "
                "Puedes escribirlo o enviar una nota de voz. "
                "Ejemplo: laptop para estudiante, máximo 15000, en Walmart y Costco."
            )
        return None

    def summary(self, session: Session) -> str:
        stores = ", ".join(store.display_name for store in session.tiendas)
        budget = (
            f"${session.presupuesto:,.2f} MXN"
            if session.presupuesto is not None
            else "Sin límite"
        )
        profile = session.perfil or "No especificado"
        mode = "fast (sin Gemini)" if session.modo == "fast" else "detallado (con Gemini)"
        lines = [
            "Revisa la consulta:",
            f"• Producto: {session.producto}",
            f"• Tiendas: {stores or 'Todas'}",
            f"• Presupuesto: {budget}",
            f"• Perfil: {profile}",
            f"• Límite: {session.limite} por tienda",
            f"• Modo: {mode}",
        ]
        missing: list[str] = []
        if not session.perfil:
            missing.append("perfil")
        if session.presupuesto is None:
            missing.append("presupuesto")
        if missing:
            lines.append(
                "Si quieres ajustar tiendas, presupuesto o perfil, envíalo en un "
                "mensaje antes de analizar."
            )
        return "\n".join(lines)

    def analysis_kwargs(self, session: Session) -> dict[str, Any]:
        if not session.producto:
            raise ValueError("falta el producto")
        return {
            "consulta": session.producto,
            "limite_por_tienda": session.limite,
            "perfil": session.perfil,
            "tiendas": list(session.tiendas),
            "presupuesto": session.presupuesto,
            "use_llm": session.modo == "detallado",
            "persist": True,
        }
