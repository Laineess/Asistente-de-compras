from __future__ import annotations

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    import numpy as np
    from telegram import Message

logger = logging.getLogger(__name__)


class VoiceError(RuntimeError):
    pass


class VoiceService:
    def __init__(
        self,
        *,
        max_audio_seconds: int = 120,
        stt_model: str = "small",
        stt_device: str = "cpu",
        stt_compute_type: str = "int8",
        tts_voice: str = "es-MX-JorgeNeural",
        transcriber: Callable[[Path], str] | None = None,
        synthesizer: Callable[[str, Path], Any] | None = None,
    ) -> None:
        self.max_audio_seconds = max(1, max_audio_seconds)
        self.stt_model = stt_model
        self.stt_device = stt_device
        self.stt_compute_type = stt_compute_type
        self.tts_voice = tts_voice
        self._transcriber = transcriber
        self._synthesizer = synthesizer
        self._model = None

    @staticmethod
    def _media(message: Message) -> Any | None:
        return message.voice or message.audio

    @staticmethod
    def _suffix(media: Any) -> str:
        name = getattr(media, "file_name", None) or ""
        return Path(name).suffix or ".ogg"

    @staticmethod
    def _missing_voice_dependency() -> VoiceError:
        return VoiceError(
            "La voz no está instalada. Ejecuta "
            "pip install -r backend/requirements-voice.txt."
        )

    def _duration_error(self) -> VoiceError:
        return VoiceError(
            f"El audio dura más de {self.max_audio_seconds} segundos. "
            "Envía uno más corto."
        )

    def _decode_audio(self, path: Path) -> np.ndarray:
        try:
            import av
            import numpy as np
        except ImportError as exc:
            raise self._missing_voice_dependency() from exc

        resampler = av.audio.resampler.AudioResampler(
            format="s16",
            layout="mono",
            rate=16000,
        )
        chunks: list[Any] = []
        try:
            with av.open(str(path), mode="r") as container:
                for frame in container.decode(audio=0):
                    for out_frame in resampler.resample(frame):
                        chunks.append(out_frame.to_ndarray().reshape(-1))
                for out_frame in resampler.resample(None):
                    chunks.append(out_frame.to_ndarray().reshape(-1))
        except Exception as exc:
            logger.warning("PyAV no pudo decodificar %s: %s", path.name, exc)
            raise VoiceError("No pude leer el audio. Verifica el formato.") from exc

        if not chunks:
            raise VoiceError("El audio está vacío o no tiene sonido.")
        return np.concatenate(chunks).astype(np.float32) / 32768.0

    def _to_ogg(self, source: Path, target: Path) -> None:
        try:
            import av
        except ImportError as exc:
            raise self._missing_voice_dependency() from exc

        try:
            with av.open(str(source), mode="r") as input_container:
                with av.open(str(target), mode="w", format="ogg") as output_container:
                    stream = output_container.add_stream("libopus", rate=48000)
                    stream.layout = "mono"
                    stream.bit_rate = 48000
                    for frame in input_container.decode(audio=0):
                        for packet in stream.encode(frame):
                            output_container.mux(packet)
                    for packet in stream.encode(None):
                        output_container.mux(packet)
        except Exception as exc:
            logger.warning("PyAV no pudo convertir a OGG: %s", exc)
            raise VoiceError("No pude convertir el audio a OGG.") from exc

        if not target.exists() or target.stat().st_size == 0:
            raise VoiceError("No se generó el audio OGG.")

    def _transcribe_file(self, path: Path) -> str:
        if self._transcriber is not None:
            text = self._transcriber(path)
        else:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise self._missing_voice_dependency() from exc

            audio = self._decode_audio(path)
            duration = audio.shape[0] / 16000
            if duration > self.max_audio_seconds:
                raise self._duration_error()

            if self._model is None:
                self._model = WhisperModel(
                    self.stt_model,
                    device=self.stt_device,
                    compute_type=self.stt_compute_type,
                )
            segments, _ = self._model.transcribe(
                audio,
                language="es",
                vad_filter=True,
            )
            text = " ".join(segment.text.strip() for segment in segments)

        text = " ".join(text.split()).strip()
        if not text:
            raise VoiceError("No pude entender el audio. Intenta de nuevo o escribe.")
        return text

    async def transcribe_message(self, message: Message) -> str:
        media = self._media(message)
        if media is None:
            raise VoiceError("No encontré una nota de voz o archivo de audio.")
        duration = getattr(media, "duration", None)
        if duration is not None and duration > self.max_audio_seconds:
            raise self._duration_error()

        workdir = Path(tempfile.mkdtemp(prefix="compras-stt-"))
        try:
            source = workdir / f"entrada{self._suffix(media)}"
            telegram_file = await media.get_file()
            await telegram_file.download_to_drive(custom_path=str(source))
            return await asyncio.to_thread(self._transcribe_file, source)
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    async def synthesize_text(self, text: str) -> Path | None:
        text = " ".join(text.split()).strip()
        if not text:
            return None
        workdir = Path(tempfile.mkdtemp(prefix="compras-tts-"))
        mp3 = workdir / "respuesta.mp3"
        try:
            if self._synthesizer is not None:
                result = self._synthesizer(text, mp3)
                if hasattr(result, "__await__"):
                    await result
            else:
                try:
                    import edge_tts
                except ImportError as exc:
                    raise self._missing_voice_dependency() from exc
                await edge_tts.Communicate(text, self.tts_voice).save(str(mp3))
            if not mp3.exists() or mp3.stat().st_size == 0:
                raise VoiceError("No se generó el audio de respuesta.")

            ogg = workdir / "respuesta.ogg"
            try:
                await asyncio.to_thread(self._to_ogg, mp3, ogg)
            except Exception as exc:
                logger.warning("No se pudo convertir a OGG; se enviará MP3: %s", exc)
                return mp3
            return ogg
        except Exception:
            shutil.rmtree(workdir, ignore_errors=True)
            raise

    @staticmethod
    def cleanup(path: Path | None) -> None:
        if path is None:
            return
        shutil.rmtree(path.parent, ignore_errors=True)
