"""Inject transcribed text into the focused application.

Two strategies are supported:

* "paste" (default): put the text on the clipboard and simulate the platform
  paste shortcut (Cmd+V on macOS, Ctrl+V elsewhere). This is fast and handles
  any Unicode/emoji, at the cost of briefly using the clipboard (we restore it
  afterwards by default).
* "type": simulate individual keystrokes. Slower and ASCII-friendliest, but
  works in places that block programmatic paste.
"""

from __future__ import annotations

import sys
import time


class TextInjector:
    def __init__(
        self,
        mode: str = "paste",
        restore_clipboard: bool = True,
    ):
        self.mode = mode
        self.restore_clipboard = restore_clipboard
        self._controller = None

    def _keyboard(self):
        if self._controller is None:
            from pynput.keyboard import Controller

            self._controller = Controller()
        return self._controller

    def send(self, text: str) -> None:
        """Type/paste `text` into whatever window currently has focus."""
        if not text:
            return
        if self.mode == "type":
            self._type(text)
        else:
            self._paste(text)

    def _type(self, text: str) -> None:
        self._keyboard().type(text)

    def _paste(self, text: str) -> None:
        import pyperclip
        from pynput.keyboard import Controller, Key

        previous = None
        if self.restore_clipboard:
            try:
                previous = pyperclip.paste()
            except Exception:
                previous = None

        # If we can't put our text on the clipboard, bail out rather than
        # firing the paste shortcut — otherwise we'd paste whatever stale
        # content happened to already be there.
        try:
            pyperclip.copy(text)
        except Exception as exc:
            raise RuntimeError(f"Could not write to clipboard: {exc}") from exc

        kb: Controller = self._keyboard()
        modifier = Key.cmd if sys.platform == "darwin" else Key.ctrl
        with kb.pressed(modifier):
            kb.press("v")
            kb.release("v")

        if self.restore_clipboard and previous is not None:
            # Give the target app a moment to read the clipboard before we
            # put the old contents back, otherwise the paste can race.
            time.sleep(0.15)
            try:
                pyperclip.copy(previous)
            except Exception:
                pass
