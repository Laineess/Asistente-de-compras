from app.bot.runner import AnalysisRunner


async def test_runner_calls_analysis_in_thread() -> None:
    calls = []

    def fake_analysis(**kwargs):
        calls.append(kwargs)
        return {"resultado": "ok"}

    runner = AnalysisRunner(fake_analysis)
    result = await runner.run(consulta="laptop", use_llm=False)

    assert result == {"resultado": "ok"}
    assert calls == [{"consulta": "laptop", "use_llm": False}]
