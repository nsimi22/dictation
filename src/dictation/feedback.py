"""Lightweight start/stop cues so you know when the mic is live.

Uses built-in OS sounds where possible and degrades gracefully (to nothing)
if they are unavailable. Kept dependency-free on purpose.
"""

from __future__ import annotations

import subprocess
import sys


def _play_macos(path: str) -> bool:
    try:
        subprocess.Popen(
            ["afplay", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def start_cue() -> None:
    """Audible cue that recording has started."""
    if sys.platform == "darwin":
        if _play_macos("/System/Library/Sounds/Pop.aiff"):
            return
    _terminal_bell()


def stop_cue() -> None:
    """Audible cue that recording has stopped / is being transcribed."""
    if sys.platform == "darwin":
        if _play_macos("/System/Library/Sounds/Tink.aiff"):
            return
    _terminal_bell()


def _terminal_bell() -> None:
    try:
        sys.stdout.write("\a")
        sys.stdout.flush()
    except Exception:
        pass
