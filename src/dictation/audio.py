"""Microphone capture.

Records mono float32 audio at the configured sample rate into an in-memory
buffer for the duration of a hold-to-talk press. faster-whisper consumes a
1-D float32 numpy array, which is exactly what `stop()` returns, so no
resampling or file I/O is needed.
"""

from __future__ import annotations

import threading

import numpy as np


class Recorder:
    """Start/stop microphone recording, accumulating samples in memory.

    Usage:
        rec = Recorder(sample_rate=16000)
        rec.start()
        ...                       # user speaks
        audio = rec.stop()        # -> float32 numpy array, mono

    `sounddevice` is imported lazily so that importing this module (e.g. in
    tests or on a machine without PortAudio) does not fail.
    """

    def __init__(self, sample_rate: int = 16000, input_device: int | str | None = None):
        self.sample_rate = sample_rate
        self.input_device = input_device
        self._frames: list[np.ndarray] = []
        self._stream = None
        self._lock = threading.Lock()
        self._recording = False

    @property
    def is_recording(self) -> bool:
        return self._recording

    def _callback(self, indata, frames, time_info, status):  # noqa: ANN001
        # Called from PortAudio's thread; copy because the buffer is reused.
        if status:
            # Overflows etc. are non-fatal; we just keep going.
            pass
        with self._lock:
            self._frames.append(indata.copy())

    def start(self) -> None:
        if self._recording:
            return
        import sounddevice as sd  # lazy import

        with self._lock:
            self._frames = []
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            device=self.input_device,
            callback=self._callback,
        )
        self._stream.start()
        self._recording = True

    def stop(self) -> np.ndarray:
        """Stop recording and return the captured mono audio as float32.

        Returns an empty array if nothing was captured.
        """
        if not self._recording:
            return np.zeros(0, dtype=np.float32)
        self._recording = False
        try:
            self._stream.stop()
            self._stream.close()
        finally:
            self._stream = None

        with self._lock:
            frames = self._frames
            self._frames = []

        if not frames:
            return np.zeros(0, dtype=np.float32)
        audio = np.concatenate(frames, axis=0)
        # Collapse to a 1-D mono signal regardless of input channel shape.
        return audio.reshape(-1).astype(np.float32)

    def duration(self, audio: np.ndarray) -> float:
        """Length of an audio buffer in seconds."""
        if audio is None or len(audio) == 0:
            return 0.0
        return len(audio) / float(self.sample_rate)
