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

"""MacroPlayer: plays back recorded macro events in a background thread."""

import ctypes
import threading
import time
from typing import Optional

from PySide6.QtCore import QObject, Signal

from .utils.platform_helpers import INPUT, MOUSEINPUT, send_mouse_input
from .utils.serialization import parse_key, send_webhook, ser_key_to_canon
from .utils.constants import (
    INPUT_MOUSE,
    MOUSEEVENTF_ABSOLUTE,
    MOUSEEVENTF_MOVE,
    MOUSEEVENTF_VIRTUALDESK,
)

try:
    from pynput.keyboard import Controller as KbCtrl
    from pynput.mouse import Controller as MsCtrl
    _OK = True
except ImportError:
    _OK = False


def _release_all(
    kb: Optional[object],
    pressed_keys: set,
    ms: Optional[object],
    pressed_btns: set,
) -> None:
    """Release all currently pressed keys and mouse buttons.

    Args:
        kb:           Keyboard controller (may be ``None``).
        pressed_keys: Set of currently held pynput key objects.
        ms:           Mouse controller (may be ``None``).
        pressed_btns: Set of currently held pynput button objects.
    """
    if kb:
        for k in list(pressed_keys):
            try:
                kb.release(k)
            except Exception:
                pass
    if ms:
        for b in list(pressed_btns):
            try:
                ms.release(b)
            except Exception:
                pass


class PlayWorker(QObject):
    """Runs a single playback pass in the thread it is moved to.

    Signals:
        finished: Emitted when all events have been dispatched (or stopped).
    """

    finished = Signal()

    def __init__(
        self,
        events: list,
        speed: float,
        listener: Optional[object] = None,
        loop_count: int = 0,
        wh_show_elapsed: bool = True,
        wh_show_cycles: bool  = True,
        global_wall_start: Optional[float] = None,
    ) -> None:
        """Initialise the worker.

        Args:
            events:            List of event dicts to replay.
            speed:             Playback speed multiplier (>1 = faster).
            listener:          MacroRecorder instance for echo suppression.
            loop_count:        Current loop iteration count for webhooks.
            wh_show_elapsed:   Include elapsed time in webhook embeds.
            wh_show_cycles:    Include cycle count in webhook embeds.
            global_wall_start: Wall-clock start time for elapsed calculation.
        """
        super().__init__()
        self._ev                 = events
        self._speed              = speed
        self._listener           = listener
        self._stop_evt           = threading.Event()
        self._kb: Optional[object] = None
        self._ms: Optional[object] = None
        self._pkeys: set           = set()
        self._pbtns: set           = set()
        self._loop_count         = loop_count
        self._wh_show_elapsed    = wh_show_elapsed
        self._wh_show_cycles     = wh_show_cycles
        self._global_wall_start  = global_wall_start

    def run(self) -> None:
        """Execute the playback loop. Called by the owning QThread."""
        if not _OK or not self._ev:
            self.finished.emit()
            return

        kb = KbCtrl()
        ms = MsCtrl()
        self._kb = kb
        self._ms = ms

        t_offset   = self._ev[0]["time"]
        wall_start = time.perf_counter()

        for ev in self._ev:
            if self._stop_evt.is_set():
                break

            target = (ev["time"] - t_offset) / self._speed
            now    = time.perf_counter() - wall_start
            delay  = target - now
            if delay > 0.001:
                self._stop_evt.wait(timeout=delay)
                if self._stop_evt.is_set():
                    break

            tp = ev["type"]
            try:
                if tp == "mouse_move":
                    user32 = ctypes.windll.user32
                    sw = user32.GetSystemMetrics(78)
                    sh = user32.GetSystemMetrics(79)
                    ox = user32.GetSystemMetrics(76)
                    oy = user32.GetSystemMetrics(77)
                    ax = int((int(ev["x"]) - ox) * 65535 / sw)
                    ay = int((int(ev["y"]) - oy) * 65535 / sh)
                    inp = (INPUT * 1)(INPUT(
                        type=INPUT_MOUSE,
                        mi=MOUSEINPUT(
                            dx=ax, dy=ay,
                            dwFlags=(
                                MOUSEEVENTF_MOVE
                                | MOUSEEVENTF_ABSOLUTE
                                | MOUSEEVENTF_VIRTUALDESK
                            ),
                        ),
                    ))
                    user32.SendInput(1, inp, ctypes.sizeof(INPUT))

                elif tp == "mouse_click":
                    btn_str = str(ev["button"]).lower()
                    if "right" in btn_str:
                        btn = "right"
                    elif "middle" in btn_str:
                        btn = "middle"
                    else:
                        btn = "left"
                    if self._listener:
                        self._listener.mark_replayed_click()
                    send_mouse_input(
                        int(ev["x"]), int(ev["y"]), btn, bool(ev["pressed"]))

                elif tp == "mouse_scroll":
                    ms.position = (int(ev["x"]), int(ev["y"]))
                    ms.scroll(int(ev["dx"]), int(ev["dy"]))

                elif tp == "key_press":
                    k     = ev["key"]
                    canon = ser_key_to_canon(k)
                    if canon and self._listener:
                        self._listener.mark_replayed(canon)
                    obj = parse_key(k)
                    if obj is not None:
                        kb.press(obj)
                        self._pkeys.add(obj)

                elif tp == "key_release":
                    obj = parse_key(ev["key"])
                    if obj is not None:
                        kb.release(obj)
                        self._pkeys.discard(obj)

                elif tp == "wait":
                    dur = float(ev.get("duration", 1.0)) / self._speed
                    self._stop_evt.wait(timeout=dur)
                    wall_start = (
                        time.perf_counter()
                        - (ev["time"] - t_offset) / self._speed
                    )

                elif tp == "webhook":
                    ref = (
                        self._global_wall_start
                        if self._global_wall_start is not None
                        else wall_start
                    )
                    elapsed = time.perf_counter() - ref
                    threading.Thread(
                        target=send_webhook,
                        args=(
                            ev.get("url", ""),
                            ev.get("user_id", ""),
                            ev.get("message", ""),
                            elapsed,
                            self._wh_show_elapsed,
                            self._wh_show_cycles,
                            self._loop_count,
                        ),
                        daemon=True,
                    ).start()

            except Exception as exc:
                print(f"[PlayWorker] ERROR on {tp}: {exc}")

        _release_all(kb, self._pkeys, ms, self._pbtns)
        self.finished.emit()

    def stop(self) -> None:
        """Signal the worker to abort playback as soon as possible."""
        self._stop_evt.set()
        _release_all(self._kb, self._pkeys, self._ms, self._pbtns)
