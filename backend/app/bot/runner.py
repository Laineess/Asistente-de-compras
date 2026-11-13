from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from app.graph.builder import run_analysis


class AnalysisRunner:
    def __init__(self, analysis_fn: Callable[..., Any] = run_analysis) -> None:
        self._analysis_fn = analysis_fn

    async def run(self, **kwargs: Any) -> dict[str, Any]:
        return await asyncio.to_thread(self._analysis_fn, **kwargs)
