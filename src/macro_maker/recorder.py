"""
MORIS UNIVERSAL LICENSE (MUL) - Version 1.0
Copyright (c) moris

This software is licensed under the MORIS UNIVERSAL LICENSE (MUL).
By downloading, copying, or running this software, you agree to accept all terms and conditions
of the MUL license, which are included in the accompanying LICENSE.md file.

KEY TERMS:
- Personal use only (non-commercial)
- Attribution to original author is REQUIRED
- Commercial use is strictly prohibited
- Redistribution without license and attribution is prohibited
- Personal modifications allowed, but derivatives must retain original credit
- NO WARRANTY - use at your own risk

Full license text: See LICENSE.md
For support: https://discord.gg/2fraBuhe3m
"""

"""MacroRecorder: captures keyboard and mouse events via pynput listeners."""

import threading
import time
from typing import Callable

from PySide6.QtCore import QObject, Signal

from .utils.serialization import (
    key_to_canon,
    ser_key,
    str_to_canon,
)

try:
    from pynput import keyboard as _kb, mouse as _ms
    _OK = True
except ImportError:
    _OK = False


class MacroRecorder(QObject):
    """Listens to keyboard and mouse input and emits captured events.

    Signals:
        hk_rec:    Emitted when the record hotkey is pressed.
        hk_play:   Emitted when the play hotkey is pressed.
        rec_event: Emitted for each captured input event dict.
    """

    hk_rec    = Signal()
    hk_play   = Signal()
    rec_event = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self._kb_listener = None
        self._ms_listener = None
        self._rec_canon: str | None   = None
        self._play_canon: str | None  = None
        self._recording: bool  = False
        self._playing: bool    = False
        self._t0: float        = 0.0
        self._last_replayed_canon: str | None = None
        self._last_replayed_at: float         = 0.0
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def set_hotkeys(self, rec_str: str, play_str: str) -> None:
        """Update the record and play hotkey canon strings.

        Args:
            rec_str:  Human-readable key name for record toggle (e.g. ``"F1"``).
            play_str: Human-readable key name for play toggle (e.g. ``"F2"``).
        """
        with self._lock:
            self._rec_canon  = str_to_canon(rec_str)
            self._play_canon = str_to_canon(play_str)

    # ------------------------------------------------------------------
    # Recording control
    # ------------------------------------------------------------------

    def start_recording(self) -> None:
        """Begin recording; resets the internal timer."""
        with self._lock:
            self._t0        = time.time()
            self._recording = True

    def stop_recording(self) -> None:
        """Stop recording."""
        with self._lock:
            self._recording = False

    # ------------------------------------------------------------------
    # Playback state (used to suppress echo during playback)
    # ------------------------------------------------------------------

    def set_playing(self, playing: bool) -> None:
        """Inform the recorder whether playback is active.

        Args:
            playing: ``True`` while the player is running.
        """
        with self._lock:
            self._playing = playing
            if not playing:
                self._last_replayed_canon = None

    def mark_replayed(self, canon: str) -> None:
        """Mark a key as just replayed so echoes are suppressed.

        Args:
            canon: Canonical key string that was synthetically sent.
        """
        with self._lock:
            self._last_replayed_canon = canon
            self._last_replayed_at    = time.time()

    def mark_replayed_click(self) -> None:
        """Mark that a mouse click was just synthetically sent."""
        with self._lock:
            self._last_replayed_canon = "__click__"
            self._last_replayed_at    = time.time()

    # ------------------------------------------------------------------
    # Listener lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start keyboard and mouse listeners."""
        self._start_kb()
        self._start_ms()

    def stop(self) -> None:
        """Stop all listeners."""
        for attr in ("_kb_listener", "_ms_listener"):
            lsn = getattr(self, attr, None)
            if lsn:
                try:
                    lsn.stop()
                except Exception:
                    pass
                setattr(self, attr, None)

    # ------------------------------------------------------------------
    # Internal listener setup
    # ------------------------------------------------------------------

    def _start_kb(self) -> None:
        def on_press(key: object) -> None:
            canon = key_to_canon(key)
            with self._lock:
                rc        = self._rec_canon
                pc        = self._play_canon
                recording = self._recording
                t         = time.time() - self._t0
                last_rep   = self._last_replayed_canon
                last_rep_t = self._last_replayed_at

            synthetic = (
                canon is not None
                and canon == last_rep
                and (time.time() - last_rep_t) < 0.15
            )

            if canon and canon == rc and not synthetic:
                self.hk_rec.emit()
                return
            if canon and canon == pc and not synthetic:
                self.hk_play.emit()
                return
            if recording:
                self.rec_event.emit(
                    {"type": "key_press", "key": ser_key(key), "time": t})

        def on_release(key: object) -> None:
            with self._lock:
                recording = self._recording
                t         = time.time() - self._t0
            if recording:
                self.rec_event.emit(
                    {"type": "key_release", "key": ser_key(key), "time": t})

        if not _OK:
            return
        self._kb_listener = _kb.Listener(on_press=on_press, on_release=on_release)
        self._kb_listener.daemon = True
        self._kb_listener.start()

    def _start_ms(self) -> None:
        def on_move(x: int, y: int) -> None:
            with self._lock:
                if not self._recording:
                    return
                t = time.time() - self._t0
            self.rec_event.emit({"type": "mouse_move", "x": x, "y": y, "time": t})

        def on_click(x: int, y: int, b: object, pr: bool) -> None:
            with self._lock:
                if not self._recording:
                    return
                t          = time.time() - self._t0
                last_rep   = self._last_replayed_canon
                last_rep_t = self._last_replayed_at
            if last_rep and (time.time() - last_rep_t) < 0.15:
                return
            bs = str(b).lower()
            if "right" in bs:
                btn = "right"
            elif "middle" in bs:
                btn = "middle"
            else:
                btn = "left"
            self.rec_event.emit({
                "type":    "mouse_click",
                "x":       x,
                "y":       y,
                "button":  btn,
                "pressed": pr,
                "time":    t,
            })

        def on_scroll(x: int, y: int, dx: float, dy: float) -> None:
            with self._lock:
                if not self._recording:
                    return
                t = time.time() - self._t0
            self.rec_event.emit({
                "type": "mouse_scroll",
                "x":    x, "y": y,
                "dx":   dx, "dy": dy,
                "time": t,
            })

        if not _OK:
            return
        self._ms_listener = _ms.Listener(
            on_move=on_move, on_click=on_click, on_scroll=on_scroll)
        self._ms_listener.daemon = True
        self._ms_listener.start()
