from __future__ import annotations

import html
from dataclasses import dataclass, field
from decimal import Decimal
from urllib.parse import urlparse

from app.agents.review_agent import heuristic_review
from app.bot.conversation import Session
from app.models import AnalysisResult, ProductOption, ReviewSummary
from app.providers.service import normalize_key

MAX_MESSAGE = 3900


@dataclass(slots=True)
class ProductGroup:
    key: str
    nombre: str
    opciones: list[ProductOption]

    @property
    def precio_minimo(self) -> Decimal:
        return min(option.precio for option in self.opciones)

    def mejor_opcion(self, recomendado: str | None) -> ProductOption:
        if recomendado:
            key = normalize_key(recomendado)
            for option in self.opciones:
                if normalize_key(option.nombre) == key:
                    return option
        return min(self.opciones, key=lambda option: option.precio)


@dataclass(slots=True)
class BotReply:
    messages: list[str]
    audio_scripts: list[str] = field(default_factory=list)
    groups: list[ProductGroup] = field(default_factory=list)


def group_options(options: list[ProductOption]) -> list[ProductGroup]:
    groups: dict[str, ProductGroup] = {}
    for option in options:
        key = normalize_key(option.nombre)
        if key not in groups:
            groups[key] = ProductGroup(key=key, nombre=option.nombre, opciones=[])
        groups[key].opciones.append(option)
    return sorted(groups.values(), key=lambda group: group.precio_minimo)


def top_groups(result: AnalysisResult, limit: int = 3) -> list[ProductGroup]:
    groups = group_options(result.opciones)
    if not groups:
        return []
    recommended = (
        result.resumen_precios.opcion_recomendada
        if result.resumen_precios is not None
        else None
    )
    recommended_key = normalize_key(recommended) if recommended else None
    selected: list[ProductGroup] = []
    for group in groups:
        if group.key == recommended_key:
            selected.append(group)
            break
    for group in groups:
        if len(selected) >= limit:
            break
        if group not in selected:
            selected.append(group)
    return selected[:limit]


def _money(value: Decimal | None) -> str:
    if value is None:
        return "Sin límite"
    return f"${value:,.2f} MXN"


def _safe_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return url


def _review(group: ProductGroup) -> ReviewSummary:
    return heuristic_review(group.opciones)


def _option_line(option: ProductOption) -> str:
    store = html.escape(option.comercio.display_name)
    name = html.escape(option.nombre)
    price = html.escape(_money(option.precio))
    url = _safe_url(option.url)
    if url is None:
        return f"• {store} — {name} — {price}"
    return f'• {store} — {name} — {price} — <a href="{html.escape(url, quote=True)}">Abrir</a>'


def _group_block(
    position: int,
    group: ProductGroup,
    recommended: str | None,
    review: ReviewSummary | None,
) -> str:
    option = group.mejor_opcion(recommended)
    is_recommended = bool(
        recommended and normalize_key(recommended) == normalize_key(option.nombre)
    )
    title = f"{position}. {html.escape(option.nombre)}"
    if is_recommended:
        title += " (Recomendado)"
    lines = [f"<b>{title}</b>"]
    lines.append(
        f"Tienda: {html.escape(option.comercio.display_name)} — "
        f"{html.escape(_money(option.precio))}"
    )
    others = [
        item
        for item in group.opciones
        if item is not option and item.comercio != option.comercio
    ]
    if others:
        extra = "; ".join(
            f"{html.escape(item.comercio.display_name)} {html.escape(_money(item.precio))}"
            for item in sorted(others, key=lambda item: item.precio)[:3]
        )
        lines.append(f"También en: {extra}")
    url = _safe_url(option.url)
    if url is not None:
        lines.append(
            f'<a href="{html.escape(url, quote=True)}">Ver producto</a>'
        )
    if review is not None:
        lines.append(f"Score: {review.score}/10")
        lines.append(f"Reseña: {html.escape(review.sintesis)}")
        if review.pros:
            lines.append(f"Pros: {html.escape('; '.join(review.pros[:2]))}")
        if review.contras:
            lines.append(f"Contras: {html.escape('; '.join(review.contras[:2]))}")
    return "\n".join(lines)


def split_message(text: str, limit: int = MAX_MESSAGE) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for line in text.splitlines():
        if len(line) > limit:
            line = line[: limit - 1] + "…"
        extra = len(line) + (1 if current else 0)
        if current and size + extra > limit:
            chunks.append("\n".join(current))
            current = [line]
            size = len(line)
        else:
            current.append(line)
            size += extra
    if current:
        chunks.append("\n".join(current))
    return chunks or [text[:limit]]


def format_welcome() -> str:
    return (
        "<b>Asistente de compras</b>\n"
        "Comparo precios y reseñas en Walmart, Costco y Sam's.\n\n"
        "Escríbeme qué buscas o envíame una nota de voz. Ejemplo:\n"
        "<i>laptop para estudiante, máximo 15000, en Walmart y Costco</i>\n\n"
        "Comandos: /nuevo /cancelar /modo /voz /estado /ayuda"
    )


def format_help() -> str:
    return (
        "<b>Comandos</b>\n"
        "/nuevo — empezar otra consulta\n"
        "/cancelar — cancelar la actual\n"
        "/modo — fast (sin Gemini) o detallado (con Gemini)\n"
        "/voz — audio: auto, siempre o nunca\n"
        "/estado — ver los datos actuales\n"
        "/ayuda — esta lista\n\n"
        "Puedes incluir producto, tiendas, presupuesto y perfil en un solo mensaje."
    )


def format_status(session: Session) -> str:
    stores = ", ".join(store.display_name for store in session.tiendas)
    budget = _money(session.presupuesto) if session.presupuesto is not None else "Sin límite"
    return (
        "<b>Estado</b>\n"
        f"Producto: {html.escape(session.producto or '—')}\n"
        f"Tiendas: {html.escape(stores)}\n"
        f"Presupuesto: {html.escape(budget)}\n"
        f"Perfil: {html.escape(session.perfil or 'No especificado')}\n"
        f"Límite: {session.limite} por tienda\n"
        f"Modo: {html.escape(session.modo)}\n"
        f"Voz: {html.escape(session.voz)}"
    )


def format_results(result: AnalysisResult, session: Session) -> BotReply:
    if not result.opciones:
        messages = [
            "<b>Sin resultados</b>\n"
            "No encontré productos para esta consulta. Prueba con otro nombre "
            "o cambia las tiendas."
        ]
        if result.errores:
            messages[0] += "\n\nErrores: " + html.escape("; ".join(result.errores))
        return BotReply(messages=messages)

    groups = top_groups(result)
    recommended = (
        result.resumen_precios.opcion_recomendada
        if result.resumen_precios is not None
        else None
    )
    header = [f"<b>Resultado para {html.escape(result.producto)}</b>"]
    if result.recomendacion:
        header.append(html.escape(result.recomendacion))
    if result.resumen_precios is not None:
        price = result.resumen_precios
        header.append(
            "Precios: "
            f"mín {html.escape(_money(price.precio_minimo))}, "
            f"máx {html.escape(_money(price.precio_maximo))}, "
            f"prom {html.escape(_money(price.precio_promedio))}."
        )
        if price.presupuesto is not None:
            header.append(
                f"Presupuesto: {html.escape(_money(price.presupuesto))} "
                f"({price.opciones_dentro_presupuesto or 0} opciones dentro)."
            )

    blocks = ["\n".join(header), "<b>Top 3</b>"]
    audio_scripts: list[str] = []
    for position, group in enumerate(groups, start=1):
        review = _review(group)
        blocks.append(_group_block(position, group, recommended, review))
        option = group.mejor_opcion(recommended)
        audio_scripts.append(
            f"{option.nombre}. Precio {_money(option.precio)} en "
            f"{option.comercio.display_name}. Score {review.score} de 10. "
            f"{review.sintesis}"
        )

    links = ["<b>Enlaces encontrados</b>"]
    for group in group_options(result.opciones):
        for option in sorted(group.opciones, key=lambda item: item.precio):
            links.append(_option_line(option))
    blocks.append("\n".join(links))

    if result.advertencias:
        blocks.append(
            "<b>Avisos</b>\n" + html.escape("; ".join(result.advertencias))
        )

    messages = split_message("\n\n".join(blocks))
    return BotReply(messages=messages, audio_scripts=audio_scripts, groups=groups)
