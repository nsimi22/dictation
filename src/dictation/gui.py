"""A simple desktop GUI for setup and settings.

Built on Tkinter, which ships with Python and runs natively on macOS and
Windows, so there is nothing extra to install. The window lets you:

  * pick the hold-to-talk hotkey, Whisper model, language, microphone, and
    output mode, then save them to the config file;
  * start/stop the dictation listener;
  * see live status (ready / recording / transcribing) and a running log of
    what was dictated.

Threading model: Tk owns the main thread. The dictation listener and the
model load run on background threads, and every UI update they trigger is
marshalled back onto the Tk thread via ``root.after`` so Tkinter is only ever
touched from one thread.
"""

from __future__ import annotations

import threading
from pathlib import Path

from .config import default_config_path, load_config, write_default_config

# Model names offered in the dropdown (the box is editable for custom names).
MODEL_CHOICES = [
    "tiny.en", "tiny",
    "base.en", "base",
    "small.en", "small",
    "medium.en", "medium",
    "large-v3",
]

STATUS_COLORS = {
    "stopped": "#888888",
    "loading": "#d18616",
    "ready": "#2e7d32",
    "recording": "#c62828",
    "transcribing": "#1565c0",
}


class DictationGUI:
    def __init__(self, config_path=None):
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.config_path = Path(config_path) if config_path else default_config_path()
        self.config = load_config(self.config_path)
        self.app = None  # the running DictationApp, if any

        self.root = tk.Tk()
        self.root.title("free-dictation")
        self.root.minsize(460, 560)

        self._build_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # -- thread-safe UI helper ---------------------------------------------
    def _ui(self, fn, *args) -> None:
        """Schedule ``fn(*args)`` to run on the Tk main thread."""
        try:
            self.root.after(0, lambda: fn(*args))
        except RuntimeError:
            pass  # window already destroyed

    # -- layout -------------------------------------------------------------
    def _labeled(self, parent, text, widget, row) -> None:
        """Place a caption in column 0 and an input widget in column 1."""
        self.ttk.Label(parent, text=text).grid(
            row=row, column=0, sticky="w", padx=8, pady=4
        )
        widget.grid(row=row, column=1, sticky="ew", padx=8, pady=4)

    def _check(self, parent, text, var, row) -> None:
        """Place a full-width checkbox spanning both columns."""
        self.ttk.Checkbutton(parent, text=text, variable=var).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=8, pady=2
        )

    def _build_widgets(self) -> None:
        tk, ttk = self.tk, self.ttk
        pad = {"padx": 10, "pady": 4}

        # Status bar.
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", **pad)
        self.status_dot = tk.Canvas(status_frame, width=14, height=14, highlightthickness=0)
        self.status_dot.pack(side="left")
        self._dot = self.status_dot.create_oval(
            2, 2, 12, 12, fill=STATUS_COLORS["stopped"], outline=""
        )
        self.status_label = ttk.Label(status_frame, text="Stopped", font=("", 12, "bold"))
        self.status_label.pack(side="left", padx=8)

        # Settings.
        settings = ttk.LabelFrame(self.root, text="Settings")
        settings.pack(fill="x", **pad)
        settings.columnconfigure(1, weight=1)
        row = 0

        self.var_hotkey = tk.StringVar(value=self.config.hotkey)
        self._labeled(
            settings, "Hold-to-talk key",
            ttk.Entry(settings, textvariable=self.var_hotkey), row,
        )
        row += 1

        self.var_model = tk.StringVar(value=self.config.model)
        self._labeled(
            settings, "Model",
            ttk.Combobox(settings, textvariable=self.var_model, values=MODEL_CHOICES), row,
        )
        row += 1

        self.var_language = tk.StringVar(value=self.config.language or "auto")
        self._labeled(
            settings, "Language",
            ttk.Entry(settings, textvariable=self.var_language), row,
        )
        row += 1

        self.var_device = tk.StringVar()
        self._device_map = self._discover_devices()
        self._labeled(
            settings, "Microphone",
            ttk.Combobox(
                settings, textvariable=self.var_device,
                values=list(self._device_map.keys()), state="readonly",
            ),
            row,
        )
        self.var_device.set(self._initial_device_label())
        row += 1

        self.var_output = tk.StringVar(value=self.config.output_mode)
        self._labeled(
            settings, "Output mode",
            ttk.Combobox(
                settings, textvariable=self.var_output,
                values=["paste", "type"], state="readonly",
            ),
            row,
        )
        row += 1

        # Checkboxes.
        self.var_capitalize = tk.BooleanVar(value=self.config.capitalize_first)
        self.var_trailing = tk.BooleanVar(value=self.config.trailing_space)
        self.var_sound = tk.BooleanVar(value=self.config.sound_cues)
        self._check(settings, "Capitalize first letter", self.var_capitalize, row)
        row += 1
        self._check(settings, "Add trailing space", self.var_trailing, row)
        row += 1
        self._check(settings, "Sound cues", self.var_sound, row)
        row += 1

        # Buttons.
        btns = ttk.Frame(self.root)
        btns.pack(fill="x", **pad)
        self.start_btn = ttk.Button(btns, text="Start Dictation", command=self._toggle)
        self.start_btn.pack(side="left")
        ttk.Button(btns, text="Save Settings", command=self._save_settings).pack(
            side="left", padx=8
        )

        # Log / transcript area.
        log_frame = ttk.LabelFrame(self.root, text="Activity")
        log_frame.pack(fill="both", expand=True, **pad)
        self.log = tk.Text(log_frame, height=10, wrap="word", state="disabled")
        scroll = ttk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)

        self._append_log(f"Config: {self.config_path}")
        self._append_log("Set your options, then click Start Dictation.")

    # -- device discovery ---------------------------------------------------
    def _discover_devices(self) -> dict:
        """Map a display label -> device index (or None for the default)."""
        devices = {"System default": None}
        try:
            import sounddevice as sd

            for idx, dev in enumerate(sd.query_devices()):
                if dev.get("max_input_channels", 0) > 0:
                    devices[f"[{idx}] {dev['name']}"] = idx
        except Exception:
            pass  # sounddevice/PortAudio unavailable; default-only is fine
        return devices

    def _initial_device_label(self) -> str:
        for label, idx in self._device_map.items():
            if idx == self.config.input_device:
                return label
        return "System default"

    # -- settings <-> config ------------------------------------------------
    def _collect_settings(self) -> None:
        lang = self.var_language.get().strip()
        self.config.hotkey = self.var_hotkey.get().strip() or self.config.hotkey
        self.config.model = self.var_model.get().strip() or self.config.model
        self.config.language = None if lang.lower() in ("", "auto") else lang
        self.config.input_device = self._device_map.get(self.var_device.get(), None)
        self.config.output_mode = self.var_output.get()
        self.config.capitalize_first = self.var_capitalize.get()
        self.config.trailing_space = self.var_trailing.get()
        self.config.sound_cues = self.var_sound.get()
        # The GUI shows its own log, so keep console output quiet by default.
        self.config.verbose = False

    def _save_settings(self) -> None:
        self._collect_settings()
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(self.config.to_yaml(), encoding="utf-8")
        self._append_log(f"Saved settings to {self.config_path}")

    # -- start / stop -------------------------------------------------------
    def _toggle(self) -> None:
        if self.app is None:
            self._start()
        else:
            self._stop()

    def _start(self) -> None:
        from .keys import parse_key
        from .app import DictationApp

        self._collect_settings()

        # Validate the hotkey up front so we can show a friendly error.
        try:
            parse_key(self.config.hotkey)
        except Exception as exc:
            self._append_log(f"[error] {exc}")
            return

        self.app = DictationApp(
            self.config,
            on_status=lambda s: self._ui(self._set_status, s),
            on_transcript=lambda t: self._ui(self._append_transcript, t),
            on_log=lambda m: self._ui(self._append_log, m),
        )
        self.start_btn.config(text="Stop Dictation")
        self._set_status("loading")
        self._append_log("Loading model (first run may download it)...")

        # app.start() loads the model (blocking) then starts the listener;
        # run it off the UI thread so the window stays responsive.
        threading.Thread(target=self._start_worker, daemon=True).start()

    def _start_worker(self) -> None:
        try:
            self.app.start()
        except Exception as exc:
            # Run all cleanup on the Tk thread so shared state (self.app) and
            # the widgets are only ever touched from one thread.
            self._ui(self._on_start_failed, exc)

    def _on_start_failed(self, exc) -> None:
        self._append_log(f"[error] Could not start: {exc}")
        self.app = None
        self.start_btn.config(text="Start Dictation")
        self._set_status("stopped")

    def _stop(self) -> None:
        if self.app is not None:
            self.app.stop()
            self.app = None
        self.start_btn.config(text="Start Dictation")
        self._set_status("stopped")
        self._append_log("Stopped.")

    # -- UI updates (Tk thread only) ---------------------------------------
    def _set_status(self, state: str) -> None:
        label = {
            "stopped": "Stopped",
            "loading": "Loading model...",
            "ready": "Ready - hold your hotkey and speak",
            "recording": "Recording...",
            "transcribing": "Transcribing...",
        }.get(state, state.title())
        self.status_label.config(text=label)
        self.status_dot.itemconfig(self._dot, fill=STATUS_COLORS.get(state, "#888888"))

    def _append_log(self, message: str) -> None:
        self.log.config(state="normal")
        self.log.insert("end", message.rstrip() + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def _append_transcript(self, text: str) -> None:
        self._append_log(f"✍ {text.rstrip()}")

    # -- lifecycle ----------------------------------------------------------
    def _on_close(self) -> None:
        if self.app is not None:
            self.app.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="dictate-gui",
        description="Desktop GUI for free-dictation (setup, settings, start/stop).",
    )
    parser.add_argument("-c", "--config", help="Path to a config file (YAML).")
    parser.add_argument(
        "--init",
        action="store_true",
        help="Write a default config file and exit.",
    )
    args = parser.parse_args(argv)

    if args.init:
        path = write_default_config(args.config)
        print(f"Wrote default config to {path}")
        return 0

    try:
        import tkinter  # noqa: F401
    except Exception:
        print(
            "Tkinter is not available in this Python build.\n"
            "  macOS: it's included with python.org installers (or `brew install python-tk`).\n"
            "  Windows: it's included with the standard python.org installer.\n"
            "Alternatively, run the command-line version with `dictate`."
        )
        return 1

    DictationGUI(config_path=args.config).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
