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

import sys
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
    hk_rec      = Signal()
    hk_rec_hold = Signal()
    hk_play     = Signal()
    rec_event   = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self._kb_listener = None
        self._ms_listener = None
        self._rec_canon: str | None   = None
        self._play_canon: str | None  = None
        self._recording: bool  = False
        self._paused: bool     = False
        self._playing: bool    = False
        self._t0: float        = 0.0
        self._pause_start: float = 0.0
        self._last_replayed_canon: str | None = None
        self._last_replayed_at: float         = 0.0
        self._rec_key_down: bool   = False
        self._rec_hold_fired: bool = False
        self._rec_hold_timer: threading.Timer | None = None
        self._lock = threading.Lock()

    _HOLD_THRESHOLD: float = 0.8

    def set_hotkeys(self, rec_str: str, play_str: str) -> None:
        with self._lock:
            self._rec_canon  = str_to_canon(rec_str)
            self._play_canon = str_to_canon(play_str)

    def start_recording(self) -> None:
        with self._lock:
            self._t0        = time.time()
            self._recording = True

    def stop_recording(self) -> None:
        with self._lock:
            self._recording = False
            self._paused    = False

    def pause_recording(self) -> None:
        with self._lock:
            if self._recording and not self._paused:
                self._paused      = True
                self._pause_start = time.time()

    def resume_recording(self) -> None:
        with self._lock:
            if self._recording and self._paused:
                self._t0   += time.time() - self._pause_start
                self._paused = False

    def set_playing(self, playing: bool) -> None:
        with self._lock:
            self._playing = playing
            if not playing:
                self._last_replayed_canon = None

    def mark_replayed(self, canon: str) -> None:
        with self._lock:
            self._last_replayed_canon = canon
            self._last_replayed_at    = time.time()

    def mark_replayed_click(self) -> None:
        with self._lock:
            self._last_replayed_canon = "__click__"
            self._last_replayed_at    = time.time()

    def start(self) -> None:
        self._start_kb()
        self._start_ms()

    def stop(self) -> None:
        with self._lock:
            t = self._rec_hold_timer
            self._rec_hold_timer = None
            self._rec_key_down   = False
            self._rec_hold_fired = False
        if t:
            t.cancel()
        for attr in ("_kb_listener", "_ms_listener"):
            lsn = getattr(self, attr, None)
            if lsn:
                try:
                    lsn.stop()
                except Exception:
                    pass
                setattr(self, attr, None)

    @staticmethod
    def _patch_ax_is_trusted() -> None:
        if sys.platform != "darwin":
            return
        try:
            import HIServices  # pyobjc-framework-ApplicationServices
            try:
                _ = HIServices.AXIsProcessTrusted  # already accessible → done
                return
            except (KeyError, AttributeError):
                pass
            import ctypes
            _lib = ctypes.cdll.LoadLibrary(
                "/System/Library/Frameworks/ApplicationServices.framework"
                "/ApplicationServices"
            )
            _lib.AXIsProcessTrusted.restype  = ctypes.c_bool
            _lib.AXIsProcessTrusted.argtypes = []
            _fn = _lib.AXIsProcessTrusted
            HIServices.AXIsProcessTrusted = lambda: bool(_fn())
        except Exception:
            pass

    def _start_kb(self) -> None:
        self._patch_ax_is_trusted()

        def on_press(key: object) -> None:
            canon = key_to_canon(key)
            with self._lock:
                rc         = self._rec_canon
                pc         = self._play_canon
                recording  = self._recording
                paused     = self._paused
                t          = time.time() - self._t0
                last_rep   = self._last_replayed_canon
                last_rep_t = self._last_replayed_at

            synthetic = (
                canon is not None
                and canon == last_rep
                and (time.time() - last_rep_t) < 0.15
            )

            if canon and canon == rc and not synthetic:
                with self._lock:
                    if self._rec_key_down:
                        return
                    def _fire_hold() -> None:
                        with self._lock:
                            if not self._rec_key_down:
                                return
                            self._rec_hold_fired = True
                            self._rec_hold_timer = None
                        self.hk_rec_hold.emit()

                    self._rec_key_down   = True
                    self._rec_hold_fired = False
                    self._rec_hold_timer = threading.Timer(self._HOLD_THRESHOLD, _fire_hold)
                    self._rec_hold_timer.daemon = True
                    self._rec_hold_timer.start()
                return
            if canon and canon == pc and not synthetic:
                self.hk_play.emit()
                return
            if recording and not paused:
                self.rec_event.emit(
                    {"type": "key_press", "key": ser_key(key), "time": t})

        def on_release(key: object) -> None:
            canon = key_to_canon(key)
            with self._lock:
                rc        = self._rec_canon
                key_down  = self._rec_key_down
                recording = self._recording
                paused    = self._paused
                t         = time.time() - self._t0

            if canon and canon == rc and key_down:
                with self._lock:
                    hold_fired = self._rec_hold_fired
                    self._rec_key_down   = False
                    self._rec_hold_fired = False
                    if self._rec_hold_timer:
                        self._rec_hold_timer.cancel()
                        self._rec_hold_timer = None
                if not hold_fired:
                    self.hk_rec.emit()
                return
            if recording and not paused:
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
                if not self._recording or self._paused:
                    return
                t = time.time() - self._t0
            self.rec_event.emit({"type": "mouse_move", "x": x, "y": y, "time": t, "recorded": True})

        def on_click(x: int, y: int, b: object, pr: bool) -> None:
            with self._lock:
                if not self._recording or self._paused:
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
                if not self._recording or self._paused:
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
