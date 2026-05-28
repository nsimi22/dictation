"""Command-line entry point for the dictation app.

Examples:
    dictate                      # run with defaults (or your config file)
    dictate --init               # write a default config file and exit
    dictate --model small.en     # override the Whisper model for this run
    dictate --hotkey right_alt   # override the hold-to-talk key
    dictate --list-keys          # show accepted hotkey names
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .config import default_config_path, load_config, write_default_config


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dictate",
        description="Free, local, hold-to-talk dictation (Willow Voice alternative).",
    )
    p.add_argument("--version", action="version", version=f"free-dictation {__version__}")
    p.add_argument("-c", "--config", help="Path to a config file (YAML).")
    p.add_argument(
        "--init",
        action="store_true",
        help="Write a default config file to the standard location and exit.",
    )
    p.add_argument("--gui", action="store_true", help="Launch the desktop GUI instead of the CLI.")
    p.add_argument("--list-keys", action="store_true", help="List valid hotkey names and exit.")
    p.add_argument("--list-devices", action="store_true", help="List audio input devices and exit.")
    # Per-run overrides of the most common settings.
    p.add_argument("--hotkey", help="Override the hold-to-talk key.")
    p.add_argument("--model", help="Override the Whisper model (e.g. base.en, small, large-v3).")
    p.add_argument("--device", help="Override compute device (auto/cpu/cuda).")
    p.add_argument("--language", help="Override language hint (e.g. en). Use 'auto' to detect.")
    p.add_argument(
        "--output-mode",
        choices=["paste", "type"],
        help="How to insert text into the focused app.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.init:
        path = write_default_config(args.config)
        print(f"Wrote default config to {path}")
        return 0

    if args.gui:
        from .gui import main as gui_main

        return gui_main(["--config", args.config] if args.config else None)

    if args.list_keys:
        from .keys import available_key_names

        print("Accepted hotkey names:\n  " + "\n  ".join(available_key_names()))
        return 0

    if args.list_devices:
        try:
            import sounddevice as sd

            print(sd.query_devices())
        except Exception as exc:
            print(f"Could not query audio devices: {exc}", file=sys.stderr)
            return 1
        return 0

    config = load_config(args.config)

    # Apply CLI overrides.
    if args.hotkey:
        config.hotkey = args.hotkey
    if args.model:
        config.model = args.model
    if args.device:
        config.device = args.device
    if args.language:
        config.language = None if args.language.lower() == "auto" else args.language
    if args.output_mode:
        config.output_mode = args.output_mode

    if not (args.config) and not default_config_path().is_file():
        print(
            f"(no config file found; using defaults. Run 'dictate --init' to create "
            f"{default_config_path()})"
        )

    # Import here so --list-* and --init work even without audio/ML deps.
    from .app import DictationApp

    app = DictationApp(config)
    app.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
