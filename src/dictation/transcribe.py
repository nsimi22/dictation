"""Local speech-to-text using faster-whisper.

The model is loaded once and reused for every dictation. Loading can take a
few seconds (and the first run may download the model), so callers should
construct the Transcriber at startup.
"""

from __future__ import annotations

import numpy as np


def _resolve_device(device: str) -> str:
    if device != "auto":
        return device
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda"
    except Exception:
        pass
    return "cpu"


def _resolve_compute_type(compute_type: str, device: str) -> str:
    if compute_type != "auto":
        return compute_type
    # int8 is a good, widely-supported default on CPU; float16 on GPU.
    return "float16" if device == "cuda" else "int8"


class Transcriber:
    """Wraps a faster-whisper model and transcribes in-memory audio buffers."""

    def __init__(
        self,
        model: str = "base.en",
        device: str = "auto",
        compute_type: str = "auto",
        language: str | None = "en",
    ):
        self.model_name = model
        self.device = _resolve_device(device)
        self.compute_type = _resolve_compute_type(compute_type, self.device)
        self.language = language or None
        self._model = None

    def load(self) -> None:
        """Load (and on first use, download) the Whisper model."""
        if self._model is not None:
            return
        from faster_whisper import WhisperModel  # lazy import

        self._model = WhisperModel(
            self.model_name,
            device=self.device,
            compute_type=self.compute_type,
        )

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe a mono float32 numpy array (16 kHz) into text."""
        if audio is None or len(audio) == 0:
            return ""
        if self._model is None:
            self.load()

        segments, _info = self._model.transcribe(
            audio,
            language=self.language,
            vad_filter=True,  # skip non-speech regions for cleaner output
            beam_size=5,
        )
        return "".join(segment.text for segment in segments)
