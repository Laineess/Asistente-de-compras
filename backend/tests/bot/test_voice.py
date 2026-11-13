import sys
import types
import wave
from pathlib import Path

import pytest

from app.bot.voice import VoiceError, VoiceService


class FakeFile:
    def __init__(self, payload: bytes = b"telegram-audio") -> None:
        self.payload = payload

    async def download_to_drive(self, custom_path: str) -> None:
        Path(custom_path).write_bytes(self.payload)


class FakeMedia:
    def __init__(
        self,
        duration: int | None = 3,
        file_name: str | None = None,
        payload: bytes = b"telegram-audio",
    ) -> None:
        self.duration = duration
        self.file_name = file_name
        self.payload = payload

    async def get_file(self) -> FakeFile:
        return FakeFile(self.payload)


class FakeMessage:
    def __init__(self, voice=None, audio=None) -> None:
        self.voice = voice
        self.audio = audio


def write_wav(path: Path, seconds: float = 0.2, rate: int = 16000) -> None:
    np = pytest.importorskip("numpy")
    samples = (
        np.sin(2 * np.pi * 440 * np.arange(int(rate * seconds)) / rate)
        * 0.2
        * 32767
    ).astype(np.int16)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(samples.tobytes())


def install_fake_whisper(monkeypatch, segments, seen=None):
    class FakeModel:
        def __init__(self, *args, **kwargs) -> None:
            if seen is not None:
                seen["model"] = args[0]
                seen["init"] = kwargs

        def transcribe(self, audio, **kwargs):
            if seen is not None:
                seen["audio"] = audio
                seen["transcribe"] = kwargs
            return segments, None

    module = types.ModuleType("faster_whisper")
    module.WhisperModel = FakeModel
    monkeypatch.setitem(sys.modules, "faster_whisper", module)


async def test_transcribe_downloads_and_cleans_without_conversion() -> None:
    seen: list[Path] = []

    def fake_transcriber(path: Path) -> str:
        seen.append(path)
        assert path.suffix == ".oga"
        assert path.read_bytes() == b"telegram-audio"
        return "  laptop para estudiante  "

    service = VoiceService(transcriber=fake_transcriber)
    text = await service.transcribe_message(
        FakeMessage(voice=FakeMedia(duration=4, file_name="nota.oga"))
    )

    assert text == "laptop para estudiante"
    assert seen
    assert not seen[0].parent.exists()


async def test_transcribe_accepts_audio_files() -> None:
    def fake_transcriber(path: Path) -> str:
        assert path.suffix == ".mp3"
        return "consulta de audio"

    service = VoiceService(transcriber=fake_transcriber)
    text = await service.transcribe_message(
        FakeMessage(audio=FakeMedia(duration=2, file_name="consulta.mp3"))
    )

    assert text == "consulta de audio"


async def test_transcribe_rejects_long_audio() -> None:
    service = VoiceService(max_audio_seconds=2)

    with pytest.raises(VoiceError, match="más de 2"):
        await service.transcribe_message(FakeMessage(voice=FakeMedia(duration=3)))


def test_transcribe_rejects_long_decoded_audio(monkeypatch) -> None:
    np = pytest.importorskip("numpy")
    install_fake_whisper(monkeypatch, [])
    service = VoiceService(max_audio_seconds=2)
    monkeypatch.setattr(
        service,
        "_decode_audio",
        lambda _path: np.zeros(3 * 16000, dtype=np.float32),
    )

    with pytest.raises(VoiceError, match="más de 2"):
        service._transcribe_file(Path("audio.ogg"))


async def test_transcribe_rejects_empty_result() -> None:
    service = VoiceService(transcriber=lambda _path: "   ")

    with pytest.raises(VoiceError, match="No pude entender"):
        await service.transcribe_message(FakeMessage(voice=FakeMedia()))


async def test_transcribe_requires_media() -> None:
    service = VoiceService()

    with pytest.raises(VoiceError, match="No encontré"):
        await service.transcribe_message(FakeMessage())


def test_transcribe_uses_numpy_array(monkeypatch) -> None:
    np = pytest.importorskip("numpy")
    seen = {}
    segments = [
        types.SimpleNamespace(text=" laptop "),
        types.SimpleNamespace(text="gamer "),
    ]
    install_fake_whisper(monkeypatch, segments, seen)
    service = VoiceService(
        stt_model="tiny",
        stt_device="cpu",
        stt_compute_type="int8",
    )
    audio = np.zeros(16000, dtype=np.float32)
    monkeypatch.setattr(service, "_decode_audio", lambda _path: audio)

    assert service._transcribe_file(Path("audio.ogg")) == "laptop gamer"
    assert seen["audio"] is audio
    assert isinstance(seen["audio"], np.ndarray)
    assert seen["transcribe"]["language"] == "es"
    assert seen["transcribe"]["vad_filter"] is True
    assert seen["model"] == "tiny"
    assert service._model is not None


def test_transcribe_reuses_cached_model(monkeypatch) -> None:
    np = pytest.importorskip("numpy")
    install_fake_whisper(monkeypatch, [])
    segments = [types.SimpleNamespace(text=" laptop ")]
    model = types.SimpleNamespace(
        transcribe=lambda audio, **kwargs: (segments, None)
    )
    service = VoiceService()
    service._model = model
    monkeypatch.setattr(
        service,
        "_decode_audio",
        lambda _path: np.zeros(16000, dtype=np.float32),
    )

    assert service._transcribe_file(Path("audio.ogg")) == "laptop"
    assert service._model is model


def test_transcribe_without_faster_whisper(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "faster_whisper", None)
    service = VoiceService()

    with pytest.raises(VoiceError, match="no está instalada"):
        service._transcribe_file(Path("audio.ogg"))


def test_decode_audio_roundtrip_with_pyav(tmp_path) -> None:
    np = pytest.importorskip("numpy")
    pytest.importorskip("av")
    service = VoiceService()
    source = tmp_path / "audio.wav"
    target = tmp_path / "audio.ogg"
    write_wav(source)

    service._to_ogg(source, target)
    audio = service._decode_audio(target)

    assert target.read_bytes()[:4] == b"OggS"
    assert audio.ndim == 1
    assert audio.dtype == np.float32
    assert audio.size > 0
    assert float(np.abs(audio).max()) <= 1.0


def test_decode_audio_rejects_invalid_file(tmp_path) -> None:
    pytest.importorskip("av")
    source = tmp_path / "audio.ogg"
    source.write_bytes(b"not audio")

    with pytest.raises(VoiceError, match="No pude leer"):
        VoiceService()._decode_audio(source)


def test_decode_audio_rejects_empty_audio(tmp_path) -> None:
    pytest.importorskip("av")
    source = tmp_path / "vacio.wav"
    with wave.open(str(source), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"")

    with pytest.raises(VoiceError, match="vacío"):
        VoiceService()._decode_audio(source)


def test_decode_audio_without_pyav(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "av", None)

    with pytest.raises(VoiceError, match="no está instalada"):
        VoiceService()._decode_audio(Path("audio.ogg"))


def test_to_ogg_rejects_invalid_source(tmp_path) -> None:
    pytest.importorskip("av")
    source = tmp_path / "audio.mp3"
    source.write_bytes(b"not audio")

    with pytest.raises(VoiceError, match="convertir"):
        VoiceService()._to_ogg(source, tmp_path / "audio.ogg")


def test_to_ogg_without_pyav(monkeypatch, tmp_path) -> None:
    monkeypatch.setitem(sys.modules, "av", None)

    with pytest.raises(VoiceError, match="no está instalada"):
        VoiceService()._to_ogg(tmp_path / "audio.mp3", tmp_path / "audio.ogg")


async def test_synthesize_converts_to_ogg(monkeypatch) -> None:
    def fake_synth(text: str, target: Path) -> None:
        assert text == "hola"
        target.write_bytes(b"mp3")

    service = VoiceService(synthesizer=fake_synth)
    monkeypatch.setattr(
        service,
        "_to_ogg",
        lambda source, target: target.write_bytes(b"ogg"),
    )

    path = await service.synthesize_text("  hola  ")

    assert path is not None
    assert path.suffix == ".ogg"
    assert path.read_bytes() == b"ogg"
    service.cleanup(path)
    assert not path.parent.exists()


async def test_synthesize_falls_back_to_mp3(monkeypatch) -> None:
    def fake_synth(_text: str, target: Path) -> None:
        target.write_bytes(b"mp3")

    service = VoiceService(synthesizer=fake_synth)

    def fail(*_args, **_kwargs):
        raise VoiceError("sin ogg")

    monkeypatch.setattr(service, "_to_ogg", fail)
    path = await service.synthesize_text("hola")

    assert path is not None and path.suffix == ".mp3"
    service.cleanup(path)


async def test_synthesize_empty_text_returns_none() -> None:
    service = VoiceService()

    assert await service.synthesize_text("   ") is None


async def test_synthesize_with_edge_tts(monkeypatch) -> None:
    class FakeCommunicate:
        def __init__(self, text: str, voice: str) -> None:
            assert text == "hola"
            assert voice == "es-MX-JorgeNeural"

        async def save(self, path: str) -> None:
            Path(path).write_bytes(b"mp3")

    module = types.ModuleType("edge_tts")
    module.Communicate = FakeCommunicate
    monkeypatch.setitem(sys.modules, "edge_tts", module)
    service = VoiceService()
    monkeypatch.setattr(
        service,
        "_to_ogg",
        lambda source, target: target.write_bytes(b"ogg"),
    )

    path = await service.synthesize_text("hola")

    assert path is not None and path.suffix == ".ogg"
    service.cleanup(path)


async def test_synthesize_without_edge_tts(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "edge_tts", None)
    service = VoiceService()

    with pytest.raises(VoiceError, match="no está instalada"):
        await service.synthesize_text("hola")


async def test_synthesize_fails_when_no_audio_created() -> None:
    service = VoiceService(synthesizer=lambda _text, _path: None)

    with pytest.raises(VoiceError, match="No se generó"):
        await service.synthesize_text("hola")


async def test_synthesize_fails_when_audio_is_empty() -> None:
    service = VoiceService(
        synthesizer=lambda _text, target: target.write_bytes(b"")
    )

    with pytest.raises(VoiceError, match="No se generó"):
        await service.synthesize_text("hola")


async def test_synthesize_awaits_async_synthesizer(monkeypatch) -> None:
    async def fake_synth(_text: str, target: Path) -> None:
        target.write_bytes(b"mp3")

    service = VoiceService(synthesizer=fake_synth)
    monkeypatch.setattr(
        service,
        "_to_ogg",
        lambda source, target: target.write_bytes(b"ogg"),
    )
    path = await service.synthesize_text("hola")

    assert path is not None
    service.cleanup(path)


def test_cleanup_none_is_noop() -> None:
    VoiceService.cleanup(None)
