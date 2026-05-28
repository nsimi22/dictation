"""The dictation application: wires the hotkey, recorder, model and output.

Flow (hold-to-talk):
    press hotkey   -> start recording (+ start cue)
    release hotkey -> stop recording (+ stop cue) -> transcribe -> type text

The Whisper model is loaded up front so the first dictation isn't slow.
Transcription runs on a worker thread so releasing the key never blocks the
keyboard listener.
"""

from __future__ import annotations

import threading
import time

from .audio import Recorder
from .config import Config
from .feedback import start_cue, stop_cue
from .keys import parse_key
from .output import TextInjector
from .text import clean_transcript
from .transcribe import Transcriber


class DictationApp:
    def __init__(
        self,
        config: Config,
        *,
        on_status=None,
        on_transcript=None,
        on_log=None,
    ):
        self.config = config
        # Optional hooks so a GUI (or other front-end) can observe the app
        # without poking at internals. All are best-effort and may be None.
        #   on_status(state: str)      -> "ready" | "recording" | "transcribing"
        #   on_transcript(text: str)   -> final, cleaned text that was inserted
        #   on_log(message: str)       -> human-readable status/log lines
        self.on_status = on_status
        self.on_transcript = on_transcript
        self.on_log = on_log
        self.recorder = Recorder(
            sample_rate=config.sample_rate,
            input_device=config.input_device,
        )
        self.transcriber = Transcriber(
            model=config.model,
            device=config.device,
            compute_type=config.compute_type,
            language=config.language,
        )
        self.injector = TextInjector(
            mode=config.output_mode,
            restore_clipboard=config.restore_clipboard,
        )
        self._hotkey = None
        self._listener = None
        self._press_time: float | None = None
        # Guards against key auto-repeat firing many press events while held.
        self._active = False

    # --- logging -----------------------------------------------------------
    def _log(self, message: str) -> None:
        if self.config.verbose:
            print(message, flush=True)
        if self.on_log is not None:
            try:
                self.on_log(message)
            except Exception:
                pass

    def _status(self, state: str) -> None:
        if self.on_status is not None:
            try:
                self.on_status(state)
            except Exception:
                pass

    # --- lifecycle ---------------------------------------------------------
    def start(self) -> None:
        from pynput import keyboard

        self._hotkey = parse_key(self.config.hotkey)

        self._log(f"Loading Whisper model '{self.config.model}' "
                  f"({self.transcriber.device}/{self.transcriber.compute_type})...")
        self.transcriber.load()

        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()
        self._log(
            f"Ready. Hold [{self.config.hotkey}] and speak; release to dictate. "
            "Press Ctrl+C in this window to quit."
        )
        self._status("ready")

    def run_forever(self) -> None:
        """Start and block until interrupted."""
        self.start()
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            self._log("\nShutting down.")
        finally:
            self.stop()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    # --- hotkey handling ---------------------------------------------------
    def _matches(self, key) -> bool:  # noqa: ANN001
        return key == self._hotkey

    def _on_press(self, key) -> None:  # noqa: ANN001
        if not self._matches(key) or self._active:
            return  # ignore other keys and auto-repeat while held
        self._active = True
        self._press_time = time.monotonic()
        try:
            self.recorder.start()
        except Exception as exc:  # mic unavailable, etc.
            self._active = False
            self._log(f"[error] Could not start recording: {exc}")
            return
        if self.config.sound_cues:
            start_cue()
        self._status("recording")
        self._log("● recording...")

    def _on_release(self, key) -> None:  # noqa: ANN001
        if not self._matches(key) or not self._active:
            return
        self._active = False
        held = time.monotonic() - (self._press_time or time.monotonic())
        audio = self.recorder.stop()
        if self.config.sound_cues:
            stop_cue()

        if held < self.config.min_duration:
            self._log(f"(ignored {held:.2f}s tap)")
            self._status("ready")
            return

        # Transcribe off the listener thread so we never block key events.
        threading.Thread(
            target=self._transcribe_and_type,
            args=(audio,),
            daemon=True,
        ).start()

    # --- worker ------------------------------------------------------------
    def _transcribe_and_type(self, audio) -> None:  # noqa: ANN001
        self._status("transcribing")
        try:
            raw = self.transcriber.transcribe(audio)
        except Exception as exc:
            self._log(f"[error] Transcription failed: {exc}")
            self._status("ready")
            return

        text = clean_transcript(
            raw,
            capitalize_first=self.config.capitalize_first,
            trailing_space=self.config.trailing_space,
        )
        if not text:
            self._log("(no speech detected)")
            self._status("ready")
            return

        self._log(f"📝 {text.rstrip()}")
        try:
            self.injector.send(text)
        except Exception as exc:
            self._log(f"[error] Could not type text: {exc}")
            self._log("   On macOS, grant Accessibility permission (see README).")
        else:
            if self.on_transcript is not None:
                try:
                    self.on_transcript(text)
                except Exception:
                    pass
        self._status("ready")
