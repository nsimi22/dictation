"""Configuration loading and defaults.

The app is configured via a small YAML file. We look for it in the standard
per-user config directory (so it survives upgrades), but a path can also be
passed explicitly. Any missing keys fall back to sensible defaults, so a user
can override just the handful of settings they care about.
"""

from __future__ import annotations

import os
import sys
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

import yaml

APP_NAME = "free-dictation"


def default_hotkey() -> str:
    """Pick a sensible hold-to-talk key per platform.

    Right-hand modifiers are chosen because they are rarely used on their own,
    so holding them to dictate is unlikely to clash with normal typing.
    """
    if sys.platform == "darwin":
        return "right_cmd"
    return "right_ctrl"


@dataclass
class Config:
    # --- Hotkey (hold-to-talk) ---
    # Key you hold down while speaking. Released => transcribe + type.
    # See output of `dictate --list-keys` for accepted names.
    hotkey: str = field(default_factory=default_hotkey)

    # --- Whisper model ---
    # tiny / base / small / medium / large-v3 (and *.en English-only variants).
    # Bigger = more accurate but slower and more memory. "base.en" is a good
    # starting point for English on a laptop CPU.
    model: str = "base.en"
    # "auto" picks CUDA if available else CPU. Force with "cpu" or "cuda".
    device: str = "auto"
    # int8 is fast and light on CPU; float16 is good on GPU.
    compute_type: str = "auto"
    # Language hint, e.g. "en". null/empty => Whisper auto-detects.
    language: str | None = "en"

    # --- Audio ---
    sample_rate: int = 16000  # Whisper expects 16 kHz mono.
    input_device: int | str | None = None  # None => system default mic.
    # Ignore press-and-release shorter than this (accidental taps), seconds.
    min_duration: float = 0.3

    # --- Output / typing ---
    # "paste": copy to clipboard and simulate Cmd/Ctrl+V (fast, handles emoji).
    # "type": simulate individual keystrokes (works where paste is blocked).
    output_mode: str = "paste"
    # When pasting, restore whatever was on the clipboard afterwards.
    restore_clipboard: bool = True
    # Add a trailing space after dictated text so phrases run together nicely.
    trailing_space: bool = True
    # Capitalize the first letter of the result.
    capitalize_first: bool = True

    # --- Feedback ---
    # Play a short sound when recording starts/stops.
    sound_cues: bool = True
    # Print transcripts and status to the console.
    verbose: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        """Build a Config from a dict, ignoring unknown keys and keeping defaults."""
        known = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in (data or {}).items() if k in known}
        return cls(**filtered)

    def to_yaml(self) -> str:
        return yaml.safe_dump(asdict(self), sort_keys=False, default_flow_style=False)


def config_dir() -> Path:
    """Standard per-user config directory for the app."""
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:  # Linux / other
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / APP_NAME


def default_config_path() -> Path:
    return config_dir() / "config.yaml"


def load_config(path: str | os.PathLike | None = None) -> Config:
    """Load config from `path` (or the default location), filling in defaults.

    A missing file is not an error — defaults are returned.
    """
    cfg_path = Path(path) if path else default_config_path()
    if cfg_path.is_file():
        with open(cfg_path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        if not isinstance(data, dict):
            raise ValueError(f"Config file {cfg_path} must contain a YAML mapping.")
        return Config.from_dict(data)
    return Config()


def write_default_config(path: str | os.PathLike | None = None) -> Path:
    """Write a default config file (creating parent dirs). Returns the path."""
    cfg_path = Path(path) if path else default_config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(Config().to_yaml(), encoding="utf-8")
    return cfg_path
