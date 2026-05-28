"""Friendly key-name parsing for hotkeys.

Maps human-friendly names from the config (e.g. "right_cmd", "f13") onto the
pynput key objects used by the listener, and accepts a few common aliases so
users don't have to remember pynput's exact spelling.
"""

from __future__ import annotations

# Aliases -> canonical pynput Key attribute names.
_ALIASES = {
    "right_cmd": "cmd_r",
    "left_cmd": "cmd_l",
    "cmd": "cmd",
    "command": "cmd",
    "right_command": "cmd_r",
    "win": "cmd",
    "super": "cmd",
    "right_ctrl": "ctrl_r",
    "left_ctrl": "ctrl_l",
    "control": "ctrl",
    "right_alt": "alt_r",
    "left_alt": "alt_l",
    "right_option": "alt_r",
    "option": "alt",
    "right_shift": "shift_r",
    "left_shift": "shift_l",
    "esc": "esc",
    "escape": "esc",
}


def parse_key(name: str):
    """Resolve a config key name to a pynput Key or KeyCode.

    Raises ValueError with the list of accepted special keys if unknown.
    """
    from pynput import keyboard

    raw = (name or "").strip().lower()
    canonical = _ALIASES.get(raw, raw)

    # Special keys live as attributes on keyboard.Key (e.g. Key.cmd_r, Key.f13).
    if hasattr(keyboard.Key, canonical):
        return getattr(keyboard.Key, canonical)

    # Single printable character (e.g. a letter) as a literal key.
    if len(canonical) == 1:
        return keyboard.KeyCode.from_char(canonical)

    raise ValueError(
        f"Unknown hotkey {name!r}. Try one of: {', '.join(available_key_names())}"
    )


def available_key_names() -> list[str]:
    """Names users can put in `hotkey:` — special keys plus our aliases."""
    from pynput import keyboard

    special = sorted(k for k in dir(keyboard.Key) if not k.startswith("_"))
    return sorted(set(special) | set(_ALIASES))
